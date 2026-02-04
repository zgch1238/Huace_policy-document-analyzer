"""政策文档分析器"""
import os
import json
import re
import logging
import threading
import concurrent.futures
from datetime import datetime
from typing import List, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass

from core.opencode_client import OpenCodeClient

logger = logging.getLogger(__name__)


@dataclass
class AnalyzerConfig:
    """分析器配置"""
    STATUS_FILE: str = '../data/analyze_status.json'
    ANALYZE_DIR: str = 'analyze_result'

    @property
    def status_file_path(self) -> str:
        """获取状态文件完整路径"""
        # 从 core/ 向上两级到项目根目录
        return str(Path(__file__).parent.parent.parent / 'data' / 'analyze_status.json')

    @property
    def analyze_dir_path(self) -> str:
        """获取分析结果目录完整路径（项目根目录下的 analyze_result）"""
        # 从 core/ 向上两级到项目根目录
        return str(Path(__file__).parent.parent / self.ANALYZE_DIR)


class PolicyAnalyzer:
    """政策文档分析器"""

    # 类级别的进度追踪
    _progress = {
        'running': False,
        'total': 0,
        'current': 0,
        'success': 0,
        'failed': 0,
        'current_file': '',
        'start_time': None
    }
    _progress_lock = threading.Lock()

    def __init__(self, opencode_client: OpenCodeClient, config: AnalyzerConfig = None):
        self.client = opencode_client
        self.config = config or AnalyzerConfig()

    def update_progress(self, current: int = None, success: int = None, failed: int = None, current_file: str = None):
        """更新分析进度"""
        with self._progress_lock:
            if current is not None:
                self._progress['current'] = current
            if success is not None:
                self._progress['success'] = success
            if failed is not None:
                self._progress['failed'] = failed
            if current_file is not None:
                self._progress['current_file'] = current_file

    def start_progress(self, total: int):
        """开始新的分析任务"""
        with self._progress_lock:
            self._progress = {
                'running': True,
                'total': total,
                'current': 0,
                'success': 0,
                'failed': 0,
                'current_file': '',
                'start_time': datetime.now().isoformat()
            }

    def stop_progress(self):
        """停止分析任务"""
        with self._progress_lock:
            self._progress['running'] = False

    def get_progress(self) -> dict:
        """获取当前分析进度"""
        with self._progress_lock:
            return {
                'running': self._progress['running'],
                'total': self._progress['total'],
                'current': self._progress['current'],
                'success': self._progress['success'],
                'failed': self._progress['failed'],
                'current_file': self._progress['current_file'],
                'progress_percent': round(self._progress['current'] / self._progress['total'] * 100, 1) if self._progress['total'] > 0 else 0,
                'start_time': self._progress['start_time']
            }

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

    def save_analysis_result(self, file_path: str, analysis_text: str) -> Optional[str]:
        """
        保存分析结果到 analyze_result 目录

        Args:
            file_path: 源文件相对路径
            analysis_text: AI 返回的分析结果文本

        Returns:
            保存的文件路径，失败返回 None
        """
        # 获取分析结果目录
        analyze_dir = self.config.analyze_dir_path
        os.makedirs(analyze_dir, exist_ok=True)

        # 过滤 AI 思考内容，只保留以 ## 文档 开头的分析结果
        lines = analysis_text.split('\n')
        start_idx = 0
        for i, line in enumerate(lines):
            # 找到分析结果开始的位置
            if line.strip().startswith('## 文档') or line.strip().startswith('# 文档'):
                start_idx = i
                break
        else:
            # 如果没找到标准格式，尝试找到第一个 ## 或 # 标题
            for i, line in enumerate(lines):
                if line.strip().startswith('##') or line.strip().startswith('# '):
                    start_idx = i
                    break

        # 截取有效内容
        content = '\n'.join(lines[start_idx:]).strip()
        if not content:
            logger.warning(f"未找到有效的分析结果内容: {file_path}")
            return None

        # 提取评分
        score_match = re.search(r'> \*\*总分\*\*[：:]\s*([\d.]+)', content)
        score = float(score_match.group(1)) if score_match else 0.0

        # 如果总分低于30分，不保存分析结果
        if score < 30:
            logger.info(f"总分 {score} < 30，不保存分析结果: {file_path}")
            return None

        score_str = str(score)
        # 从源文件路径提取文档名（完整标题）
        doc_name = os.path.basename(file_path)
        doc_title = os.path.splitext(doc_name)[0]

        # 获取相对路径，保留子文件夹结构
        rel_path = os.path.dirname(file_path)
        if rel_path and rel_path != '.':
            # 保持相对路径结构
            target_dir = os.path.join(analyze_dir, rel_path)
        else:
            target_dir = analyze_dir

        os.makedirs(target_dir, exist_ok=True)

        # 构建文件名：{完整标题}_分析结果_{评分}.md
        filename = f"{doc_title}_分析结果_{score_str}.md"
        output_path = os.path.join(target_dir, filename)

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"保存分析结果: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"保存分析结果失败: {e}")
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
        """获取已分析的文件名列表（基于文件名判断，递归扫描所有子目录）"""
        analyzed_files = set()
        if not os.path.exists(analyze_dir):
            return analyzed_files

        # 递归扫描所有子目录
        for root, dirs, files in os.walk(analyze_dir):
            for file in files:
                if file.endswith('.md') and '_分析结果_' in file:
                    # 计算相对于 analyze_dir 的路径
                    rel_path = os.path.relpath(os.path.join(root, file), analyze_dir)
                    # 去掉 "_分析结果_X.X.md" 后缀，提取原始文档相对路径
                    base_path = rel_path.replace('_分析结果_', ' ').rsplit(' ', 1)[0]
                    # 去掉 .md 后缀
                    if base_path.endswith('.md'):
                        base_path = base_path[:-3]
                    # 添加相对路径（带 .md 后缀）
                    analyzed_files.add(base_path + '.md')

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

        # 复用单个 session 分析所有文档
        session_id = self.client.create_session()
        if not session_id:
            logger.error(f"无法创建 session，无法分析任何文档")
            return 0, len(files_to_analyze)

        logger.info(f"创建分析 session: {session_id}")

        # 逐个发送 prompt，让 AI 按 skill 自己处理
        for i, file_path in enumerate(files_to_analyze):
            logger.info(f"分析文档 ({i+1}/{len(files_to_analyze)}): {file_path}")

            # 检查 session 是否仍有效，失效则重建
            if not self.client.validate_session(session_id):
                session_id = self.client.create_session()
                if not session_id:
                    logger.error(f"无法创建 session，跳过: {file_path}")
                    failed_count += 1
                    continue
                logger.info(f"重建 session: {session_id}")

            # 只发送 prompt，AI 返回分析结果，Python 保存文件
            prompt = f"""请使用 policy-document-analyzer skill 分析 {file_path} 这篇政策文档，只返回分析结果文本，不要保存文件。"""

            # 发送并等待响应（不设置超时）
            result = self.client.send_message(session_id, prompt)
            if result:
                # Python 保存分析结果
                saved_path = self.save_analysis_result(file_path, result)
                if saved_path:
                    success_count += 1
                    logger.info(f"文档分析完成: {file_path}")
                else:
                    failed_count += 1
                    logger.error(f"保存分析结果失败: {file_path}")
            else:
                failed_count += 1
                logger.error(f"文档分析失败: {file_path}")

        # 记录完成状态
        logger.info(f"增量分析完成: 新增成功 {success_count}, 失败 {failed_count}")
        self.save_status(datetime.now().isoformat(), success_count, 'success')

        # 分析完成后同步数据库
        if success_count > 0 or failed_count > 0:
            try:
                from backend.database import init_db, migrate_existing_files
                init_db()
                migrate_existing_files()
                logger.info("数据库同步完成")
            except Exception as e:
                logger.error(f"数据库同步失败: {e}")

            # 高亮政策文档
            try:
                from core.highlight import highlight_all_documents
                highlight_count = highlight_all_documents(policy_dir)
                logger.info(f"高亮处理完成: {highlight_count} 个文件")
            except Exception as e:
                logger.error(f"高亮处理失败: {e}")

        logger.info("=" * 50)
        logger.info("定时分析任务执行完毕")
        logger.info("=" * 50)

        return success_count, failed_count

    def run_parallel_analysis(self, policy_dir: str, max_workers: int = 5) -> Tuple[int, int]:
        """并行分析政策文档（多session并发）"""
        logger.info("=" * 50)
        logger.info("开始执行并行分析任务")
        logger.info("=" * 50)

        # 确保 analyze_result 目录存在
        analyze_dir = self.config.analyze_dir_path
        os.makedirs(analyze_dir, exist_ok=True)

        # 获取文档列表
        doc_files = self.get_policy_documents(policy_dir)
        if not doc_files:
            logger.warning(f"没有找到政策文档: {policy_dir}")
            self.save_status(datetime.now().isoformat(), 0, 'no_docs')
            self.stop_progress()
            return 0, 0

        logger.info(f"找到 {len(doc_files)} 个政策文档")

        # 获取已分析的文件列表
        analyzed_files = self.get_analyzed_files(analyze_dir)
        logger.info(f"已有 {len(analyzed_files)} 个文档已分析过")

        # 过滤出未分析的文档
        files_to_analyze = [f for f in doc_files if f not in analyzed_files]

        if not files_to_analyze:
            logger.info("所有文档都已分析完成，无需新分析")
            self.save_status(datetime.now().isoformat(), 0, 'no_new_docs')
            self.stop_progress()
            return 0, 0

        logger.info(f"需要分析的新文档: {len(files_to_analyze)} 个，使用 {max_workers} 个并行任务")

        # 启动进度追踪
        self.start_progress(len(files_to_analyze))

        # 线程安全的计数器
        lock = threading.Lock()
        success_count = 0
        failed_count = 0

        def analyze_file(file_path: str, session_id: str, policy_dir: str) -> bool:
            """用指定session分析单个文件，返回是否成功"""
            nonlocal success_count, failed_count
            # 更新当前处理的文件
            self.update_progress(current_file=file_path)
            prompt = f"""请使用 policy-document-analyzer skill 分析 {file_path} 这篇政策文档，只返回分析结果文本，不要保存文件。"""
            result = self.client.send_message(session_id, prompt)
            with lock:
                if result:
                    # Python 保存分析结果
                    saved_path = self.save_analysis_result(file_path, result)
                    if saved_path:
                        success_count += 1
                        self.update_progress(success=success_count, current=success_count + failed_count)
                        logger.info(f"[Session-{session_id[:8]}] 分析完成: {file_path}")

                        # 立即执行高亮处理和分析结果Word转换
                        try:
                            from core.highlight import highlight_doc, convert_analysis_to_word
                            doc_path = os.path.join(policy_dir, file_path)
                            if os.path.exists(doc_path):
                                # 生成高亮文档
                                success_hl, _, _ = highlight_doc(doc_path, verbose=False)
                                if success_hl:
                                    logger.info(f"[Session-{session_id[:8]}] 高亮文档完成: {file_path}")
                                # 生成分析结果Word文档
                                success_wd, _, _ = convert_analysis_to_word(doc_path, verbose=False)
                                if success_wd:
                                    logger.info(f"[Session-{session_id[:8]}] 分析结果Word完成: {file_path}")
                        except Exception as e:
                            logger.error(f"[Session-{session_id[:8]}] Word生成失败: {file_path}, {e}")

                        return True
                    else:
                        failed_count += 1
                        logger.error(f"[Session-{session_id[:8]}] 保存分析结果失败: {file_path}")
                        return False
                else:
                    failed_count += 1
                    self.update_progress(failed=failed_count, current=success_count + failed_count)
                    logger.error(f"[Session-{session_id[:8]}] 分析失败: {file_path}")
                    return False

        # 将文件分成 max_workers 组
        groups = [[] for _ in range(max_workers)]
        for i, file_path in enumerate(files_to_analyze):
            groups[i % max_workers].append(file_path)

        # 创建 max_workers 个 session
        sessions = []
        for i in range(max_workers):
            session_id = self.client.create_session()
            if session_id:
                sessions.append(session_id)
                logger.info(f"创建 Session-{i+1}: {session_id}")

        if not sessions:
            logger.error("无法创建任何 session")
            self.stop_progress()
            return 0, len(files_to_analyze)

        # 并行执行分析任务
        def analyze_group(group_files: list, session_id: str, worker_id: int):
            """分析一组文件"""
            logger.info(f"Worker-{worker_id} 开始分析，使用 session {session_id[:8]}")
            for file_path in group_files:
                if not self.client.validate_session(session_id):
                    # session 失效，尝试重建
                    new_session = self.client.create_session()
                    if new_session:
                        session_id = new_session
                        logger.info(f"Worker-{worker_id} 重建 session: {session_id[:8]}")
                    else:
                        with lock:
                            failed_count += 1
                        self.update_progress(failed=failed_count, current=success_count + failed_count)
                        continue
                analyze_file(file_path, session_id, policy_dir)

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(sessions)) as executor:
            futures = [
                executor.submit(analyze_group, groups[i], sessions[i], i + 1)
                for i in range(len(sessions))
            ]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"并行分析任务异常: {e}")

        # 确保最终进度更新为完成
        with self._progress_lock:
            self._progress['current'] = self._progress['total']
            self._progress['running'] = False
            logger.info(f"进度追踪完成: current={self._progress['current']}, total={self._progress['total']}, running=False")

        # 记录完成状态
        logger.info(f"并行分析完成: 成功 {success_count}, 失败 {failed_count}")
        self.save_status(datetime.now().isoformat(), success_count, 'success')

        # 分析完成后同步数据库（每个文件高亮已在分析时执行）
        if success_count > 0 or failed_count > 0:
            try:
                from backend.database import init_db, migrate_existing_files
                init_db()
                migrate_existing_files()
                logger.info("数据库同步完成")
            except Exception as e:
                logger.error(f"数据库同步失败: {e}")

        logger.info("=" * 50)
        logger.info("并行分析任务执行完毕")
        logger.info("=" * 50)

        return success_count, failed_count
