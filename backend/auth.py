"""用户认证模块"""
import json
import hashlib
from pathlib import Path
from typing import Optional, List, Dict

# 用户数据文件路径
USERS_FILE = Path(__file__).parent.parent / "data" / "users.json"


def load_users() -> List[Dict]:
    """加载用户数据"""
    if not USERS_FILE.exists():
        return []
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def save_users(users: List[Dict]) -> None:
    """保存用户数据"""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def hash_password(password: str) -> str:
    """密码哈希加密"""
    return hashlib.sha256(password.encode()).hexdigest()


def register(username: str, password: str, is_admin: bool = False) -> tuple:
    """
    用户注册
    返回: (success: bool, message: str)
    """
    if not username or not password:
        return False, "用户名和密码不能为空"

    if len(username) < 3:
        return False, "用户名至少需要3个字符"

    if len(password) < 6:
        return False, "密码至少需要6个字符"

    users = load_users()

    # 检查用户名是否已存在
    for user in users:
        if user.get("username") == username:
            return False, "用户名已存在"

    # 创建新用户
    new_user = {
        "username": username,
        "password": hash_password(password),
        "role": "admin" if is_admin else "user",
        "created_at": "",
        "sessions": [],  # 初始化会话列表
    }
    users.append(new_user)
    save_users(users)

    return True, "注册成功"


def login(username: str, password: str) -> tuple:
    """
    用户登录
    返回: (success: bool, message: str, user_data: dict or None)
    """
    if not username or not password:
        return False, "用户名和密码不能为空", None

    users = load_users()

    # 查找用户
    hashed_password = hash_password(password)
    for user in users:
        if user.get("username") == username and user.get("password") == hashed_password:
            return True, "登录成功", {
                "username": user["username"],
                "role": user.get("role", "user")
            }

    return False, "用户名或密码错误", None


def get_user_role(username: str) -> str:
    """获取用户角色"""
    users = load_users()
    for user in users:
        if user.get("username") == username:
            return user.get("role", "user")
    return "user"


def is_admin(username: str) -> bool:
    """检查是否是管理员"""
    return get_user_role(username) == "admin"


def user_exists(username: str) -> bool:
    """检查用户是否存在"""
    users = load_users()
    return any(u.get("username") == username for u in users)


def add_session(username: str, session_id: str) -> bool:
    """
    将会话ID关联到用户
    返回: (success: bool)
    """
    users = load_users()
    for user in users:
        if user.get("username") == username:
            if "sessions" not in user:
                user["sessions"] = []
            if session_id not in user["sessions"]:
                user["sessions"].append(session_id)
                save_users(users)
            return True
    return False


def get_user_sessions(username: str) -> List[str]:
    """获取用户的所有会话ID列表"""
    users = load_users()
    for user in users:
        if user.get("username") == username:
            return user.get("sessions", [])
    return []


def remove_session(username: str, session_id: str) -> bool:
    """从用户中移除会话ID"""
    users = load_users()
    for user in users:
        if user.get("username") == username:
            if "sessions" in user and session_id in user["sessions"]:
                user["sessions"].remove(session_id)
                save_users(users)
            return True
    return False
