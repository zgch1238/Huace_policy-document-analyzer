"""政策文档分析器"""
import os
import json
import logging
from datetime import datetime
from typing import List, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass

from opencode_client import OpenCodeClient

logger = logging.getLogger(__name__)


@dataclass
class AnalyzerConfig:
    """分析器配置"""
    STATUS_FILE: str = 'analyze_status.json'
    ANALYZE_DIR: str = 'analyze_result'

    @property
    def status_file_path(self) -> str:
        """获取状态文件完整路径"""
        return str(Path(__file__).parent / self.STATUS_FILE)

    @property
    def analyze_dir_path(self) -> str:
        """获取分析结果目录完整路径"""
        return str(Path(__file__).parent / self.ANALYZE_DIR)


class PolicyAnalyzer:
    """政策文档分析器"""

    def __init__(self, opencode_client: OpenCodeClient, config: AnalyzerConfig = None):
        self.client = opencode_client
        self.config = config or AnalyzerConfig()

    def get_status_file_path(self) -> str:
        """获取状态文件路径"""
        return self.config.status_file_path

    def save_status(self, last_run: str, result_count: int = 0, status: str = 'success'):
        """保存分析状态"""
        status_data = {
            'last_run': last_run,
            'result_count': result_count,
            'status': status
        }
        try:
            with open(self.get_status_file_path(), 'w', encoding='utf-8') as f:
                json.dump(status_data, f, ensure_ascii=False)
            logger.info(f"保存分析状态: {status_data}")
        except Exception as e:
            logger.error(f"保存分析状态失败: {e}")

    def get_status(self) -> Optional[dict]:
        """获取分析状态"""
        try:
            with open(self.get_status_file_path(), 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.error(f"读取分析状态失败: {e}")
            return None

    def get_policy_documents(self, policy_dir: str) -> List[str]:
        """获取政策文档列表"""
        doc_files = []
        if not os.path.exists(policy_dir):
            return doc_files

        for root, _, files in os.walk(policy_dir):
            for file in files:
                if file.endswith('.md'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, policy_dir)
                    if rel_path == '.':
                        doc_files.append(file)
                    else:
                        doc_files.append(rel_path)

        return doc_files

    def get_analyzed_files(self, analyze_dir: str) -> set:
        """获取已分析的文件名列表（基于文件名判断）"""
        analyzed_files = set()
        if not os.path.exists(analyze_dir):
            return analyzed_files

        for file in os.listdir(analyze_dir):
            if file.endswith('.md') and '_分析结果_' in file:
                # 解析文件名：去掉 "_分析结果_X.X.md" 后缀，提取原始文档名
                base_name = file.replace('_分析结果_', ' ').rsplit(' ', 1)[0] if '_分析结果_' in file else file
                # 尝试从文件名中提取原始文档名（去掉 .md 后缀再拼接）
                if base_name.endswith('.md'):
                    base_name = base_name[:-3]
                analyzed_files.add(base_name + '.md')

        return analyzed_files

    def run_analysis(self, policy_dir: str) -> Tuple[int, int]:
        """执行完整分析任务（增量分析模式）"""
        logger.info("=" * 50)
        logger.info("开始执行定时分析任务")
        logger.info("=" * 50)

        # 确保 analyze_result 目录存在
        analyze_dir = self.config.analyze_dir_path
        os.makedirs(analyze_dir, exist_ok=True)

        # 获取文档列表
        doc_files = self.get_policy_documents(policy_dir)
        if not doc_files:
            logger.warning(f"没有找到政策文档: {policy_dir}")
            self.save_status(datetime.now().isoformat(), 0, 'no_docs')
            return 0, 0

        logger.info(f"找到 {len(doc_files)} 个政策文档")

        # 获取已分析的文件列表（基于文件名判断）
        analyzed_files = self.get_analyzed_files(analyze_dir)
        logger.info(f"已有 {len(analyzed_files)} 个文档已分析过")

        # 过滤出未分析的文档
        files_to_analyze = [f for f in doc_files if f not in analyzed_files]

        if not files_to_analyze:
            logger.info("所有文档都已分析完成，无需新分析")
            self.save_status(datetime.now().isoformat(), 0, 'no_new_docs')
            return 0, 0

        logger.info(f"需要分析的新文档: {len(files_to_analyze)} 个")

        success_count = 0
        failed_count = 0

        # 逐个发送 prompt，让 AI 按 skill 自己处理
        for i, file_path in enumerate(files_to_analyze):
            logger.info(f"分析文档 ({i+1}/{len(files_to_analyze)}): {file_path}")

            # 为每个文档创建独立 session
            session_id = self.client.create_session()
            if not session_id:
                logger.error(f"无法创建 session: {file_path}")
                failed_count += 1
                continue

            # 只发送 prompt，AI 会自己读取文件并按 skill 保存结果
            prompt = f"""请使用 policy-document-analyzer skill 分析 {file_path} 这篇政策文档。"""

            # 发送并等待响应（不设置超时）
            result = self.client.send_message(session_id, prompt)
            if result:
                success_count += 1
                logger.info(f"文档分析完成: {file_path}")
            else:
                failed_count += 1
                logger.error(f"文档分析失败: {file_path}")

            # 不删除 session，让 OpenCode 处理完

        # 记录完成状态
        logger.info(f"增量分析完成: 新增成功 {success_count}, 失败 {failed_count}")
        self.save_status(datetime.now().isoformat(), success_count, 'success')

        logger.info("=" * 50)
        logger.info("定时分析任务执行完毕")
        logger.info("=" * 50)

        return success_count, failed_count
