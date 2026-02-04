"""文档管理API端点"""
from flask import Blueprint, request, jsonify
import os
import logging

logger = logging.getLogger(__name__)

# 创建蓝图
documents_bp = Blueprint('documents', __name__)


def get_policy_dir():
    """获取政策文档目录路径"""
    # 从 backend/api/ 向上两级到项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(project_root, 'policy_document')


def get_file_service():
    """获取文件服务（延迟导入避免循环依赖）"""
    from backend.services.file_service import FileService
    return FileService


@documents_bp.route("/api/documents", methods=["GET"])
def list_documents():
    """直接从 policy_document 目录获取文档列表（兼容旧接口）"""
    from backend.auth import is_admin
    keyword = request.args.get("keyword", "").strip()

    try:
        policy_dir = get_policy_dir()
        if not os.path.exists(policy_dir):
            return jsonify({"documents": [], "count": 0, "total": 0})

        documents = []
        total_count = 0

        def collect_folders(current_dir, parent_name=""):
            nonlocal total_count
            try:
                items = os.listdir(current_dir)
                folder_files = []
                sub_folders = []

                for item in items:
                    item_path = os.path.join(current_dir, item)
                    if os.path.isfile(item_path) and (item.endswith('.md') or item.endswith('.docx')):
                        if not keyword or keyword.lower() in item.lower():
                            folder_files.append(item)
                    elif os.path.isdir(item_path):
                        sub_folders.append(item)

                folder_name = "根目录" if current_dir == policy_dir else (
                    parent_name + "/" + os.path.basename(current_dir) if parent_name else os.path.basename(current_dir)
                )

                if folder_files:
                    documents.append({"name": folder_name, "files": sorted(folder_files)})
                    total_count += len(folder_files)

                for sub_folder in sub_folders:
                    collect_folders(os.path.join(current_dir, sub_folder), folder_name)

            except PermissionError:
                pass

        collect_folders(policy_dir)
        return jsonify({"documents": documents, "count": len(documents), "total": total_count, "keyword": keyword})

    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        return jsonify({"error": str(e)}), 500


@documents_bp.route("/api/documents/list", methods=["GET"])
def list_documents_in_dir():
    """列出指定目录下的文件和文件夹（资源管理器风格）"""
    keyword = request.args.get("keyword", "").strip()
    rel_path = request.args.get("path", "").strip()

    try:
        policy_dir = get_policy_dir()
        if not os.path.exists(policy_dir):
            return jsonify({"success": True, "files": [], "folders": [], "currentPath": "", "parentPath": ""})

        current_dir = os.path.join(policy_dir, rel_path) if rel_path else policy_dir
        if not os.path.exists(current_dir):
            return jsonify({"success": True, "files": [], "folders": [], "currentPath": "", "parentPath": ""})

        # 列出目录内容
        items = os.listdir(current_dir)

        parent_path = os.path.dirname(rel_path) if rel_path else None
        current_path = rel_path

        items = os.listdir(current_dir)
        folders = []
        files = []

        for item in items:
            item_path = os.path.join(current_dir, item)
            if os.path.isdir(item_path):
                folders.append(item)
            elif item.endswith('.md') or item.endswith('.docx'):
                if not keyword or keyword.lower() in item.lower():
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


@documents_bp.route("/api/download-documents", methods=["POST"])
def download_documents():
    """下载政策文档（支持文件和文件夹）"""
    from flask import send_file
    files = request.json.get("files", [])
    if not files:
        return jsonify({"success": False, "message": "未指定文件"}), 400

    policy_dir = get_policy_dir()
    result = get_file_service().download_files(policy_dir, files, "policy_documents")

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


@documents_bp.route("/api/delete-documents", methods=["POST"])
def delete_documents():
    """删除政策文档（仅管理员）"""
    from backend.auth import is_admin
    data = request.json
    files = data.get("files", [])
    username = data.get("username", "")

    if not is_admin(username):
        return jsonify({"success": False, "message": "只有管理员才能删除文档"}), 403

    if not files:
        return jsonify({"success": False, "message": "请选择要删除的文件"}), 400

    policy_dir = get_policy_dir()
    result = get_file_service().delete_files(policy_dir, files)
    return jsonify(result)


@documents_bp.route("/api/delete-folder", methods=["POST"])
def delete_folder():
    """删除文件夹（仅管理员）"""
    from backend.auth import is_admin
    data = request.json
    folder_path = data.get("folderPath", "")
    username = data.get("username", "")

    if not is_admin(username):
        return jsonify({"success": False, "message": "只有管理员才能删除文件夹"}), 403

    if not folder_path:
        return jsonify({"success": False, "message": "请提供文件夹路径"}), 400

    result = get_file_service().delete_folder(folder_path)
    return jsonify(result)


@documents_bp.route("/api/download-folder", methods=["POST"])
def download_folder():
    """打包下载文件夹"""
    from flask import send_file
    data = request.json
    folder_path = data.get("folderPath", "")

    if not folder_path:
        return jsonify({"success": False, "message": "请提供文件夹路径"}), 400

    result = get_file_service().download_folder_as_zip(folder_path)

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
