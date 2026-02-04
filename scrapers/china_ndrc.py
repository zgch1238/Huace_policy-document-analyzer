# -*- coding: utf-8 -*-
"""
中华人民共和国国家发展和改革委员会网站爬虫
网站: https://www.ndrc.gov.cn
搜索页面: https://so.ndrc.gov.cn/s?siteCode=bm04000007&ssl=1&token=&qt=关键词
"""

import time
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from .base import BaseScraper


class ChinaNDRCScraper(BaseScraper):
    """中华人民共和国国家发展和改革委员会网站爬虫"""

    name = "中华人民共和国国家发展和改革委员会"
    base_url = "https://www.ndrc.gov.cn"
    search_base_url = "https://so.ndrc.gov.cn"

    DATE_FILTER_OPTIONS = {
        "1d": "最近1天",
        "7d": "最近7天",
        "30d": "最近1个月",
        "365d": "最近1年",
        "cur-year": "最近1年",
        "pre-year": "全部",
    }

    def search_with_selenium(self, keyword, date_filter=None):
        results = []
        search_url = f"{self.search_base_url}/s?siteCode=bm04000007&ssl=1&token=&qt={quote(keyword)}"

        self.log(f"访问搜索页面: {search_url}")

        driver = self.init_browser()
        if not driver:
            return results

        try:
            driver.get(search_url)
            self.log("页面加载中，等待搜索结果...")
            time.sleep(8)

            if date_filter:
                self._click_date_filter(driver, date_filter)
                time.sleep(4)

            results = self._scrape_all_pages(driver)

        except Exception as e:
            self.log(f"[错误] Selenium搜索失败: {e}", "error")

        return results

    def _click_date_filter(self, driver, date_filter):
        filter_name = self.DATE_FILTER_OPTIONS.get(date_filter, "全部")
        try:
            time.sleep(2)
            try:
                date_btn = driver.find_element(By.XPATH, f"//a[contains(text(), '{filter_name}')]")
                if date_btn and date_btn.is_displayed():
                    driver.execute_script("arguments[0].click();", date_btn)
                    time.sleep(4)
                    return True
            except:
                pass
        except:
            pass
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

            result_items = soup.select('div.result-item') or \
                          soup.select('div.search-result') or \
                          soup.select('li.result-item') or \
                          soup.select('div[class*="result"]')

            if not result_items:
                break

            for idx, item in enumerate(result_items, 1):
                try:
                    result = self._parse_result_item(item, seen_urls)
                    if result:
                        results.append(result)
                        seen_urls.add(result['url'])
                except:
                    continue

            if not self._click_next_page(driver, current_page):
                break

            current_page += 1

        self.log(f"共爬取 {current_page-1} 页，提取到 {len(results)} 条有效结果")
        return results

    def _parse_result_item(self, item, seen_urls):
        try:
            link = item.find('a', href=True)
            if not link:
                return None

            title = link.get_text(strip=True)
            if not title:
                title_elem = item.find(['h3', 'h4', 'div'], class_=lambda x: x and 'title' in x.lower())
                if title_elem:
                    title = title_elem.get_text(strip=True)

            if not title:
                return None

            href = link.get('href', '')
            if not href or href.startswith('#') or href.startswith('javascript'):
                return None

            if href.startswith('/'):
                full_url = self.base_url + href
            elif href.startswith('http'):
                full_url = href
            else:
                full_url = urljoin(self.base_url, href)

            if full_url in seen_urls:
                return None

            if '/s?' in full_url or 'search' in full_url.lower():
                return None

            date_str = ""
            date_elem = item.find(['span', 'div'], class_=lambda x: x and ('date' in x.lower() or 'time' in x.lower()))
            if date_elem:
                date_str = date_elem.get_text(strip=True)
            else:
                import re
                text = item.get_text()
                date_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', text)
                if date_match:
                    date_str = date_match.group(1).replace('/', '-')

            content = ""
            content_elem = item.find(['p', 'div'], class_=lambda x: x and ('content' in x.lower() or 'abstract' in x.lower()))
            if content_elem:
                content = content_elem.get_text(strip=True)

            return {
                "title": title,
                "Url": full_url,
                "date": date_str,
                "content": content,
            }

        except:
            return None

    def _click_next_page(self, driver, current_page):
        next_page = current_page + 1

        try:
            try:
                next_btn = driver.find_element(By.XPATH, "//a[contains(text(), '下一页') or contains(text(), '下页')]")
                if next_btn and next_btn.is_displayed():
                    class_attr = next_btn.get_attribute('class') or ''
                    if 'disabled' in class_attr.lower():
                        return False

                    driver.execute_script("arguments[0].click();", next_btn)
                    time.sleep(4)
                    return True
            except:
                pass

            try:
                next_link = driver.find_element(By.XPATH, f"//a[text()='{next_page}']")
                if next_link and next_link.is_displayed():
                    driver.execute_script("arguments[0].click();", next_link)
                    time.sleep(4)
                    return True
            except:
                pass

        except:
            pass

        return False

    def scrape(self, keywords, start_date, end_date=None, date_filter=None, **kwargs):
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

                search_results = self.search_with_selenium(keyword, date_filter=date_filter)

                if not search_results:
                    continue

                for item in search_results:
                    try:
                        title = item.get("title", "")
                        url = item.get("url", "")
                        date_str = item.get("date", "")
                        content = item.get("content", "")

                        if not title or not url:
                            continue

                        if url in seen_urls:
                            continue
                        seen_urls.add(url)
                        total_processed += 1

                        pub_date = self.parse_date_string(date_str)

                        if pub_date:
                            if start_date and pub_date < start_date:
                                continue
                            if end_date and pub_date > end_date:
                                continue

                        date_display = pub_date.strftime('%Y-%m-%d') if pub_date else "未知"

                        result = {
                            "publish_date": pub_date.strftime("%Y年%m月") if pub_date else "未知",
                            "publish_date_full": date_display,
                            "publisher": self.name,
                            "title": title,
                            "doc_number": "",
                            "category": "搜索结果",
                            "keyword_contexts": [{"keyword": keyword, "context": content[:200] if content else f"通过搜索【{keyword}】找到此结果"}],
                            "url": url,
                            "matched_keywords": [keyword],
                        }

                        results.append(result)
                        total_matched += 1

                    except:
                        continue

                time.sleep(1)

        finally:
            self.close_browser()

        print("\n" + "="*60, flush=True)
        print("  爬取完成!", flush=True)
        print("="*60, flush=True)
        print(f"  共检索: {total_processed} 篇", flush=True)
        print(f"  匹配: {total_matched} 篇", flush=True)

        return results