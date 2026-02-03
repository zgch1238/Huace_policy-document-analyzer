from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import time
import uuid
import requests
from dotenv import load_dotenv

load_dotenv()

# Vue 构建目录路径
VUE_DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'policy-doc-frontend', 'dist')

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from opencode_client import OpenCodeClient
from analyzer import PolicyAnalyzer
from scheduler import AnalysisScheduler, APSCHEDULER_AVAILABLE
from backend.auth import register, login, add_session, get_user_sessions, remove_session, is_admin
from backend.services.file_service import FileService
from backend.services.session_service import SessionService
from backend.database import (
    init_db, migrate_existing_files
)

OPENCODE_SERVER_URL = os.getenv('OPENCODE_SERVER_URL', 'http://127.0.0.1:4096')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

app = Flask(__name__)

# 跨域配置 - 允许所有来源（开发环境）
CORS(app, resources={
    r"/api/*": {"origins": "*"},
    r"/ask": {"origins": "*"}
})

# API 限流配置
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["2000 per day", "50 per hour"],
    storage_uri="memory://"
)

opencode_client = OpenCodeClient(OPENCODE_SERVER_URL)
analyzer = PolicyAnalyzer(opencode_client)
scheduler = AnalysisScheduler(analyzer)

# 初始化数据库
try:
    init_db()
    logger.info("数据库初始化成功")
except Exception as e:
    logger.error(f"数据库初始化失败: {e}")

SESSION_ID = None


def get_session_id():
    global SESSION_ID
    # 如果已有 session 且有效，直接返回
    if SESSION_ID:
        try:
            resp = requests.get(f"{OPENCODE_SERVER_URL}/session/{SESSION_ID}", timeout=30)
            if resp.status_code == 200:
                return SESSION_ID
        except Exception:
            pass
        SESSION_ID = None

    # 创建新 session
    for attempt in range(3):
        try:
            if attempt > 0:
                logger.info(f"第 {attempt + 1} 次重试连接 OpenCode 服务器...")
                time.sleep(1)
            logger.info(f"正在连接 OpenCode 服务器: {OPENCODE_SERVER_URL}")
            SESSION_ID = opencode_client.create_session()
            if SESSION_ID:
                logger.info(f"创建新会话: {SESSION_ID}")
                return SESSION_ID
        except Exception as e:
            logger.warning(f"第 {attempt + 1} 次连接尝试失败: {e}")
            if attempt == 2:
                logger.error("连接 OpenCode 服务器失败，已重试 3 次")
                return None
    return None


