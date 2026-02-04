# -*- coding: utf-8 -*-
"""
上海市发展和改革委员会网站爬虫
网站: https://fgw.sh.gov.cn
搜索页面: https://fgw.sh.gov.cn/websearch/#search/query=关键词
"""

import time
from datetime import datetime
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from .base import BaseScraper


class ShanghaiFGWScraper(BaseScraper):
    """上海市发展和改革委员会网站爬虫"""

    name = "上海市发展和改革委员会"
    base_url = "https://fgw.sh.gov.cn"

    DATE_FILTER_OPTIONS = {
        "all": "不限时间",
        "3d": "最近3天",
        "7d": "最近7天",
        "30d": "最近1个月",
        "90d": "最近3个月",
        "cur-year": "今年",
        "pre-year": "去年",
    }

    SECTION_OPTIONS = {
        "all": "全部",
        "xwzx": "要闻动态",
        "xxgk": "政务公开",
    }

    def search_with_selenium(self, keyword, date_filter=None, section_filter='all'):
        results = []
        search_url = f"{self.base_url}/websearch/#search/query={quote(keyword)}"

        self.log(f"访问搜索页面: {search_url}")

        driver = self.init_browser()
        if not driver:
            self.log("[错误] 无法启动浏览器", "error")
            return results

        try:
            driver.get(search_url)
            self.log("页面加载中，等待搜索结果...")
            time.sleep(5)

            if date_filter:
                self._click_date_filter(driver, date_filter)
                time.sleep(2)

            if section_filter and section_filter != 'all':
                section_name = self.SECTION_OPTIONS.get(section_filter, section_filter)
                clicked = self._click_section_filter(driver, section_filter)
                if not clicked:
                    raise Exception(f"板块「{section_name}」无内容或无法访问")

            results = self._scrape_all_pages(driver)

        except Exception as e:
            self.log(f"[错误] Selenium搜索失败: {e}", "error")
            if "板块" in str(e) and "无内容" in str(e):
                raise

        return results

    def _click_date_filter(self, driver, date_filter):
        filter_name = self.DATE_FILTER_OPTIONS.get(date_filter, date_filter)
        self.log(f"尝试点击时间筛选按钮: {filter_name}")

        try:
            time.sleep(2)
            try:
                date_btn = driver.find_element(By.CSS_SELECTOR, f'a[search-date-range="{date_filter}"]')
                if date_btn and date_btn.is_displayed():
                    driver.execute_script("arguments[0].click();", date_btn)
                    self.log(f"✓ 成功点击时间筛选按钮: {filter_name}")
                    time.sleep(3)
                    return True
            except:
                pass

            try:
                date_btn = driver.find_element(By.XPATH, f'//a[@search-date-range="{date_filter}"]')
                if date_btn and date_btn.is_displayed():
                    driver.execute_script("arguments[0].click();", date_btn)
                    self.log(f"✓ 通过XPath成功点击时间筛选按钮: {filter_name}")
                    time.sleep(3)
                    return True
            except:
                pass

        except Exception as e:
            self.log(f"点击时间筛选按钮失败: {e}")

        return False

    def _click_section_filter(self, driver, section_filter):
        section_name = self.SECTION_OPTIONS.get(section_filter, section_filter)
        self.log(f"点击板块筛选: {section_name}")

        def check_active():
            try:
                return driver.execute_script(f'''
                    var target = document.querySelector('li[view-code="{section_filter}"]');
                    return target ? target.classList.contains('active') : false;
                ''')
            except:
                return False

        try:
            time.sleep(1)
            if check_active():
                self.log(f"板块 {section_name} 已激活")
                return True

            from selenium.webdriver.common.action_chains import ActionChains
            element = driver.find_element(By.CSS_SELECTOR, f'li[view-code="{section_filter}"]')
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.3)
            ActionChains(driver).move_to_element(element).click().perform()

            for i in range(3):
                time.sleep(1)
                if check_active():
                    self.log(f"✓ 板块 {section_name} 已激活")
                    time.sleep(2)
                    return True

            return False

        except Exception as e:
            self.log(f"板块筛选失败: {e}")
            return False

    def _scrape_all_pages(self, driver):
        results = []
        seen_urls = set()
        current_page = 1
        max_pages = 50

        while current_page <= max_pages:
            self.log(f"正在爬取第 {current_page} 页...")

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')

            result_items = soup.select('div.maya-result-item')

            if not result_items:
                result_items = soup.select('div.result-item') or \
                              soup.select('div.search-result-item') or \
                              soup.select('div[class*="result"]')

            page_results_count = 0

            for item in result_items:
                try:
                    result = self._parse_result_item(item, seen_urls)
                    if result:
                        results.append(result)
                        seen_urls.add(result['url'])
                        page_results_count += 1
                except:
                    continue

            self.log(f"第 {current_page} 页提取到 {page_results_count} 条结果，累计 {len(results)} 条")

            if not self._click_next_page(driver):
                self.log(f"没有更多页面，停止翻页")
                break

            current_page += 1

        self.log(f"共爬取 {current_page-1} 页，提取到 {len(results)} 条有效结果")
        return results

    def _parse_result_item(self, item, seen_urls):
        link = item.find('a', href=True)
        if not link:
            return None

        date_span = item.find('span', class_='doc-date')
        date_str = date_span.get_text(strip=True) if date_span else ""

        title = link.get_text(strip=True) or "无标题"
        href = link.get('href', '')

        if not href or href.startswith('#') or href.startswith('javascript'):
            return None

        if href.startswith('/'):
            full_url = self.base_url + href
        elif href.startswith('http'):
            full_url = href
        else:
            full_url = urljoin(self.base_url, href)

        if 'websearch' in full_url:
            return None

        if full_url in seen_urls:
            return None

        return {
            "title": title,
            "url": full_url,
            "date": date_str,
            "content": "",
        }

    def _click_next_page(self, driver):
        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, 'span[title="下一页"]')
            if next_btn and next_btn.is_displayed():
                driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(3)
                return True
        except:
            pass

        return False

    def scrape(self, keywords, start_date, end_date=None, date_filter=None, fetch_content=True, section_filter='all', **kwargs):
        results = []
        seen_urls = set()

        print("\n" + "="*60, flush=True)
        print(f"  开始爬取{self.name}", flush=True)
        print("="*60, flush=True)

        total_processed = 0
        total_matched = 0

        try:
            for kw_idx, keyword in enumerate(keywords, 1):
                print(f"\n[关键词 {kw_idx}/{len(keywords)}] 搜索: {keyword}", flush=True)

                search_results = self.search_with_selenium(keyword, date_filter=date_filter, section_filter=section_filter)

                if not search_results:
                    continue

                skipped_by_date = 0
                skipped_by_quotes = 0
                for item in search_results:
                    try:
                        title = item.get("title", "")
                        url = item.get("url", "")
                        date_str = item.get("date", "")

                        if not title or not url:
                            continue

                        if url in seen_urls:
                            continue
                        seen_urls.add(url)

                        total_processed += 1

                        # 检查标题是否包含书名号
                        if '《' not in title or '》' not in title:
                            skipped_by_quotes += 1
                            continue

                        pub_date = self.parse_date_string(date_str)

                        if pub_date:
                            if start_date and pub_date < start_date:
                                skipped_by_date += 1
                                continue
                            if end_date and pub_date > end_date:
                                skipped_by_date += 1
                                continue

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
                            "full_content": "",
                        }

                        results.append(result)
                        total_matched += 1

                    except Exception as e:
                        continue

                time.sleep(1)

            if results and fetch_content:
                print("\n开始提取正文内容和附件...")
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
                        print(f"[{idx}/{len(results)}] 提取正文: {title[:50]}...")
                        content_result = self.extract_article_content(
                            url,
                            content_selectors=['#ivs_content', '.xxgk_content_nr', '.article-content'],
                            extract_attachments=True
                        )

                        if isinstance(content_result, dict):
                            result["full_content"] = content_result.get("content", "")
                            result["attachments"] = content_result.get("attachments", [])
                        else:
                            result["full_content"] = content_result
                            result["attachments"] = []

                        time.sleep(1)

        finally:
            self.close_browser()

        print("\n" + "="*60, flush=True)
        print("  爬取完成!", flush=True)
        print("="*60, flush=True)
        print(f"  共检索: {total_processed} 篇", flush=True)
        print(f"  匹配: {total_matched} 篇", flush=True)
        if skipped_by_quotes > 0:
            print(f"  无书名号跳过: {skipped_by_quotes} 篇", flush=True)
        if skipped_quotes_count > 0:
            print(f"  正文提取时无书名号跳过: {skipped_quotes_count} 篇", flush=True)

        return results