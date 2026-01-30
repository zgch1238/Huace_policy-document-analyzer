"""会话服务模块 - 提供会话管理逻辑"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# 会话存储目录
SESSIONS_DIR = Path(__file__).parent.parent.parent / "sessions"


class SessionService:
    """会话服务类 - 管理对话会话的存储和加载"""

    @staticmethod
    def get_session_path(session_id: str) -> Path:
        """获取会话文件路径"""
        SESSIONS_DIR.mkdir(exist_ok=True)
        return SESSIONS_DIR / f"{session_id}.json"

    @staticmethod
    def load_session(session_id: str) -> Dict[str, Any]:
        """加载会话数据"""
        path = SessionService.get_session_path(session_id)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"加载会话失败: {session_id}, 错误: {e}")
        return {}

    @staticmethod
    def save_session(session_id: str, data: Dict[str, Any]) -> bool:
        """保存会话数据"""
        path = SessionService.get_session_path(session_id)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            logger.error(f"保存会话失败: {session_id}, 错误: {e}")
            return False

    @staticmethod
    def delete_session(session_id: str) -> bool:
        """删除会话文件"""
        path = SessionService.get_session_path(session_id)
        if path.exists():
            try:
                path.unlink()
                logger.info(f"删除会话文件: {session_id}")
                return True
            except Exception as e:
                logger.error(f"删除会话失败: {session_id}, 错误: {e}")
        return False

    @staticmethod
    def create_session_data(session_id: str, title: str = "新对话", username: str = None) -> Dict[str, Any]:
        """
        创建新的会话数据

        Args:
            session_id: 会话ID
            title: 会话标题
            username: 用户名（可选）

        Returns:
            会话数据字典
        """
        now = datetime.now().isoformat()
        return {
            "id": session_id,
            "title": title,
            "preview": "",
            "messages": [],
            "username": username,
            "created_at": now,
            "updated_at": now
        }

    @staticmethod
    def add_message(session_data: Dict[str, Any], role: str, content: str) -> None:
        """
        添加消息到会话

        Args:
            session_data: 会话数据
            role: 消息角色 ("user" 或 "assistant")
            content: 消息内容
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        session_data["messages"].append(message)

        # 更新预览（第一条用户消息）
        if role == "user" and not session_data.get("preview"):
            session_data["preview"] = content[:50] + ("..." if len(content) > 50 else "")

        # 更新时间
        session_data["updated_at"] = datetime.now().isoformat()

    @staticmethod
    def get_session_summary(session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取会话摘要信息

        Args:
            session_data: 会话数据

        Returns:
            包含 id、title、preview、message_count、created_at、updated_at 的字典
        """
        return {
            "id": session_data.get("id", ""),
            "title": session_data.get("title", "无标题会话"),
            "preview": session_data.get("preview", ""),
            "message_count": len(session_data.get("messages", [])),
            "created_at": session_data.get("created_at", ""),
            "updated_at": session_data.get("updated_at", "")
        }

    @staticmethod
    def list_sessions_by_user(user_session_ids: List[str]) -> List[Dict[str, Any]]:
        """
        列出用户的所有会话

        Args:
            user_session_ids: 用户拥有的会话ID列表

        Returns:
            会话摘要列表（按更新时间倒序排列）
        """
        sessions = []
        for session_id in user_session_ids:
            session_data = SessionService.load_session(session_id)
            if session_data:
                sessions.append(SessionService.get_session_summary(session_data))

        # 按更新时间倒序排列
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return sessions

    @staticmethod
    def validate_session_access(session_id: str, username: str, user_session_ids: List[str]) -> bool:
        """
        验证用户是否有权限访问会话

        Args:
            session_id: 会话ID
            username: 用户名
            user_session_ids: 用户拥有的会话ID列表

        Returns:
            是否有权限
        """
        # 公开会话（无用户关联）可以访问
        session_data = SessionService.load_session(session_id)
        if not session_data:
            return False

        # 如果会话没有关联用户，则公开
        if not session_data.get("username"):
            return True

        # 否则检查是否是该用户的会话
        return session_id in user_session_ids