@app.route("/")
def index():
    # 检查 Vue 构建产物是否存在
    index_path = os.path.join(VUE_DIST_DIR, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(VUE_DIST_DIR, 'index.html')
    return jsonify({
        "message": "Vue 前端未构建",
        "hint": "请执行: cd policy-doc-frontend && npm run build"
    }), 503


@app.route("/<path:filename>")
def static_files(filename):
    """服务 Vue 构建的静态文件"""
    if os.path.exists(os.path.join(VUE_DIST_DIR, filename)):
        return send_from_directory(VUE_DIST_DIR, filename)
    return jsonify({"error": "File not found"}), 404


@app.route("/health")
def health():
    session_id = get_session_id()
    if session_id:
        return jsonify({"status": "ok", "opencode": "connected"})
    return jsonify({"status": "warning", "opencode": "disconnected"})


@limiter.limit("10 per minute")
@app.route("/ask", methods=["POST"])
def ask():
    user_message = request.json.get("message", "").strip()
    if not user_message:
        return jsonify({"response": "请输入有效的问题。"})
    logger.info(f"收到用户消息: {user_message[:100]}...")
    session_id = get_session_id()
    if not session_id:
        error_msg = "无法连接到 OpenCode 服务器。请确保 'opencode serve' 正在运行。"
        logger.error(error_msg)
        return jsonify({"response": error_msg})
    try:
        result = opencode_client.send_message(session_id, user_message)
        if result:
            logger.info(f"回复长度: {len(result)} 字符")
            return jsonify({"response": result})
        return jsonify({"response": "分析失败，请重试。"})
    except Exception as e:
        logger.error(f"请求异常: {e}")
        return jsonify({"response": f"连接 OpenCode 服务器失败: {str(e)}"})


@app.route("/api/documents")
def list_documents():
    """直接从 policy_document 目录获取文档列表，支持递归子目录"""
    keyword = request.args.get("keyword", "").strip()
    try:
        project_root = os.path.dirname(os.path.abspath(__file__))
        policy_dir = os.path.join(project_root, 'policy_document')

        if not os.path.exists(policy_dir):
            return jsonify({"documents": [], "count": 0, "total": 0})

        documents = []
        total_count = 0

        def collect_folders(current_dir, parent_name=""):
            """递归收集所有文件夹及其直接包含的文件"""
            nonlocal total_count

            try:
                items = os.listdir(current_dir)
                folder_files = []
                sub_folders = []

                for item in items:
                    item_path = os.path.join(current_dir, item)
                    if os.path.isfile(item_path) and item.endswith('.md'):
                        if keyword:
                            if keyword.lower() in item.lower():
                                folder_files.append(item)
                        else:
                            folder_files.append(item)
                    elif os.path.isfile(item_path) and item.endswith('.docx'):
                        if keyword:
                            if keyword.lower() in item.lower():
                                folder_files.append(item)
                        else:
                            folder_files.append(item)
                    elif os.path.isdir(item_path):
                        sub_folders.append(item)

                # 计算文件夹名称
                if current_dir == policy_dir:
                    folder_name = "根目录"
                elif parent_name:
                    folder_name = parent_name + "/" + os.path.basename(current_dir)
                else:
                    folder_name = os.path.basename(current_dir)

                # 添加当前文件夹
                documents.append({
                    "name": folder_name,
                    "files": sorted(folder_files) if folder_files else []
                })
                total_count += len(folder_files)

                # 递归处理所有子文件夹
                for sub_folder in sub_folders:
                    sub_dir = os.path.join(current_dir, sub_folder)
                    collect_folders(sub_dir, folder_name)

            except PermissionError:
                pass

        # 开始收集
        collect_folders(policy_dir)

        return jsonify({
            "documents": documents,
            "count": len(documents),
            "total": total_count,
            "keyword": keyword
        })
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/download-documents", methods=["POST"])
def download_documents():
    files = request.json.get("files", [])
    if not files:
        return jsonify({"success": False, "message": "未指定文件"}), 400
    project_root = os.path.dirname(os.path.abspath(__file__))
    policy_dir = os.path.join(project_root, 'policy_document')
    result = FileService.download_files(policy_dir, files, "policy_documents")
    return jsonify(result)


@app.route("/api/documents/list")
def list_documents_in_dir():
    """列出指定目录下的文件和文件夹（资源管理器风格）"""
    keyword = request.args.get("keyword", "").strip()
    rel_path = request.args.get("path", "").strip()  # 相对于 policy_document 的路径

    try:
        project_root = os.path.dirname(os.path.abspath(__file__))
        policy_dir = os.path.join(project_root, 'policy_document')

        if not os.path.exists(policy_dir):
            return jsonify({"success": True, "files": [], "folders": [], "currentPath": "", "parentPath": ""})

        # 计算实际目录路径
        if rel_path:
            current_dir = os.path.join(policy_dir, rel_path)
        else:
            current_dir = policy_dir

        if not os.path.exists(current_dir):
            return jsonify({"success": True, "files": [], "folders": [], "currentPath": "", "parentPath": ""})

        # 计算父路径
        if rel_path:
            parent_path = os.path.dirname(rel_path)
            if parent_path == ".":
                parent_path = ""
        else:
            parent_path = None  # 已经是根目录

        current_path = rel_path

        # 获取文件和文件夹
        items = os.listdir(current_dir)
        folders = []
        files = []

        for item in items:
            item_path = os.path.join(current_dir, item)
            if os.path.isdir(item_path):
                folders.append(item)
            elif item.endswith('.md') or item.endswith('.docx'):
                # 如果有搜索关键词，进行过滤
                if keyword:
                    if keyword.lower() in item.lower():
                        files.append(item)
                else:
                    files.append(item)

        folders.sort()
        files.sort()

        return jsonify({
            "success": True,
            "files": files,
            "folders": folders,
            "currentPath": current_path,
            "parentPath": parent_path if parent_path is not None else "",
            "keyword": keyword
        })
    except Exception as e:
        logger.error(f"获取目录内容失败: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/analysis/list")
def list_analysis_dir():
    """列出分析结果目录的内容（资源管理器风格）"""
    base_dir = request.args.get("baseDir", "").strip()  # analyze_result 或 policy_document_word
    rel_path = request.args.get("path", "").strip()     # 相对于 base_dir 的路径
    keyword = request.args.get("keyword", "").strip()
    min_score = request.args.get("minScore")

    try:
        project_root = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.join(project_root, base_dir)

        if not os.path.exists(base_path):
            return jsonify({"success": True, "files": [], "folders": [], "currentPath": "", "parentPath": ""})

        # 计算实际目录路径
        if rel_path:
            current_dir = os.path.join(base_path, rel_path)
        else:
            current_dir = base_path

        if not os.path.exists(current_dir):
            return jsonify({"success": True, "files": [], "folders": [], "currentPath": "", "parentPath": ""})

        # 计算父路径
        if rel_path:
            parent_path = os.path.dirname(rel_path)
            if parent_path == ".":
                parent_path = ""
        else:
            parent_path = ""

        current_path = rel_path

        # 获取文件和文件夹
        items = os.listdir(current_dir)
        folders = []
        files = []

        for item in items:
            item_path = os.path.join(current_dir, item)
            if os.path.isdir(item_path):
                folders.append(item)
            elif item.endswith('.docx'):
                # 搜索关键词筛选
                if keyword and keyword.lower() not in item.lower():
                    continue
                # 分数筛选
                if min_score:
                    score_val = float(min_score)
                    match = item.match(r'_(\d+\.?\d*)\.docx$')
                    if match:
                        file_score = float(match[1])
                        if file_score < score_val:
                            continue
                files.append(item)

        folders.sort()
        files.sort()

        return jsonify({
            "success": True,
            "files": files,
            "folders": folders,
            "currentPath": current_path,
            "parentPath": parent_path,
            "keyword": keyword
        })
    except Exception as e:
        logger.error(f"获取分析目录内容失败: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/analysis-results")
def list_analysis_results():
    """直接从 analyze_result 目录获取分析结果列表"""
    try:
        project_root = os.path.dirname(os.path.abspath(__file__))
        analyze_dir = os.path.join(project_root, 'analyze_result')

        if not os.path.exists(analyze_dir):
            return jsonify({"results": [], "count": 0, "total": 0})

        # 获取目录下的所有 .md 和 .docx 文件
        files = sorted([f for f in os.listdir(analyze_dir) if f.endswith('.md') or f.endswith('.docx')])

        # 只显示分析结果文件（包含 "_分析结果_"）
        analysis_files = [f for f in files if '_分析结果_' in f]

        results = [{"name": "根目录", "files": analysis_files}]
        return jsonify({
            "results": results,
            "count": len(analysis_files),
            "total": len(analysis_files)
        })
    except Exception as e:
        logger.error(f"获取分析结果列表失败: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/highlight-docs")
def list_highlight_docs():
    """获取 policy_document_word 目录中的高亮文档列表"""
    try:
        project_root = os.path.dirname(os.path.abspath(__file__))
        highlight_dir = os.path.join(project_root, 'policy_document_word')

        if not os.path.exists(highlight_dir):
            return jsonify({"results": [], "count": 0, "total": 0})

        # 获取目录下的所有 .docx 文件
        files = sorted([f for f in os.listdir(highlight_dir) if f.endswith('.docx')])

        results = [{"name": "根目录", "files": files}]
        return jsonify({
            "results": results,
            "count": len(files),
            "total": len(files)
        })
    except Exception as e:
        logger.error(f"获取高亮文档列表失败: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/analysis-results/<analysis_id>")
def get_analysis_detail(analysis_id):
    """获取分析结果详情"""
    try:
        result = get_analysis_result(analysis_id)
        if result:
            return jsonify({"success": True, "result": result})
        return jsonify({"success": False, "message": "分析结果不存在"}), 404
    except Exception as e:
        logger.error(f"获取分析详情失败: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/download-analysis", methods=["POST"])
def download_analysis():
    data = request.json
    files = data.get("files", [])
    directory = data.get("directory", "analysis_results")

    if not files:
        return jsonify({"success": False, "message": "未指定文件"}), 400

    project_root = os.path.dirname(os.path.abspath(__file__))

    # 根据目录参数选择源目录
    if directory == "policy_document_word":
        source_dir = os.path.join(project_root, 'policy_document_word')
        download_name = "highlight_docs"
    else:
        source_dir = os.path.join(project_root, 'analyze_result')
        download_name = "analysis_results"

    result = FileService.download_files(source_dir, files, download_name)
    return jsonify(result)


@app.route("/api/delete-documents", methods=["POST"])
def delete_documents():
    data = request.json
    files = data.get("files", [])
    username = data.get("username", "")

    # 检查是否是管理员
    if not is_admin(username):
        return jsonify({"success": False, "message": "只有管理员才能删除文档"}), 403

    if not files:
        return jsonify({"success": False, "message": "请选择要删除的文件"}), 400
    project_root = os.path.dirname(os.path.abspath(__file__))
    policy_dir = os.path.join(project_root, 'policy_document')
    result = FileService.delete_files(policy_dir, files)
    return jsonify(result)


@app.route("/api/delete-analysis", methods=["POST"])
def delete_analysis():
    data = request.json
    files = data.get("files", [])
    username = data.get("username", "")

    # 检查是否是管理员
    if not is_admin(username):
        return jsonify({"success": False, "message": "只有管理员才能删除分析结果"}), 403

    if not files:
        return jsonify({"success": False, "message": "请选择要删除的文件"}), 400
    project_root = os.path.dirname(os.path.abspath(__file__))
    analyze_dir = os.path.join(project_root, 'analyze_result')
    result = FileService.delete_files(analyze_dir, files)
    return jsonify(result)


@app.route("/api/save-analysis", methods=["POST"])
def save_analysis():
    doc_name = request.json.get('docName', '')
    result = request.json.get('result', '')
    if not doc_name or not result:
        return jsonify({"success": False, "message": "参数不完整"}), 400
    project_root = os.path.dirname(os.path.abspath(__file__))
    analyze_dir = os.path.join(project_root, 'analyze_result')
    if not os.path.exists(analyze_dir):
        os.makedirs(analyze_dir)
    output_filename = f"{os.path.splitext(doc_name)[0]}_分析结果.md"
    output_path = os.path.join(analyze_dir, output_filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)
    logger.info(f"保存分析结果: {output_path}")
    return jsonify({"success": True, "path": output_path})


@app.route("/api/analyze-status")
def analyze_status():
    status = analyzer.get_status()
    if status:
        status_text = status.get('status', 'unknown')
        if status_text == 'success':
            text = '已自动分析成功'
        elif status_text == 'session_failed':
            text = '已自动分析失败'
        else:
            text = '等待自动分析'
        return jsonify({"success": True, "status": status_text, "text": text})
    return jsonify({"success": True, "status": "pending", "text": "等待自动分析"})


@app.route("/api/analyze-progress")
@limiter.exempt  # 进度查询不限制
def analyze_progress():
    """获取分析进度"""
    try:
        progress = analyzer.get_progress()
        return jsonify({
            "success": True,
            "running": progress.get('running', False),
            "total": progress.get('total', 0),
            "current": progress.get('current', 0),
            "success_count": progress.get('success', 0),
            "failed_count": progress.get('failed', 0),
            "current_file": progress.get('current_file', ''),
            "progress_percent": progress.get('progress_percent', 0)
        })
    except Exception as e:
        logger.error(f"获取分析进度失败: {e}")
        return jsonify({"success": False, "error": str(e)})


# ============ 用户认证接口 ============

@app.route("/api/auth/register", methods=["POST"])
def api_register():
    """用户注册"""
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")

    success, message = register(username, password)
    if success:
        logger.info(f"新用户注册成功: {username}")
        return jsonify({"success": True, "message": message, "username": username})
    return jsonify({"success": False, "message": message}), 400


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    """用户登录"""
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")

    success, message, user_data = login(username, password)
    if success:
        logger.info(f"用户登录成功: {username}")
        return jsonify({
            "success": True,
            "message": message,
            "user": user_data
        })
    return jsonify({"success": False, "message": message}), 401


# ============ 会话管理接口 ============


@app.route("/api/sessions", methods=["GET"])
def list_sessions():
    """获取用户会话列表"""
    username = request.args.get("username")
    if not username:
        return jsonify({"error": "缺少用户名参数"}), 400

    # 获取用户有权访问的会话ID列表
    user_session_ids = get_user_sessions(username)

    # 使用 SessionService 获取会话摘要列表
    sessions = SessionService.list_sessions_by_user(user_session_ids)

    return jsonify({"sessions": sessions})


@app.route("/api/session", methods=["POST"])
def create_session():
    """创建新会话"""
    data = request.json or {}
    username = data.get("username")
    title = data.get("title", "新对话")

    if not username:
        return jsonify({"error": "缺少用户名参数"}), 400

    # 生成会话ID
    session_id = str(uuid.uuid4())

    # 使用 SessionService 创建会话数据
    session_data = SessionService.create_session_data(session_id, title, username)

    # 保存会话
    if SessionService.save_session(session_id, session_data):
        # 将会话ID关联到用户
        add_session(username, session_id)
        logger.info(f"创建会话: {session_id} (用户: {username})")
        return jsonify({"success": True, "id": session_id, "title": title})

    return jsonify({"error": "创建会话失败"}), 500


@app.route("/api/session/<session_id>", methods=["GET"])
def get_session(session_id: str):
    """获取会话详情"""
    username = request.args.get("username")

    # 检查权限
    if username:
        user_session_ids = get_user_sessions(username)
        if session_id not in user_session_ids:
            return jsonify({"error": "无权访问此会话"}), 403

    session_data = SessionService.load_session(session_id)
    if session_data:
        return jsonify({"success": True, "session": session_data})

    return jsonify({"error": "会话不存在"}), 404


@app.route("/api/session/<session_id>", methods=["DELETE"])
def delete_session(session_id: str):
    """删除会话"""
    data = request.json or {}
    username = data.get("username")

    if not username:
        return jsonify({"error": "缺少用户名参数"}), 400

    # 检查权限
    user_session_ids = get_user_sessions(username)
    if session_id not in user_session_ids:
        return jsonify({"error": "无权删除此会话"}), 403

    # 使用 SessionService 删除会话文件
    SessionService.delete_session(session_id)

    # 从用户中移除会话ID
    remove_session(username, session_id)

    logger.info(f"删除会话: {session_id} (用户: {username})")
    return jsonify({"success": True})


@app.route("/api/session/<session_id>/message", methods=["POST"])
def add_message(session_id: str):
    """添加消息到会话"""
    data = request.json or {}
    username = data.get("username")
    role = data.get("role")  # "user" or "assistant"
    content = data.get("content", "")

    if not username or not role or not content:
        return jsonify({"error": "参数不完整"}), 400

    # 检查权限
    user_session_ids = get_user_sessions(username)
    if session_id not in user_session_ids:
        return jsonify({"error": "无权访问此会话"}), 403

    # 加载会话
    session_data = SessionService.load_session(session_id)
    if not session_data:
        return jsonify({"error": "会话不存在"}), 404

    # 使用 SessionService 添加消息
    SessionService.add_message(session_data, role, content)

    # 保存会话
    SessionService.save_session(session_id, session_data)

    return jsonify({"success": True})


# ============ 分析任务接口 ============

@limiter.limit("5 per hour")
@app.route("/api/trigger-analyze", methods=["POST"])
def trigger_analyze():
    """手动触发分析任务（并行分析）"""
    try:
        logger.info("手动触发政策文档分析（并行模式）...")
        project_root = os.path.dirname(os.path.abspath(__file__))
        policy_dir = os.path.join(project_root, 'policy_document')
        # 使用并行分析（5个session并发）
        success_count, failed_count = analyzer.run_parallel_analysis(policy_dir, max_workers=5)
        if success_count > 0 or failed_count > 0:
            return jsonify({
                "success": True,
                "message": f"分析完成！成功: {success_count}, 失败: {failed_count}",
                "successCount": success_count,
                "failedCount": failed_count
            })
        else:
            # 检查是否有文档
            from analyzer import PolicyAnalyzer
            temp_analyzer = PolicyAnalyzer(None)
            doc_files = temp_analyzer.get_policy_documents(policy_dir)
            if not doc_files:
                return jsonify({"success": False, "message": "没有找到政策文档"})
            else:
                return jsonify({"success": True, "message": "所有政策文档已分析完成，无需新分析"})
    except Exception as e:
        logger.error(f"手动分析失败: {e}")
        return jsonify({"success": False, "message": str(e)})


@app.route("/api/sync-data", methods=["POST"])
def sync_data():
    """同步数据：重新扫描目录并更新数据库"""
    try:
        from backend.database import init_db, migrate_existing_files, get_statistics

        # 重新初始化数据库并迁移数据
        init_db()
        migrate_existing_files()
        stats = get_statistics()

        logger.info(f"数据同步完成: 文档{stats['document_count']}个, 分析结果{stats['analysis_count']}个")

        return jsonify({
            "success": True,
            "message": "同步完成",
            "statistics": stats
        })
    except Exception as e:
        logger.error(f"数据同步失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


if __name__ == "__main__":
    # 启动调度器（不执行启动时分析）
    sched = scheduler.start(interval_days=30)
    logger.info(f"启动 Flask 应用，端口: {FLASK_PORT}")
    logger.info(f"OpenCode 服务器地址: {OPENCODE_SERVER_URL}")
    try:
        app.run(debug=FLASK_DEBUG, host='0.0.0.0', port=FLASK_PORT)
    finally:
        if APSCHEDULER_AVAILABLE and sched:
            scheduler.shutdown()
