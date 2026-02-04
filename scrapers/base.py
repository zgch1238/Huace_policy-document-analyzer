# -*- coding: utf-8 -*-
"""
爬虫基类
提供通用的浏览器操作、日期解析等功能
"""

import re
import time
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil.parser import parse as parse_date
from urllib.parse import urljoin, urlparse, quote
import logging

# Selenium相关
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# 禁用SSL警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# 降低Selenium相关日志级别，避免显示详细的错误堆栈
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('webdriver_manager').setLevel(logging.WARNING)


class BaseScraper:
    """爬虫基类 - 提供通用功能"""

    # 子类需要覆盖的属性
    name = "基础爬虫"
    base_url = ""

    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        self.session.headers.update(self.headers)
        self.driver = None

    def init_browser(self):
        """初始化Chrome浏览器"""
        if self.driver:
            return self.driver

        self.log("正在初始化浏览器...")

        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 无头模式
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument(f'--user-agent={self.headers["User-Agent"]}')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

        # 尝试多种方式初始化浏览器
        methods = [
            ("本地缓存的ChromeDriver", self._init_with_cached_driver),
            ("自动下载ChromeDriver", self._init_with_manager),
            ("系统Chrome", self._init_with_system_chrome),
        ]

        for method_name, init_func in methods:
            try:
                self.log(f"尝试使用 {method_name}...")
                driver = init_func(chrome_options)
                if driver:
                    self.driver = driver
                    # 增加页面加载超时时间到120秒
                    self.driver.set_page_load_timeout(120)
                    # 设置隐式等待时间为10秒
                    self.driver.implicitly_wait(10)
                    # 设置脚本超时时间
                    self.driver.set_script_timeout(60)
                    self.log(f"浏览器初始化成功! (使用 {method_name})")
                    return self.driver
            except Exception as e:
                self.log(f"  {method_name} 失败: {e}")
                continue

        self.log("[错误] 所有浏览器初始化方法都失败了", "error")
        return None

    def _init_with_cached_driver(self, chrome_options):
        """使用本地缓存的ChromeDriver"""
        import os
        import glob

        # 查找缓存的ChromeDriver
        cache_paths = [
            os.path.expanduser("~/.wdm/drivers/chromedriver"),
            "C:/Users/Administrator/.wdm/drivers/chromedriver",
        ]

        for cache_path in cache_paths:
            if os.path.exists(cache_path):
                # 查找最新版本的chromedriver.exe
                pattern = os.path.join(cache_path, "**", "chromedriver.exe")
                drivers = glob.glob(pattern, recursive=True)
                if drivers:
                    # 使用最新的驱动
                    latest_driver = max(drivers, key=os.path.getmtime)
                    self.log(f"  找到缓存的驱动: {latest_driver}")
                    service = Service(latest_driver)
                    return webdriver.Chrome(service=service, options=chrome_options)

        return None

    def _init_with_manager(self, chrome_options):
        """使用webdriver-manager自动下载"""
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)

    def _init_with_system_chrome(self, chrome_options):
        """尝试直接使用系统Chrome（不指定驱动）"""
        return webdriver.Chrome(options=chrome_options)

    def safe_get_page(self, driver, url, max_retries=3, wait_after_load=3):
        """安全地加载页面，带重试机制"""
        for retry in range(max_retries):
            try:
                driver.get(url)
                time.sleep(wait_after_load)
                return True
            except TimeoutException:
                if retry < max_retries - 1:
                    wait_time = (retry + 1) * 5
                    self.log(f"  页面加载超时，{wait_time}秒后重试 ({retry + 1}/{max_retries})...")
                    time.sleep(wait_time)
                else:
                    self.log(f"  页面加载超时，已达到最大重试次数", "error")
                    return False
            except Exception as e:
                if retry < max_retries - 1:
                    wait_time = (retry + 1) * 5
                    self.log(f"  页面加载出错: {e}，{wait_time}秒后重试 ({retry + 1}/{max_retries})...")
                    time.sleep(wait_time)
                else:
                    self.log(f"  页面加载失败: {e}", "error")
                    return False
        return False

    def close_browser(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

    def log(self, message, level="info"):
        """输出带时间戳的日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}", flush=True)
        if level == "error":
            logger.error(message)

    def fetch_page(self, url, encoding=None):
        """获取页面内容（使用requests）"""
        try:
            response = self.session.get(url, timeout=30, verify=False)
            if encoding:
                response.encoding = encoding
            else:
                response.encoding = response.apparent_encoding or 'utf-8'
            return response.text
        except Exception as e:
            self.log(f"[错误] 获取页面失败: {url}, 错误: {e}", "error")
            return None

    def parse_date_string(self, date_str):
        """解析日期字符串"""
        if not date_str:
            return None

        date_str = str(date_str).strip()

        date_patterns = [
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
            r'(\d{4})\.(\d{1,2})\.(\d{1,2})',
            r'(\d{4})/(\d{1,2})/(\d{1,2})',
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    return datetime(year, month, day)
                except:
                    continue

        try:
            return parse_date(date_str, fuzzy=True)
        except:
            return None

    def extract_keywords_context(self, text, keywords, context_length=200):
        """提取包含关键词的上下文"""
        contexts = []
        if not text:
            return contexts
        text_lower = text.lower()

        for keyword in keywords:
            keyword_lower = keyword.lower()
            start = 0
            found_count = 0
            while found_count < 3:
                pos = text_lower.find(keyword_lower, start)
                if pos == -1:
                    break

                context_start = max(0, pos - context_length // 2)
                context_end = min(len(text), pos + len(keyword) + context_length // 2)

                context = text[context_start:context_end]
                if context_start > 0:
                    context = "..." + context
                if context_end < len(text):
                    context = context + "..."

                highlighted = context.replace(keyword, f"【{keyword}】")

                contexts.append({
                    "keyword": keyword,
                    "context": highlighted
                })

                start = pos + 1
                found_count += 1

        return contexts

    def contains_keywords(self, text, keywords):
        """检查文本是否包含任意关键词"""
        if not text:
            return False
        text_lower = text.lower()
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return True
        return False

    def extract_article_content(self, url, content_selectors=None, use_existing_driver=True, extract_attachments=False):
        """提取文章正文内容并转换为Markdown格式"""
        try:
            # 优先使用已有的浏览器实例
            driver = None
            if use_existing_driver and self.driver:
                driver = self.driver
            else:
                driver = self.init_browser()

            if not driver:
                # 如果浏览器不可用，尝试使用requests
                result = self._extract_content_with_requests(url, content_selectors)
                if extract_attachments:
                    attachments = self._extract_attachments_from_soup(BeautifulSoup(self.fetch_page(url) or "", 'lxml'), url)
                    return {"content": result, "attachments": attachments}
                return result

            self.log(f"正在提取正文内容: {url[:80]}...")

            # 使用安全加载方法
            if not self.safe_get_page(driver, url, max_retries=3, wait_after_load=3):
                # 如果Selenium加载失败，尝试使用requests作为备用方案
                self.log("  Selenium加载失败，尝试使用requests方式...")
                result = self._extract_content_with_requests(url, content_selectors)
                if extract_attachments:
                    soup = BeautifulSoup(self.fetch_page(url) or "", 'lxml')
                    attachments = self._extract_attachments_from_soup(soup, url)
                    return {"content": result, "attachments": attachments}
                return result

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')

            # 移除脚本和样式
            for script in soup(["script", "style", "noscript"]):
                script.decompose()

            # 查找正文内容
            content_elem = None

            if content_selectors:
                for selector in content_selectors:
                    try:
                        content_elem = soup.select_one(selector)
                        if content_elem:
                            self.log(f"  找到内容区域: {selector}")
                            break
                    except:
                        continue

            # 如果没找到，尝试通用选择器
            if not content_elem:
                common_selectors = [
                    '#ivs_content',
                    '.xxgk_content_nr',
                    'div[class*="content"]',
                    'div[class*="article"]',
                    'div[class*="main"]',
                    'article',
                    '.content',
                    '#content'
                ]
                for selector in common_selectors:
                    try:
                        content_elem = soup.select_one(selector)
                        if content_elem:
                            self.log(f"  找到内容区域: {selector}")
                            break
                    except:
                        continue

            if not content_elem:
                self.log(f"  未找到正文内容区域")
                markdown_content = ""
            else:
                # 转换为Markdown
                markdown_content = self._html_to_markdown(content_elem)

            if markdown_content:
                self.log(f"  [成功] 成功提取正文内容 ({len(markdown_content)} 字符)")
            else:
                self.log(f"  [警告] 正文内容为空")

            # 提取附件信息
            attachments = []
            if extract_attachments:
                attachments = self._extract_attachments_from_soup(soup, url)
                if attachments:
                    self.log(f"  [成功] 找到 {len(attachments)} 个附件")

            if extract_attachments:
                return {"content": markdown_content, "attachments": attachments}
            else:
                return markdown_content

        except Exception as e:
            self.log(f"  提取正文内容失败: {e}", "error")
            if extract_attachments:
                return {"content": "", "attachments": []}
            return ""

    def _extract_content_with_requests(self, url, content_selectors=None):
        """使用requests提取内容（备用方法）"""
        try:
            html = self.fetch_page(url)
            if not html:
                return ""

            soup = BeautifulSoup(html, 'lxml')

            # 移除脚本和样式
            for script in soup(["script", "style", "noscript"]):
                script.decompose()

            # 查找正文内容
            content_elem = None
            if content_selectors:
                for selector in content_selectors:
                    try:
                        content_elem = soup.select_one(selector)
                        if content_elem:
                            break
                    except:
                        continue

            if not content_elem:
                return ""

            return self._html_to_markdown(content_elem)

        except Exception as e:
            self.log(f"  requests方式提取失败: {e}", "error")
            return ""

    def _extract_attachments_from_soup(self, soup, page_url):
        """从BeautifulSoup对象中提取附件链接"""
        attachments = []

        try:
            document_extensions = ['.doc', '.docx', '.pdf', '.xls', '.xlsx', '.ppt', '.pptx',
                                  '.zip', '.rar', '.txt', '.csv', '.xml']

            exclude_keywords = ['>', '搜索', '网站地图', '首页', '返回', '上一页', '下一页']
            exclude_url_patterns = ['search', 'query', 'index.html', 'wzdt', 'jiucuo']

            def is_document_url(url):
                url_lower = url.lower()
                url_clean = url_lower.split('?')[0]
                return any(url_clean.endswith(ext) for ext in document_extensions)

            all_links = soup.find_all('a', href=True)

            for link in all_links:
                link_text = link.get_text(strip=True)
                href = link.get('href', '')

                if not href or href.startswith('#') or href.startswith('javascript'):
                    continue

                if any(exclude_kw in link_text for exclude_kw in exclude_keywords):
                    continue

                href_lower = href.lower()
                if any(pattern in href_lower for pattern in exclude_url_patterns):
                    continue

                if is_document_url(href):
                    if href.startswith('/'):
                        full_url = self.base_url + href
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        full_url = urljoin(page_url, href)

                    filename = link_text.strip()
                    if not filename or filename in ['附件', '下载', '点击下载', '查看', '打开']:
                        filename = href.split('/')[-1].split('?')[0]
                        try:
                            import urllib.parse
                            filename = urllib.parse.unquote(filename, encoding='utf-8')
                        except:
                            pass
                        if not filename or '.' not in filename:
                            filename = f"附件_{len(attachments) + 1}"

                    file_type = ""
                    href_clean = href_lower.split('?')[0]
                    for ext in document_extensions:
                        if href_clean.endswith(ext):
                            file_type = ext.lstrip('.')
                            break

                    if not any(att['url'] == full_url for att in attachments):
                        attachments.append({
                            "name": filename,
                            "url": full_url,
                            "file_type": file_type,
                            "size": None
                        })

            # 去重
            seen_urls = set()
            unique_attachments = []
            for att in attachments:
                if att['url'] not in seen_urls:
                    seen_urls.add(att['url'])
                    unique_attachments.append(att)

            return unique_attachments

        except Exception as e:
            self.log(f"  提取附件失败: {e}", "error")
            return []

    def download_attachment(self, attachment_url, save_dir=None, filename=None):
        """下载附件文件"""
        try:
            self.log(f"正在下载附件: {attachment_url[:80]}...")

            response = self.session.get(attachment_url, timeout=60, verify=False, stream=True)
            response.raise_for_status()

            if not filename:
                content_disposition = response.headers.get('Content-Disposition', '')
                if 'filename=' in content_disposition:
                    import re
                    import urllib.parse
                    match = re.search(r'filename\*=UTF-8\'\'([^;]+)', content_disposition)
                    if match:
                        filename = urllib.parse.unquote(match.group(1), encoding='utf-8')
                    else:
                        match = re.search(r'filename[^;=\n]*=(([\'"]).*?\2|[^;\n]*)', content_disposition)
                        if match:
                            filename = match.group(1).strip('\'"')
                            try:
                                filename = urllib.parse.unquote(filename, encoding='utf-8')
                            except:
                                pass

            if not filename:
                filename = attachment_url.split('/')[-1].split('?')[0]
                try:
                    import urllib.parse
                    filename = urllib.parse.unquote(filename, encoding='utf-8')
                except:
                    pass
                if not filename or '.' not in filename:
                    filename = "attachment"

            file_content = response.content

            if save_dir:
                import os
                os.makedirs(save_dir, exist_ok=True)

                safe_filename = self._sanitize_filename(filename)
                filepath = os.path.join(save_dir, safe_filename)

                with open(filepath, 'wb') as f:
                    f.write(file_content)

                file_size = len(file_content)
                self.log(f"  [成功] 附件已保存: {safe_filename} ({file_size} 字节)")
                return filepath
            else:
                return file_content

        except Exception as e:
            self.log(f"  下载附件失败: {e}", "error")
            return None

    def _sanitize_filename(self, filename):
        """清理文件名，移除非法字符，保留中文字符"""
        import re
        import os
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)
        filename = re.sub(r'\s+', '_', filename)
        filename = filename.strip('. ')
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200-len(ext)] + ext
        return filename or "attachment"

    def _html_to_markdown(self, html_element):
        """将HTML元素转换为Markdown格式"""
        try:
            from markdownify import markdownify as md

            html_str = str(html_element)

            markdown = md(
                html_str,
                heading_style="ATX",
                bullets="-",
                convert=['p', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                        'strong', 'b', 'em', 'i', 'ul', 'ol', 'li', 'blockquote',
                        'code', 'pre', 'table', 'tr', 'td', 'th', 'a', 'img', 'div', 'span']
            )

            import re
            markdown = re.sub(r'\n{3,}', '\n\n', markdown)

            lines = [line.rstrip() for line in markdown.split('\n')]
            markdown = '\n'.join(lines)
            markdown = re.sub(r'\n\n\n+', '\n\n', markdown)

            return markdown.strip()

        except ImportError:
            self.log("  markdownify未安装，使用简单文本提取", "error")
            return html_element.get_text(separator='\n', strip=True)
        except Exception as e:
            self.log(f"  HTML转Markdown失败: {e}", "error")
            return self._manual_html_to_markdown(html_element)

    def _manual_html_to_markdown(self, html_element):
        """手动将HTML转换为Markdown（备用方法）"""
        try:
            markdown_lines = []

            for elem in html_element.descendants:
                if elem.name == 'p':
                    text = elem.get_text(strip=True)
                    if text:
                        if elem.find(['strong', 'b']):
                            content = str(elem)
                            import re
                            content = re.sub(r'<strong>(.*?)</strong>', r'**\1**', content, flags=re.DOTALL)
                            content = re.sub(r'<b>(.*?)</b>', r'**\1**', content, flags=re.DOTALL)
                            from bs4 import BeautifulSoup
                            soup = BeautifulSoup(content, 'lxml')
                            text = soup.get_text(separator=' ', strip=True)
                            markdown_lines.append(text)
                        else:
                            markdown_lines.append(text)
                elif elem.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    text = elem.get_text(strip=True)
                    if text:
                        level = int(elem.name[1])
                        markdown_lines.append('#' * level + ' ' + text)
                elif elem.name == 'br':
                    markdown_lines.append('')

            result = '\n'.join(markdown_lines)
            import re
            result = re.sub(r'\n{3,}', '\n\n', result)
            return result.strip()

        except Exception as e:
            return html_element.get_text(separator='\n', strip=True)

    def scrape(self, keywords, start_date, end_date=None, date_filter=None, **kwargs):
        """主爬取方法 - 子类必须实现"""
        raise NotImplementedError("子类必须实现 scrape 方法")