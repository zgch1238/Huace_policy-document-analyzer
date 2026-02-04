#!/usr/bin/env python3
"""
数据库初始化脚本
运行此脚本初始化数据库并迁移现有数据
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import init_db, migrate_existing_files, get_statistics

def main():
    print("=" * 50)
    print("政策文档管理系统 - 数据库初始化")
    print("=" * 50)

    # 1. 初始化数据库表结构
    print("\n[1/2] 初始化数据库...")
    init_db()
    print("  [OK] 数据库表结构创建完成")

    # 2. 迁移现有文件
    print("\n[2/2] 迁移现有文件...")
    migrate_existing_files()
    print("  [OK] 数据迁移完成")

    # 3. 显示统计信息
    print("\n" + "=" * 50)
    stats = get_statistics()
    print("统计信息:")
    print(f"  - 文档总数: {stats['document_count']}")
    print(f"  - 分析结果总数: {stats['analysis_count']}")
    print(f"  - 平均相关度分数: {stats['avg_score']}%")
    print(f"  - 本周分析次数: {stats['week_analysis']}")
    print("=" * 50)
    print("\n初始化完成！可以启动应用了。")

if __name__ == "__main__":
    main()
