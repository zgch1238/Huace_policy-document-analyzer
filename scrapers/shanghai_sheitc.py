# -*- coding: utf-8 -*-
"""
上海市经济和信息化委员会网站爬虫
网站: https://mhapi.sheitc.sh.gov.cn
搜索页面: https://mhapi.sheitc.sh.gov.cn/websearch.html#search/query=关键词

特点:
- 使用网站原生搜索功能（与上海市科委、发改委类似）
- 支持时间筛选（3d/7d/30d/90d/cur-year/pre-year）
- 支持自动翻页
- 搜索结果在 div.maya-result-item 中
- 日期在 span.doc-date 中
- 下一页按钮: <span title="下一页">»</span>
"""

import time
from datetime import datetime
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from .base import BaseScraper


class ShanghaiSHEITCScraper(BaseScraper):
    """上海市经济和信息化委员会网站爬虫"""

    name = "上海市经济和信息化委员会"
    base_url = "https://mhapi.sheitc.sh.gov.cn"

    # 时间筛选选项映射
    DATE_FILTER_OPTIONS = {
        "3d": "最近3天",
        "7d": "最近7天",
        "30d": "最近1个月",
        "90d": "最近3个月",
        "cur-year": "今年",
        "pre-year": "去年",
    }

    # 板块选项映射
    SECTION_OPTIONS = {
        "all": "全部",
        "xwzx": "新闻中心",
        "xxgk": "政务公开",
        "hdpt": "互动平台",
        "jxdj": "经信党建",
    }

    def search_with_selenium(self, keyword, date_filter=None, section_filter='all'):
        """
        使用Selenium访问搜索页面

        参数:
            keyword: 搜索关键词
            date_filter: 时间筛选选项（3d/7d/30d/90d/cur-year/pre-year）
            section_filter: 板块筛选选项（all/xwzx/xxgk/hdpt/jxdj）

        返回:
            搜索结果列表，每项包含 title, url, date
        """
        results = []
        search_url = f"{self.base_url}/websearch.html#search/query={quote(keyword)}"

        self.log(f"访问搜索页面: {search_url}")

        driver = self.init_browser()
        if not driver:
            self.log("[错误] 无法启动浏览器", "error")
            return results

        try:
            driver.get(search_url)
            self.log("页面加载中，等待搜索结果...")

            # 等待页面加载
            time.sleep(5)

            # 先点击时间筛选，再点击板块筛选
            if date_filter:
                self._click_date_filter(driver, date_filter)
                time.sleep(2)

            # 如果指定了板块筛选，最后点击板块
            if section_filter and section_filter != 'all':
                section_name = self.SECTION_OPTIONS.get(section_filter, section_filter)
                clicked = self._click_section_filter(driver, section_filter)
                if not clicked:
                    raise Exception(f"板块「{section_name}」无内容或无法访问")

            # 分页爬取所有结果
            results = self._scrape_all_pages(driver)

        except Exception as e:
            self.log(f"[错误] Selenium搜索失败: {e}", "error")
            # 如果是板块无内容的错误，重新抛出以便前端处理
            if "板块" in str(e) and "无内容" in str(e):
                raise
            # 其他错误记录后继续

        return results

    def _click_date_filter(self, driver, date_filter):
        """点击时间筛选按钮"""
        filter_name = self.DATE_FILTER_OPTIONS.get(date_filter, date_filter)
        self.log(f"尝试点击时间筛选按钮: {filter_name}")

        try:
            time.sleep(2)

            # 方法1: CSS选择器
            try:
                date_btn = driver.find_element(By.CSS_SELECTOR, f'a[search-date-range="{date_filter}"]')
                if date_btn and date_btn.is_displayed():
                    self.log(f"找到时间筛选按钮，尝试点击...")
                    driver.execute_script("arguments[0].click();", date_btn)
                    self.log(f"✓ 成功点击时间筛选按钮: {filter_name}")
                    time.sleep(3)
                    return True
            except Exception as e1:
                self.log(f"CSS选择器方式失败: {e1}")

            # 方法2: XPath
            try:
                date_btn = driver.find_element(By.XPATH, f'//a[@search-date-range="{date_filter}"]')
                if date_btn and date_btn.is_displayed():
                    driver.execute_script("arguments[0].click();", date_btn)
                    self.log(f"✓ 通过XPath成功点击时间筛选按钮: {filter_name}")
                    time.sleep(3)
                    return True
            except Exception as e2:
                self.log(f"XPath方式失败: {e2}")

            # 方法3: JavaScript
            try:
                js_code = f'''
                    var btn = document.querySelector('a[search-date-range="{date_filter}"]');
                    if (btn) {{ btn.click(); return true; }}
                    return false;
                '''
                clicked = driver.execute_script(js_code)
                if clicked:
                    self.log(f"✓ 通过JavaScript成功点击时间筛选按钮: {filter_name}")
                    time.sleep(3)
                    return True
                else:
                    self.log(f"JavaScript未找到按钮")
            except Exception as e3:
                self.log(f"JavaScript方式失败: {e3}")

        except Exception as e:
            self.log(f"点击时间筛选按钮失败: {e}")

        return False

    def _click_section_filter(self, driver, section_filter):
        """点击板块筛选按钮"""
        section_name = self.SECTION_OPTIONS.get(section_filter, section_filter)
        self.log(f"点击板块筛选: {section_name}")

        def check_active():
            """检查目标板块是否已激活"""
            try:
                return driver.execute_script(f'''
                    var target = document.querySelector('li[view-code="{section_filter}"]');
                    return target ? target.classList.contains('active') : false;
                ''')
            except:
                return False

        try:
            time.sleep(1)

            # 如果已激活，直接返回
            if check_active():
                self.log(f"板块 {section_name} 已激活")
                return True

            # 使用模拟鼠标点击
            from selenium.webdriver.common.action_chains import ActionChains
            element = driver.find_element(By.CSS_SELECTOR, f'li[view-code="{section_filter}"]')
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.3)
            ActionChains(driver).move_to_element(element).click().perform()

            # 等待active状态变化
            for i in range(3):
                time.sleep(1)
                if check_active():
                    self.log(f"✓ 板块 {section_name} 已激活")
                    time.sleep(2)  # 等待AJAX加载
                    return True

            self.log(f"[警告] 板块切换未成功", "warning")
            return False

        except Exception as e:
            self.log(f"板块筛选失败: {e}")
            return False

    def _scrape_all_pages(self, driver):
        """爬取所有页面的结果"""
        results = []
        seen_urls = set()
        current_page = 1
        max_pages = 50  # 最多爬取50页

        while current_page <= max_pages:
            self.log(f"正在爬取第 {current_page} 页...")

            # 滚动页面确保内容加载
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)

            # 获取当前页面源码并解析
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')

            # 查找搜索结果
            result_items = soup.select('div.maya-result-item')

            # 调试信息
            if not result_items:
                self.log(f"  [调试] 未找到 div.maya-result-item，尝试其他选择器...")
                result_items = soup.select('div.result-item') or \
                              soup.select('div.search-result-item') or \
                              soup.select('div[class*="result"]')
                self.log(f"  [调试] 找到 {len(result_items)} 个备选结果项")

            page_results_count = 0

            for item in result_items:
                try:
                    result = self._parse_result_item(item, seen_urls)
                    if result:
                        results.append(result)
                        seen_urls.add(result['url'])
                        page_results_count += 1
                except Exception as e:
                    continue

            self.log(f"第 {current_page} 页提取到 {page_results_count} 条结果，累计 {len(results)} 条")

            # 尝试点击下一页
            if not self._click_next_page(driver):
                self.log(f"没有更多页面，停止翻页")
                break

            current_page += 1

        self.log(f"共爬取 {current_page-1} 页，提取到 {len(results)} 条有效结果")
        return results

    def _parse_result_item(self, item, seen_urls):
        """解析单个搜索结果项"""
        # 提取链接
        link = item.find('a', href=True)
        if not link:
            return None

        # 提取日期
        date_span = item.find('span', class_='doc-date')
        date_str = date_span.get_text(strip=True) if date_span else ""

        title = link.get_text(strip=True) or "无标题"
        href = link.get('href', '')

        # 过滤无效链接
        if not href or href.startswith('#') or href.startswith('javascript'):
            return None

        # 构建完整URL
        if href.startswith('/'):
            full_url = self.base_url + href
        elif href.startswith('http'):
            full_url = href
        else:
            full_url = urljoin(self.base_url, href)

        # 过滤搜索页面本身
        if 'websearch' in full_url:
            return None

        # 去重
        if full_url in seen_urls:
            return None

        return {
            "title": title,
            "url": full_url,
            "date": date_str,
            "content": "",
        }

    def _click_next_page(self, driver):
        """点击下一页按钮，返回是否成功"""
        # 方法1: CSS选择器
        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, 'span[title="下一页"]')
            if next_btn and next_btn.is_displayed():
                self.log(f"找到下一页按钮，点击翻页...")
                driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(3)
                return True
        except:
            pass

        # 方法2: XPath
        try:
            next_btn = driver.find_element(By.XPATH, '//span[@title="下一页"]')
            if next_btn and next_btn.is_displayed():
                self.log(f"通过XPath找到下一页按钮，点击翻页...")
                driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(3)
                return True
        except:
            pass

        # 方法3: JavaScript
        try:
            js_code = '''
                var btn = document.querySelector('span[title="下一页"]');
                if (btn) { btn.click(); return true; }
                return false;
            '''
            clicked = driver.execute_script(js_code)
            if clicked:
                self.log(f"通过JavaScript点击下一页按钮...")
                time.sleep(3)
                return True
        except:
            pass

        return False

    def scrape(self, keywords, start_date, end_date=None, date_filter=None, fetch_content=True, section_filter='all', **kwargs):
        """
        爬取上海市经济和信息化委员会网站

        参数:
            keywords: 关键词列表
            start_date: 开始日期 (datetime对象)
            end_date: 结束日期 (datetime对象，可选)
            date_filter: 时间筛选选项（3d/7d/30d/90d/cur-year/pre-year）
        """
        results = []
        seen_urls = set()

        # 打印任务信息
        print("\n" + "="*60, flush=True)
        print(f"  开始爬取{self.name}", flush=True)
        print("="*60, flush=True)
        print(f"  目标网站: {self.base_url}", flush=True)
        print(f"  搜索链接: {self.base_url}/websearch.html#search/query=关键词", flush=True)
        print(f"  搜索关键词: {', '.join(keywords)}", flush=True)
        start_str = start_date.strftime('%Y-%m-%d') if start_date else '不限'
        end_str = end_date.strftime('%Y-%m-%d') if end_date else '今天'
        print(f"  日期范围: {start_str} 至 {end_str}", flush=True)
        if date_filter:
            print(f"  网站筛选: {self.DATE_FILTER_OPTIONS.get(date_filter, date_filter)}", flush=True)
        print("="*60, flush=True)

        total_processed = 0
        total_matched = 0

        try:
            # 对每个关键词进行搜索
            for kw_idx, keyword in enumerate(keywords, 1):
                print(f"\n[关键词 {kw_idx}/{len(keywords)}] 搜索: {keyword}", flush=True)
                print("-"*50, flush=True)

                # 使用Selenium搜索（传递板块筛选参数）
                search_results = self.search_with_selenium(keyword, date_filter=date_filter, section_filter=section_filter)

                if not search_results:
                    self.log(f"关键词 '{keyword}' 未找到搜索结果")
                    continue

                self.log(f"关键词 '{keyword}' 找到 {len(search_results)} 条搜索结果")

                # 处理搜索结果
                skipped_by_date = 0
                skipped_by_quotes = 0
                for item in search_results:
                    try:
                        title = item.get("title", "")
                        url = item.get("url", "")
                        date_str = item.get("date", "")

                        if not title or not url:
                            continue

                        # 避免重复
                        if url in seen_urls:
                            continue
                        seen_urls.add(url)

                        total_processed += 1

                        # 检查标题是否包含书名号
                        if '《' not in title or '》' not in title:
                            skipped_by_quotes += 1
                            continue

                        pub_date = self.parse_date_string(date_str)

                        # 检查日期范围
                        if pub_date:
                            if start_date and pub_date < start_date:
                                skipped_by_date += 1
                                short_t = title[:30] + "..." if len(title) > 30 else title
                                self.log(f"    [跳过-日期早] {pub_date.strftime('%Y-%m-%d')} {short_t}")
                                continue
                            if end_date and pub_date > end_date:
                                skipped_by_date += 1
                                continue

                        # 构建结果
                        date_display = pub_date.strftime('%Y-%m-%d') if pub_date else "未知"

                        result = {
                            "publish_date": pub_date.strftime("%Y年%m月") if pub_date else "未知",
                            "publish_date_full": date_display,
                            "publisher": self.name,
                            "title": title,
                            "doc_number": "",
                            "category": "搜索结果",
                            "keyword_contexts": [{"keyword": keyword, "context": f"通过搜索【{keyword}】找到此结果"}],
                            "url": url,
                            "matched_keywords": [keyword],
                            "full_content": "",  # 将在后面提取
                        }

                        results.append(result)
                        total_matched += 1

                        short_title = title[:50] + "..." if len(title) > 50 else title
                        print(f"  [{total_matched}] [{date_display}] {short_title}", flush=True)

                    except Exception as e:
                        self.log(f"  处理结果时出错: {e}", "error")
                        continue

                if skipped_by_date > 0:
                    self.log(f"因日期不在范围内跳过: {skipped_by_date} 条")

                # 关键词之间稍作等待
                time.sleep(1)

            # 提取所有结果的正文内容和附件
            if results and fetch_content:
                print("\n" + "="*60, flush=True)
                print("  开始提取正文内容和附件...", flush=True)
                print("="*60, flush=True)

                skipped_quotes_count = 0
                for idx, result in enumerate(results, 1):
                    title = result.get("title", "")
                    url = result.get("url", "")

                    # 检查标题是否包含书名号
                    if '《' not in title or '》' not in title:
                        skipped_quotes_count += 1
                        result["full_content"] = ""
                        result["attachments"] = []
                        continue

                    if url:
                        print(f"\n[{idx}/{len(results)}] 提取正文: {title[:50]}...", flush=True)
                        # 上海市经信委网站的内容选择器，同时提取附件
                        content_result = self.extract_article_content(
                            url,
                            content_selectors=['#ivs_content', '.xxgk_content_nr', 'div.xxgk_content_nr', '.article-content'],
                            extract_attachments=True
                        )

                        # 处理返回结果（可能是字符串或字典）
                        if isinstance(content_result, dict):
                            result["full_content"] = content_result.get("content", "")
                            result["attachments"] = content_result.get("attachments", [])
                        else:
                            result["full_content"] = content_result
                            result["attachments"] = []

                        # 如果有附件，打印信息
                        if result.get("attachments"):
                            print(f"    找到 {len(result['attachments'])} 个附件:", flush=True)
                            for att in result["attachments"]:
                                print(f"      - {att.get('name', '未知')} ({att.get('file_type', '未知类型')})", flush=True)

                        time.sleep(1)  # 避免请求过快
            elif results and not fetch_content:
                print("\n" + "="*60, flush=True)
                print("  跳过提取正文内容（用户未勾选）", flush=True)
                print("="*60, flush=True)

        finally:
            self.close_browser()

        # 打印完成信息
        print("\n" + "="*60, flush=True)
        print("  爬取完成!", flush=True)
        print("="*60, flush=True)
        print(f"  共检索: {total_processed} 篇", flush=True)
        print(f"  匹配: {total_matched} 篇", flush=True)
        if skipped_by_quotes > 0:
            print(f"  无书名号跳过: {skipped_by_quotes} 篇", flush=True)
        if skipped_quotes_count > 0:
            print(f"  正文提取时无书名号跳过: {skipped_quotes_count} 篇", flush=True)
        print("="*60 + "\n", flush=True)

        return results
