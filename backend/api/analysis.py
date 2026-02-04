"""分析结果API端点"""
from flask import Blueprint, request, jsonify
import os
import re
import logging

logger = logging.getLogger(__name__)

OPENCODE_SERVER_URL = os.getenv('OPENCODE_SERVER_URL', 'http://127.0.0.1:4096')

# 创建蓝图
analysis_bp = Blueprint('analysis', __name__)


def get_analysis_dir():
    """获取分析结果目录路径"""
    # 从 backend/api/ 向上两级到项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(project_root, 'analyze_result')


def get_highlight_dir():
    """获取高亮文档目录路径"""
    # 从 backend/api/ 向上两级到项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(project_root, 'policy_document_word')


def get_file_service():
    """获取文件服务（延迟导入避免循环依赖）"""
    from backend.services.file_service import FileService
    return FileService


@analysis_bp.route("/api/analysis/list", methods=["GET"])
def list_analysis_dir():
    """列出分析结果目录的内容（资源管理器风格）"""
    base_dir = request.args.get("baseDir", "").strip()  # analyze_result 或 policy_document_word
    rel_path = request.args.get("path", "").strip()
    keyword = request.args.get("keyword", "").strip()
    min_score = request.args.get("minScore")

    try:
        # 从 backend/api/ 向上两级到项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        base_path = os.path.join(project_root, base_dir)

        if not os.path.exists(base_path):
            return jsonify({"success": True, "files": [], "folders": [], "currentPath": "", "parentPath": ""})

        current_dir = os.path.join(base_path, rel_path) if rel_path else base_path

        if not os.path.exists(current_dir):
            return jsonify({"success": True, "files": [], "folders": [], "currentPath": "", "parentPath": ""})

        parent_path = os.path.dirname(rel_path) if rel_path else ""
        current_path = rel_path

        items = os.listdir(current_dir)
        folders = []
        files = []

        for item in items:
            item_path = os.path.join(current_dir, item)
            if os.path.isdir(item_path):
                folders.append(item)
            elif base_dir == 'analyze_result':
                # 分析结果目录：只显示 .md 文件
                if item.endswith('.md'):
                    # 搜索关键词筛选
                    if keyword and keyword.lower() not in item.lower():
                        continue
                    # 分数筛选 - 从文件名末尾提取分数（如 xxx_58.0.md）
                    if min_score:
                        score_val = float(min_score)
                        # 从右向左匹配最后一个下划线后的数字
                        match = re.match(r'.*[_-](\d+\.?\d*)\.md$', item)
                        if match:
                            file_score = float(match[1])
                            if file_score < score_val:
                                continue
                    files.append(item)
            elif base_dir == 'policy_document_word':
                # 高亮文档目录：只显示 .docx 文件
                if item.endswith('.docx'):
                    # 搜索关键词筛选
                    if keyword and keyword.lower() not in item.lower():
                        continue
                    # 分数筛选 - 从文件名末尾提取分数（如 xxx_58.0.docx）
                    if min_score:
                        score_val = float(min_score)
                        # 从右向左匹配最后一个下划线后的数字
                        match = re.match(r'.*[_-](\d+\.?\d*)\.docx$', item)
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


@analysis_bp.route("/api/analysis-results", methods=["GET"])
def list_analysis_results():
    """获取分析结果列表（兼容旧接口）"""
    try:
        analyze_dir = get_analysis_dir()
        if not os.path.exists(analyze_dir):
            return jsonify({"results": [], "count": 0, "total": 0})

        files = sorted([f for f in os.listdir(analyze_dir) if f.endswith('.docx')])
        analysis_files = [f for f in files if '_分析结果_' in f]

        return jsonify({
            "results": [{"name": "根目录", "files": analysis_files}],
            "count": len(analysis_files),
            "total": len(analysis_files)
        })

    except Exception as e:
        logger.error(f"获取分析结果列表失败: {e}")
        return jsonify({"error": str(e)}), 500


@analysis_bp.route("/api/highlight-docs", methods=["GET"])
def list_highlight_docs():
    """获取高亮文档列表（兼容旧接口）"""
    try:
        highlight_dir = get_highlight_dir()
        if not os.path.exists(highlight_dir):
            return jsonify({"results": [], "count": 0, "total": 0})

        files = sorted([f for f in os.listdir(highlight_dir) if f.endswith('.docx')])
        return jsonify({
            "results": [{"name": "根目录", "files": files}],
            "count": len(files),
            "total": len(files)
        })

    except Exception as e:
        logger.error(f"获取高亮文档列表失败: {e}")
        return jsonify({"error": str(e)}), 500


@analysis_bp.route("/api/download-analysis", methods=["POST"])
def download_analysis():
    """下载分析结果或高亮文档（支持文件和文件夹）"""
    from flask import send_file
    data = request.json
    files = data.get("files", [])
    directory = data.get("directory", "analysis_results")

    if not files:
        return jsonify({"success": False, "message": "未指定文件"}), 400

    if directory == "policy_document_word":
        source_dir = get_highlight_dir()
        download_name = "highlight_docs"
    else:
        source_dir = get_analysis_dir()
        download_name = "analysis_results"

    result = get_file_service().download_files(source_dir, files, download_name)

    # 如果是文件夹下载，返回ZIP文件
    if result.get("isFolder") and result.get("zipPath"):
        try:
            return send_file(
                result["zipPath"],
                as_attachment=True,
                download_name=result["fileName"],
                mimetype='application/zip'
            )
        except Exception as e:
            logger.error(f"发送ZIP文件失败: {e}")
            return jsonify({"success": False, "message": "下载失败"}), 500

    return jsonify(result)


