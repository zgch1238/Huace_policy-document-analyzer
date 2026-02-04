"""认证和会话管理API端点"""
from flask import Blueprint, request, jsonify
import uuid
import logging

logger = logging.getLogger(__name__)

# 创建蓝图
auth_bp = Blueprint('auth', __name__)


@auth_bp.route("/api/auth/register", methods=["POST"])
def api_register():
    """用户注册"""
    from backend.auth import register

    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")

    success, message = register(username, password)
    if success:
        logger.info(f"新用户注册成功: {username}")
        return jsonify({"success": True, "message": message, "username": username})
    return jsonify({"success": False, "message": message}), 400


@auth_bp.route("/api/auth/login", methods=["POST"])
def api_login():
    """用户登录"""
    from backend.auth import login

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


@auth_bp.route("/api/sessions", methods=["GET"])
def list_sessions():
    """获取用户会话列表"""
    from backend.auth import get_user_sessions
    from backend.services.session_service import SessionService

    username = request.args.get("username")
    if not username:
        return jsonify({"error": "缺少用户名参数"}), 400

    user_session_ids = get_user_sessions(username)
    sessions = SessionService.list_sessions_by_user(user_session_ids)
    return jsonify({"sessions": sessions})


@auth_bp.route("/api/session", methods=["POST"])
def create_session():
    """创建新会话"""
    from backend.auth import add_session
    from backend.services.session_service import SessionService

    data = request.json or {}
    username = data.get("username")
    title = data.get("title", "新对话")

    if not username:
        return jsonify({"error": "缺少用户名参数"}), 400

    session_id = str(uuid.uuid4())
    session_data = SessionService.create_session_data(session_id, title, username)

    if SessionService.save_session(session_id, session_data):
        add_session(username, session_id)
        logger.info(f"创建会话: {session_id} (用户: {username})")
        return jsonify({"success": True, "id": session_id, "title": title})

    return jsonify({"error": "创建会话失败"}), 500


@auth_bp.route("/api/session/<session_id>", methods=["GET"])
def get_session(session_id: str):
    """获取会话详情"""
    from backend.auth import get_user_sessions
    from backend.services.session_service import SessionService

    username = request.args.get("username")

    if username:
        user_session_ids = get_user_sessions(username)
        if session_id not in user_session_ids:
            return jsonify({"error": "无权访问此会话"}), 403

    session_data = SessionService.load_session(session_id)
    if session_data:
        return jsonify({"success": True, "session": session_data})

    return jsonify({"error": "会话不存在"}), 404


@auth_bp.route("/api/session/<session_id>", methods=["DELETE"])
def delete_session(session_id: str):
    """删除会话"""
    from backend.auth import get_user_sessions, remove_session
    from backend.services.session_service import SessionService

    data = request.json or {}
    username = data.get("username")

    if not username:
        return jsonify({"error": "缺少用户名参数"}), 400

    user_session_ids = get_user_sessions(username)
    if session_id not in user_session_ids:
        return jsonify({"error": "无权删除此会话"}), 403

    SessionService.delete_session(session_id)
    remove_session(username, session_id)

    logger.info(f"删除会话: {session_id} (用户: {username})")
    return jsonify({"success": True})


@auth_bp.route("/api/session/<session_id>/message", methods=["POST"])
def add_message(session_id: str):
    """添加消息到会话"""
    from backend.auth import get_user_sessions
    from backend.services.session_service import SessionService

    data = request.json or {}
    username = data.get("username")
    role = data.get("role")
    content = data.get("content", "")

    if not username or not role or not content:
        return jsonify({"error": "参数不完整"}), 400

    user_session_ids = get_user_sessions(username)
    if session_id not in user_session_ids:
        return jsonify({"error": "无权访问此会话"}), 403

    session_data = SessionService.load_session(session_id)
    if not session_data:
        return jsonify({"error": "会话不存在"}), 404

    SessionService.add_message(session_data, role, content)
    SessionService.save_session(session_id, session_data)

    return jsonify({"success": True})
