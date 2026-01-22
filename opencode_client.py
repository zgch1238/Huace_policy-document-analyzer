"""OpenCode 客户端封装"""
import requests
import json
import logging
import threading
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class OpenCodeClient:
    """OpenCode API 客户端"""

    def __init__(self, server_url: str):
        self.server_url = server_url

    def create_session(self) -> Optional[str]:
        """创建新的会话"""
        try:
            resp = requests.post(f"{self.server_url}/session", json={}, timeout=30)
            if resp.status_code == 200:
                session_id = resp.json().get('id')
                if session_id:
                    logger.info(f"创建新 OpenCode session: {session_id}")
                    return session_id
            return None
        except Exception as e:
            logger.error(f"创建 OpenCode session 失败: {e}")
            return None

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            requests.delete(f"{self.server_url}/session/{session_id}", timeout=10)
            return True
        except Exception:
            return False

    def send_message(self, session_id: str, message: str, on_chunk: Optional[Callable[[str], None]] = None) -> Optional[str]:
        """发送消息并获取回复，使用后台线程避免阻塞"""
        result = {"response": None, "error": None, "completed": False}

        def do_request():
            try:
                # 不再单独验证 session，因为 Flask 的 get_session_id 已经验证过
                # 直接发送消息，如果 session 无效，OpenCode 会返回错误

                payload = {
                    "agent": "general",
                    "parts": [{"type": "text", "text": message}],
                }

                url = f"{self.server_url}/session/{session_id}/message"
                logger.info(f"发送请求到: {url}")
                logger.info(f"消息内容 (前100字符): {message[:100]}")

                # 发送请求，不设置超时或使用较长的超时
                resp = requests.post(url, json=payload, timeout=None)
                logger.info(f"收到响应，状态码: {resp.status_code}")

                if resp.status_code != 200:
                    result["error"] = f"响应状态码异常: {resp.status_code}"
                    result["completed"] = True
                    return

                resp_text = resp.text
                logger.info(f"响应内容 (前200字符): {resp_text[:200]}")

                if not resp_text or resp_text.strip() == '':
                    result["response"] = "分析未返回结果"
                    result["completed"] = True
                    return

                try:
                    resp_data = resp.json()
                    response_parts = resp_data.get("parts", [])
                    full_response = "".join([
                        part.get("text", "")
                        for part in response_parts
                        if part.get("type") == "text"
                    ])
                    result["response"] = full_response if full_response else "分析未返回结果"
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON 解析失败: {e}, 响应内容: {resp_text[:100]}")
                    result["response"] = resp_text if resp_text else "分析未返回结果"

                result["completed"] = True
                logger.info(f"请求完成，响应长度: {len(result.get('response', ''))}")

            except requests.exceptions.Timeout as e:
                logger.error(f"OpenCode 请求超时: {e}")
                result["error"] = "请求超时"
                result["completed"] = True
            except requests.exceptions.ConnectionError as e:
                logger.error(f"连接 OpenCode 失败: {e}")
                result["error"] = "连接失败"
                result["completed"] = True
            except Exception as e:
                logger.error(f"发送消息失败: {type(e).__name__}: {e}")
                import traceback
                logger.error(f"详细错误: {traceback.format_exc()}")
                result["error"] = str(e)
                result["completed"] = True

        # 在后台线程中执行请求
        thread = threading.Thread(target=do_request, daemon=True)
        thread.start()

        # 不设置超时限制，等待请求完成
        thread.join()

        if not result["completed"]:
            logger.warning("请求未完成")
            return "分析未完成，请稍后重试"

        if result["error"]:
            logger.error(f"请求错误: {result['error']}")
            return f"分析失败: {result['error']}"

        return result["response"] if result["response"] else "分析未返回结果"

    def send_message_async(self, session_id: str, message: str):
        """异步发送消息，不等待结果（在新线程中执行）"""
        def do_request():
            try:
                payload = {
                    "agent": "general",
                    "parts": [
                        {
                            "type": "text",
                            "text": message,
                        }
                    ],
                }
                requests.post(
                    f"{self.server_url}/session/{session_id}/message",
                    json=payload,
                    timeout=None
                )
            except Exception as e:
                logger.error(f"异步发送消息失败: {e}")

        import threading
        thread = threading.Thread(target=do_request, daemon=True)
        thread.start()

    def get_existing_session(self) -> Optional[str]:
        """获取现有会话"""
        try:
            resp = requests.get(f"{self.server_url}/session", timeout=10)
            sessions = resp.json()
            if sessions:
                return sessions[0]["id"]
            return None
        except Exception:
            return None

    def validate_session(self, session_id: str) -> bool:
        """验证会话是否有效"""
        try:
            resp = requests.get(f"{self.server_url}/session/{session_id}", timeout=30)
            # 只有 200 响应才表示 session 存在
            return resp.status_code == 200
        except Exception:
            return False