@analysis_bp.route("/api/delete-analysis", methods=["POST"])
def delete_analysis():
    """删除分析结果（仅管理员）"""
    from backend.auth import is_admin
    data = request.json
    files = data.get("files", [])
    username = data.get("username", "")

    if not is_admin(username):
        return jsonify({"success": False, "message": "只有管理员才能删除分析结果"}), 403

    if not files:
        return jsonify({"success": False, "message": "请选择要删除的文件"}), 400

    analyze_dir = get_analysis_dir()
    result = get_file_service().delete_files(analyze_dir, files)
    return jsonify(result)


@analysis_bp.route("/api/analysis/delete-folder", methods=["POST"])
def delete_analysis_folder():
    """删除分析结果文件夹（仅管理员）"""
    from backend.auth import is_admin
    from backend.services.file_service import FileService
    data = request.json
    folder_path = data.get("folderPath", "")
    base_dir = data.get("baseDir", "analyze_result")
    username = data.get("username", "")

    if not is_admin(username):
        return jsonify({"success": False, "message": "只有管理员才能删除文件夹"}), 403

    if not folder_path:
        return jsonify({"success": False, "message": "请提供文件夹路径"}), 400

    result = FileService.delete_folder(folder_path)
    return jsonify(result)


@analysis_bp.route("/api/analysis/download-folder", methods=["POST"])
def download_analysis_folder():
    """打包下载分析结果文件夹"""
    from flask import send_file
    from backend.services.file_service import FileService
    data = request.json
    folder_path = data.get("folderPath", "")

    if not folder_path:
        return jsonify({"success": False, "message": "请提供文件夹路径"}), 400

    result = FileService.download_folder_as_zip(folder_path)

    if not result.get("success"):
        return jsonify(result), 400

    try:
        return send_file(
            result["zipPath"],
            as_attachment=True,
            download_name=result["zipName"],
            mimetype='application/zip'
        )
    except Exception as e:
        logger.error(f"发送ZIP文件失败: {e}")
        return jsonify({"success": False, "message": "下载失败"}), 500


@analysis_bp.route("/api/save-analysis", methods=["POST"])
def save_analysis():
    """保存分析结果"""
    doc_name = request.json.get('docName', '')
    result = request.json.get('result', '')

    if not doc_name or not result:
        return jsonify({"success": False, "message": "参数不完整"}), 400

    analyze_dir = get_analysis_dir()
    if not os.path.exists(analyze_dir):
        os.makedirs(analyze_dir)

    output_filename = f"{os.path.splitext(doc_name)[0]}_分析结果.md"
    output_path = os.path.join(analyze_dir, output_filename)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)

    logger.info(f"保存分析结果: {output_path}")
    return jsonify({"success": True, "path": output_path})


@analysis_bp.route("/api/analyze-status", methods=["GET"])
def analyze_status():
    """获取分析状态"""
    try:
        from core.analyzer import PolicyAnalyzer
        from core.opencode_client import OpenCodeClient

        opencode_client = OpenCodeClient(OPENCODE_SERVER_URL)
        analyzer = PolicyAnalyzer(opencode_client)
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
    except Exception as e:
        logger.error(f"获取分析状态失败: {e}")
        return jsonify({"success": True, "status": "pending", "text": "等待自动分析"})


@analysis_bp.route("/api/analyze-progress", methods=["GET"])
def analyze_progress():
    """获取分析进度"""
    from core.analyzer import PolicyAnalyzer
    from core.opencode_client import OpenCodeClient

    try:
        opencode_client = OpenCodeClient(OPENCODE_SERVER_URL)
        analyzer = PolicyAnalyzer(opencode_client)
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


@analysis_bp.route("/api/trigger-analyze", methods=["POST"])
def trigger_analyze():
    """手动触发分析任务"""
    from core.analyzer import PolicyAnalyzer
    from core.opencode_client import OpenCodeClient

    try:
        logger.info("手动触发政策文档分析（并行模式）...")
        # 从 backend/api/ 向上两级到项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        policy_dir = os.path.join(project_root, 'policy_document')

        opencode_client = OpenCodeClient(OPENCODE_SERVER_URL)
        analyzer = PolicyAnalyzer(opencode_client)

        # 使用并行分析
        success_count, failed_count = analyzer.run_parallel_analysis(policy_dir, max_workers=5)

        if success_count > 0 or failed_count > 0:
            return jsonify({
                "success": True,
                "message": f"分析完成！成功: {success_count}, 失败: {failed_count}",
                "successCount": success_count,
                "failedCount": failed_count
            })
        else:
            doc_files = analyzer.get_policy_documents(policy_dir)
            if not doc_files:
                return jsonify({"success": False, "message": "没有找到政策文档"})
            else:
                return jsonify({"success": True, "message": "所有政策文档已分析完成，无需新分析"})

    except Exception as e:
        logger.error(f"手动分析失败: {e}")
        return jsonify({"success": False, "message": str(e)})
