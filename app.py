"""
政策文档分析系统 - Flask后端主入口
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import time
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

from core.opencode_client import OpenCodeClient
from core.analyzer import PolicyAnalyzer
from core.scheduler import AnalysisScheduler, APSCHEDULER_AVAILABLE

# 导入API蓝图
from backend.api.documents import documents_bp
from backend.api.analysis import analysis_bp
from backend.api.auth import auth_bp
from backend.api.system import system_bp

OPENCODE_SERVER_URL = os.getenv('OPENCODE_SERVER_URL', 'http://127.0.0.1:4096')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

app = Flask(__name__)

# 跨域配置
CORS(app, resources={
    r"/api/*": {"origins": "*"},
    r"/ask": {"origins": "*"}
})

# API限流配置（使用更宽松的限制）
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["2000 per day", "500 per hour"],
    storage_uri="memory://"
)

# 初始化服务
opencode_client = OpenCodeClient(OPENCODE_SERVER_URL)
analyzer = PolicyAnalyzer(opencode_client)
scheduler = AnalysisScheduler(analyzer)

# 初始化数据库
try:
    from backend.database import init_db
    init_db()
    logger.info("数据库初始化成功")
except Exception as e:
    logger.error(f"数据库初始化失败: {e}")

# 注册API蓝图
app.register_blueprint(documents_bp)
app.register_blueprint(analysis_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(system_bp)

SESSION_ID = None


def get_session_id():
    """获取OpenCode会话ID"""
    global SESSION_ID
    if SESSION_ID:
        try:
            resp = requests.get(f"{OPENCODE_SERVER_URL}/session/{SESSION_ID}", timeout=30)
            if resp.status_code == 200:
                return SESSION_ID
        except Exception:
            pass
        SESSION_ID = None

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


# ============ 前端页面路由 ============

@app.route("/")
def index():
    """服务Vue前端"""
    index_path = os.path.join(VUE_DIST_DIR, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(VUE_DIST_DIR, 'index.html')
    return jsonify({
        "message": "Vue 前端未构建",
        "hint": "请执行: cd policy-doc-frontend && npm run build"
    }), 503


@app.route("/<path:filename>")
def static_files(filename):
    """服务Vue静态文件"""
    # 排除 API 路径，让它们由蓝图处理
    if filename.startswith('api/') or filename.startswith('ask'):
        return jsonify({"error": "Not found"}), 404
    # 只处理实际存在的静态文件
    file_path = os.path.join(VUE_DIST_DIR, filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(VUE_DIST_DIR, filename)
    # 返回 404 而不是前端首页，避免 API 调用返回 HTML
    return jsonify({"error": "File not found"}), 404


# ============ OpenCode AI问答 ============

@app.route("/health")
def health():
    """健康检查（含OpenCode连接状态）"""
    session_id = get_session_id()
    if session_id:
        return jsonify({"status": "ok", "opencode": "connected"})
    return jsonify({"status": "warning", "opencode": "disconnected"})


@limiter.limit("10 per minute")
@app.route("/ask", methods=["POST"])
def ask():
    """OpenCode AI问答"""
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


# ============ 启动入口 ============

if __name__ == "__main__":
    sched = scheduler.start(interval_days=30)
    logger.info(f"启动 Flask 应用，端口: {FLASK_PORT}")
    logger.info(f"OpenCode 服务器地址: {OPENCODE_SERVER_URL}")
    try:
        app.run(debug=FLASK_DEBUG, host='0.0.0.0', port=FLASK_PORT)
    finally:
        if APSCHEDULER_AVAILABLE and sched:
            scheduler.shutdown()
