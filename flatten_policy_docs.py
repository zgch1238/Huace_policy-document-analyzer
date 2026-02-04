"""
将政策文档从结构1转换为结构2

结构1:
policy_document\20260203_131103_上海市_科学技术委员会_测绘_卫星_导航\004_文件名.md
或
policy_document\20260203_131103_上海市_科学技术委员会_测绘_卫星_导航\004_文件名\内容.md

结构2:
policy_document\20260203_131103_上海市_科学技术委员会_测绘_卫星_导航\文件名.md
"""

import os
import re
import shutil

def flatten_policy_documents(policy_dir: str):
    """扁平化政策文档目录结构"""
    moved_count = 0

    # 遍历所有 .md 文件
    for root, dirs, files in os.walk(policy_dir):
        for filename in files:
            if not filename.endswith('.md'):
                continue

            old_path = os.path.join(root, filename)
            rel_path = os.path.relpath(old_path, policy_dir)
            parts = rel_path.split(os.sep)

            # 需要至少 2 层
            if len(parts) < 2:
                continue

            # 第一层: 日期+分类 (保持不变)
            category = parts[0]

            # 文件名
            raw_filename = filename
            # 移除编号前缀 (003_, 082_, 009_ 等)
            filename_clean = re.sub(r'^\d{3}_', '', raw_filename)

            # 目标路径
            new_dir = os.path.join(policy_dir, category)
            new_path = os.path.join(new_dir, filename_clean)

            # 跳过如果目标已存在
            if os.path.exists(new_path):
                print(f"[跳过] 已存在: {rel_path}")
                continue

            # 移动文件
            os.makedirs(new_dir, exist_ok=True)
            shutil.move(old_path, new_path)
            print(f"[移动] {filename_clean}")
            moved_count += 1

            # 删除空的外层目录
            if len(parts) >= 3:
                # 有第三层，删除编号文件夹
                num_dir = os.path.dirname(old_path)
                if os.path.exists(num_dir) and not os.listdir(num_dir):
                    os.rmdir(num_dir)

    print(f"\n完成！移动 {moved_count} 个文件")


if __name__ == '__main__':
    policy_dir = r'c:\Users\admin\Desktop\AI快速工作流\AI Skill分析\policy_document'

    print("=" * 50)
    print("政策文档结构转换工具")
    print("=" * 50)
    print(f"\n目录: {policy_dir}")
    print("\n执行转换...")
    print("=" * 50 + "\n")

    flatten_policy_documents(policy_dir)
