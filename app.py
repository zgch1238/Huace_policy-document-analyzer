from flask import Flask, render_template, request, jsonify
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from opencode_client import OpenCodeClient
from analyzer import PolicyAnalyzer
from scheduler import AnalysisScheduler, APSCHEDULER_AVAILABLE

OPENCODE_SERVER_URL = os.getenv('OPENCODE_SERVER_URL', 'http://127.0.0.1:4096')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

app = Flask(__name__)
opencode_client = OpenCodeClient(OPENCODE_SERVER_URL)
analyzer = PolicyAnalyzer(opencode_client)
scheduler = AnalysisScheduler(analyzer)

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
    return render_template("index.html")


@app.route("/health")
def health():
    session_id = get_session_id()
    if session_id:
        return jsonify({"status": "ok", "opencode": "connected"})
    return jsonify({"status": "warning", "opencode": "disconnected"})


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
    project_root = os.path.dirname(os.path.abspath(__file__))
    policy_dir = os.path.join(project_root, 'policy_document')
    try:
        folders = analyzer.get_policy_documents(policy_dir)
        if folders:
            logger.info(f"找到 {len(folders)} 个政策文档")
            return jsonify({"documents": [{"name": "根目录", "files": folders}], "count": len(folders)})
        return jsonify({"documents": [], "count": 0, "message": "暂无政策文档"})
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
    try:
        all_content = []
        for file_path in files:
            full_path = os.path.join(policy_dir, file_path)
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    all_content.append(f"=== {file_path} ===\n\n{content}")
        combined_content = "\n\n".join(all_content)
        return jsonify({
            "success": True,
            "fileName": f"policy_documents_{time.strftime('%Y%m%d_%H%M%S')}.md",
            "content": combined_content
        })
    except Exception as e:
        logger.error(f"下载文档失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/analysis-results")
def list_analysis_results():
    project_root = os.path.dirname(os.path.abspath(__file__))
    analyze_dir = os.path.join(project_root, 'analyze_result')
    try:
        folders = analyzer.get_policy_documents(analyze_dir)
        if folders:
            return jsonify({"results": [{"name": "根目录", "files": folders}], "count": len(folders)})
        return jsonify({"results": [], "count": 0, "message": "暂无分析结果"})
    except Exception as e:
        logger.error(f"获取分析结果列表失败: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/download-analysis", methods=["POST"])
def download_analysis():
    files = request.json.get("files", [])
    if not files:
        return jsonify({"success": False, "message": "未指定文件"}), 400
    project_root = os.path.dirname(os.path.abspath(__file__))
    analyze_dir = os.path.join(project_root, 'analyze_result')
    try:
        all_content = []
        for file_path in files:
            full_path = os.path.join(analyze_dir, file_path)
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    all_content.append(f"=== {file_path} ===\n\n{content}")
        combined_content = "\n\n".join(all_content)
        return jsonify({
            "success": True,
            "fileName": f"analysis_results_{time.strftime('%Y%m%d_%H%M%S')}.md",
            "content": combined_content
        })
    except Exception as e:
        logger.error(f"下载分析结果失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/delete-documents", methods=["POST"])
def delete_documents():
    files = request.json.get("files", [])
    if not files:
        return jsonify({"success": False, "message": "请选择要删除的文件"}), 400
    project_root = os.path.dirname(os.path.abspath(__file__))
    policy_dir = os.path.join(project_root, 'policy_document')
    deleted_count = 0
    for file_path in files:
        full_path = os.path.join(policy_dir, file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            deleted_count += 1
    return jsonify({"success": True, "message": f"成功删除 {deleted_count} 个文件", "deletedCount": deleted_count})


@app.route("/api/delete-analysis", methods=["POST"])
def delete_analysis():
    files = request.json.get("files", [])
    if not files:
        return jsonify({"success": False, "message": "请选择要删除的文件"}), 400
    project_root = os.path.dirname(os.path.abspath(__file__))
    analyze_dir = os.path.join(project_root, 'analyze_result')
    deleted_count = 0
    for file_path in files:
        full_path = os.path.join(analyze_dir, file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            deleted_count += 1
    return jsonify({"success": True, "message": f"成功删除 {deleted_count} 个文件", "deletedCount": deleted_count})


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


@app.route("/api/trigger-analyze", methods=["POST"])
def trigger_analyze():
    """手动触发分析任务"""
    try:
        logger.info("手动触发政策文档分析...")
        project_root = os.path.dirname(os.path.abspath(__file__))
        policy_dir = os.path.join(project_root, 'policy_document')
        success_count, failed_count = analyzer.run_analysis(policy_dir)
        if success_count > 0 or failed_count > 0:
            return jsonify({
                "success": True,
                "message": "分析完成",
                "successCount": success_count,
                "failedCount": failed_count
            })
        else:
            return jsonify({"success": False, "message": "没有找到政策文档"})
    except Exception as e:
        logger.error(f"手动分析失败: {e}")
        return jsonify({"success": False, "message": str(e)})


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
