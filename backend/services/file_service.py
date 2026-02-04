"""文件服务模块 - 提供通用的文件操作服务"""
import os
import time
import logging
import base64
import shutil
import zipfile
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class FileService:
    """文件服务类 - 提供通用的文件下载和删除功能"""

    @staticmethod
    def download_files(file_dir: str, files: List[str], prefix: str = "files") -> Dict[str, Any]:
        """
        通用文件/文件夹下载逻辑

        Args:
            file_dir: 文件目录
            files: 文件/文件夹路径列表
            prefix: 下载文件名的前缀

        Returns:
            包含 success、fileName、content、isBinary 的字典
            如果包含文件夹，返回 folderDownload: True 和 zipPath
        """
        # 检查是否有文件夹
        has_folder = False
        folder_to_download = None

        for file_path in files:
            full_path = os.path.join(file_dir, file_path)
            if os.path.isdir(full_path):
                has_folder = True
                folder_to_download = full_path
                break

        # 如果有文件夹，优先处理文件夹下载
        if has_folder:
            result = FileService.download_folder_as_zip(folder_to_download)
            if result.get("success"):
                return {
                    "success": True,
                    "fileName": result["zipName"],
                    "zipPath": result["zipPath"],
                    "isFolder": True,
                    "message": "文件夹打包成功"
                }
            else:
                return result

        # 纯文件下载（原有逻辑）
        all_content = []
        is_binary = False
        original_file_name = ""

        for file_path in files:
            # 优先查找对应的 docx 文件
            md_path = os.path.join(file_dir, file_path)
            base_name = os.path.splitext(file_path)[0]
            docx_path = os.path.join(file_dir, base_name + '.docx')

            # 确定要下载的文件
            download_path = None
            file_ext = '.md'

            if os.path.exists(docx_path):
                download_path = docx_path
                file_ext = '.docx'
            elif os.path.exists(md_path):
                download_path = md_path
            else:
                logger.warning(f"文件不存在: {file_path}")
                continue

            if download_path:
                # 检测是否为二进制文件
                binary_extensions = ['.docx', '.xlsx', '.pptx', '.pdf', '.zip', '.jpg', '.png', '.gif']

                if file_ext in binary_extensions:
                    # 二进制文件使用 base64 编码
                    try:
                        with open(download_path, 'rb') as f:
                            content = f.read()
                            encoded_content = base64.b64encode(content).decode('utf-8')
                            # 返回 docx 文件名（去掉路径前缀）
                            return_name = os.path.basename(download_path)
                            all_content.append({
                                "fileName": return_name,
                                "content": encoded_content,
                                "isBinary": True
                            })
                            is_binary = True
                            original_file_name = return_name
                    except Exception as e:
                        logger.error(f"读取二进制文件失败: {download_path}, 错误: {e}")
                else:
                    # 文本文件使用 UTF-8 读取
                    try:
                        with open(download_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            all_content.append({
                                "fileName": os.path.basename(download_path),
                                "content": content,
                                "isBinary": False
                            })
                            original_file_name = os.path.basename(download_path)
                    except Exception as e:
                        logger.error(f"读取文件失败: {download_path}, 错误: {e}")

        if not all_content:
            return {
                "success": False,
                "message": "没有找到有效文件",
                "fileName": "",
                "content": "",
                "isBinary": False
            }

        if is_binary and len(all_content) == 1:
            # 单个二进制文件直接返回
            return {
                "success": True,
                "fileName": all_content[0]["fileName"],
                "content": all_content[0]["content"],
                "isBinary": True
            }
        else:
            # 文本文件合并返回
            combined_content = "\n\n".join([
                f"=== {item['fileName']} ===\n\n{item['content']}"
                for item in all_content
            ])
            return {
                "success": True,
                "fileName": f"{prefix}_{time.strftime('%Y%m%d_%H%M%S')}.md",
                "content": combined_content,
                "isBinary": False
            }

    @staticmethod
    def delete_files(file_dir: str, files: List[str]) -> Dict[str, Any]:
        """
        通用文件/文件夹删除逻辑

        Args:
            file_dir: 文件目录
            files: 要删除的文件/文件夹路径列表

        Returns:
            包含 success、message、deletedCount 的字典
        """
        if not files:
            return {
                "success": False,
                "message": "请选择要删除的文件",
                "deletedCount": 0
            }

        deleted_count = 0
        errors = []

        for file_path in files:
            full_path = os.path.join(file_dir, file_path)
            if os.path.exists(full_path):
                try:
                    if os.path.isdir(full_path):
                        # 是文件夹，递归删除
                        shutil.rmtree(full_path)
                        logger.info(f"删除文件夹成功: {full_path}")
                    else:
                        # 是文件，正常删除
                        os.remove(full_path)
                        logger.info(f"删除文件成功: {full_path}")
                    deleted_count += 1
                except Exception as e:
                    error_msg = f"删除失败: {file_path}, 错误: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            else:
                logger.warning(f"不存在: {full_path}")

        if errors:
            return {
                "success": deleted_count > 0,
                "message": f"部分删除失败: {'; '.join(errors[:3])}",
                "deletedCount": deleted_count
            }

        return {
            "success": True,
            "message": f"成功删除 {deleted_count} 个项目",
            "deletedCount": deleted_count
        }

    @staticmethod
    def get_file_list(base_dir: str, extension: str = ".md", exclude_pattern: str = None) -> List[str]:
        """
        获取目录下的文件列表

        Args:
            base_dir: 基础目录
            extension: 文件扩展名过滤
            exclude_pattern: 排除模式（如 "_分析结果_"）

        Returns:
            文件路径列表
        """
        file_list = []

        if not os.path.exists(base_dir):
            return file_list

        for root, _, files in os.walk(base_dir):
            for file in files:
                if not file.endswith(extension):
                    continue
                if exclude_pattern and exclude_pattern in file:
                    continue

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, base_dir)
                if rel_path == '.':
                    file_list.append(file)
                else:
                    file_list.append(rel_path)

        return file_list

    @staticmethod
    def delete_folder(folder_path: str) -> Dict[str, Any]:
        """
        删除文件夹（递归删除）

        Args:
            folder_path: 文件夹路径

        Returns:
            包含 success、message 的字典
        """
        if not folder_path:
            return {
                "success": False,
                "message": "请提供文件夹路径"
            }

        if not os.path.exists(folder_path):
            return {
                "success": False,
                "message": "文件夹不存在"
            }

        if not os.path.isdir(folder_path):
            return {
                "success": False,
                "message": "提供的路径不是文件夹"
            }

        try:
            shutil.rmtree(folder_path)
            logger.info(f"删除文件夹成功: {folder_path}")
            return {
                "success": True,
                "message": "删除成功"
            }
        except Exception as e:
            error_msg = f"删除文件夹失败: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    @staticmethod
    def download_folder_as_zip(folder_path: str) -> Dict[str, Any]:
        """
        将文件夹打包为ZIP并返回打包后的文件路径

        Args:
            folder_path: 文件夹路径

        Returns:
            包含 success、zipPath、zipName、message 的字典
        """
        if not os.path.exists(folder_path):
            return {
                "success": False,
                "zipPath": "",
                "zipName": "",
                "message": "文件夹不存在"
            }

        if not os.path.isdir(folder_path):
            return {
                "success": False,
                "zipPath": "",
                "zipName": "",
                "message": "提供的路径不是文件夹"
            }

        try:
            # 创建临时目录存放ZIP文件
            temp_dir = os.path.join(os.path.dirname(folder_path), "temp_download")
            os.makedirs(temp_dir, exist_ok=True)

            # ZIP文件名使用文件夹名称
            folder_name = os.path.basename(folder_path)
            zip_name = f"{folder_name}.zip"
            zip_path = os.path.join(temp_dir, zip_name)

            # 如果已存在同名ZIP，先删除
            if os.path.exists(zip_path):
                os.remove(zip_path)

            # 创建ZIP文件
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(folder_path):
                    # 保持文件夹结构
                    for file in files:
                        file_path = os.path.join(root, file)
                        # 计算相对路径
                        arcname = os.path.relpath(file_path, os.path.dirname(folder_path))
                        zipf.write(file_path, arcname)

            logger.info(f"文件夹打包成功: {zip_path}")
            return {
                "success": True,
                "zipPath": zip_path,
                "zipName": zip_name,
                "message": "打包成功"
            }
        except Exception as e:
            error_msg = f"打包文件夹失败: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "zipPath": "",
                "zipName": "",
                "message": error_msg
            }
