"""系统管理API端点"""
from flask import Blueprint, request, jsonify
import os
import logging

logger = logging.getLogger(__name__)

# 创建蓝图
system_bp = Blueprint('system', __name__)


@system_bp.route("/api/sync-data", methods=["POST"])
def sync_data():
    """同步数据：重新扫描目录并更新数据库"""
    from backend.database import init_db, migrate_existing_files, get_statistics

    try:
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


@system_bp.route("/api/statistics", methods=["GET"])
def get_statistics():
    """获取统计信息"""
    try:
        from backend.database import get_statistics
        stats = get_statistics()
        return jsonify({"success": True, **stats})
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@system_bp.route("/health", methods=["GET"])
def health_check():
    """健康检查"""
    return jsonify({"status": "ok"})
