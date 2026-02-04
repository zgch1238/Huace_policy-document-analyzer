# -*- coding: utf-8 -*-
"""
中华人民共和国工业和信息化部网站爬虫
网站: https://www.miit.gov.cn
"""

import time
from datetime import datetime
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from .base import BaseScraper


class ChinaMIITScraper(BaseScraper):
    """中华人民共和国工业和信息化部网站爬虫"""

    name = "中华人民共和国工业和信息化部"
    base_url = "https://www.miit.gov.cn"

    DATE_FILTER_OPTIONS = {
        "1d": "一天内",
        "7d": "一周内",
        "30d": "一月内",
        "365d": "一年内",
        "cur-year": "一年内",
        "pre-year": "全部",
    }

    MIIT_DATE_VALUES = {
        "1d": "1",
        "7d": "2",
        "30d": "3",
        "365d": "4",
        "cur-year": "4",
        "pre-year": "0",
    }

    def search_with_selenium(self, keyword, date_filter=None):
        results = []
        search_url = f"{self.base_url}/search/index.html?websiteid=110000000000000&pg=&p=&tpl=&category=&jsflIndexSeleted=&q={quote(keyword)}"

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
        data_value = self.MIIT_DATE_VALUES.get(date_filter, "0")

        self.log(f"尝试点击时间筛选按钮: {filter_name} (data-value={data_value})")

        try:
            time.sleep(2)
            try:
                css_selector = f'div.jsearch-condition-box-item[data-value="{data_value}"]'
                date_btn = driver.find_element(By.CSS_SELECTOR, css_selector)
                if date_btn and date_btn.is_displayed():
                    driver.execute_script("arguments[0].click();", date_btn)
                    self.log(f"✓ 成功点击时间筛选按钮: {filter_name}")
                    time.sleep(4)
                    return True
            except:
                pass

            try:
                js_code = f'''
                    var items = document.querySelectorAll('div.jsearch-condition-box-item');
                    for (var i = 0; i < items.length; i++) {{
                        if (items[i].getAttribute('data-value') === '{data_value}') {{
                            items[i].click();
                            return true;
                        }}
                    }}
                    return false;
                '''
                clicked = driver.execute_script(js_code)
                if clicked:
                    self.log(f"✓ 通过JavaScript成功点击时间筛选按钮: {filter_name}")
                    time.sleep(4)
                    return True
            except:
                pass

        except Exception as e:
            self.log(f"点击时间筛选按钮失败: {e}")

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

            result_items = soup.select('div.news-type > div.jcse-result-box.news-result')

            if not result_items:
                result_items = soup.select('div.jcse-result-box.news-result')

            if not result_items:
                result_items = soup.select('div.news-result') or soup.select('div[class*="result"]')

            page_results_count = 0

            for idx, item in enumerate(result_items, 1):
                try:
                    result = self._parse_result_item(item, seen_urls)
                    if result:
                        results.append(result)
                        seen_urls.add(result['url'])
                        page_results_count += 1
                except:
                    continue

            self.log(f"第 {current_page} 页提取到 {page_results_count} 条结果，累计 {len(results)} 条")

            if not self._click_next_page(driver, current_page):
                self.log(f"没有更多页面，停止翻页")
                break

            current_page += 1

        self.log(f"共爬取 {current_page-1} 页，提取到 {len(results)} 条有效结果")
        return results

    def _parse_result_item(self, item, seen_urls):
        try:
            link = item.find('a', href=True)
            if not link:
                return None

            title_div = item.find('div', class_='itemdiy')
            if title_div:
                title = title_div.get_text(strip=True)
            else:
                title = link.get_text(strip=True)

            if not title:
                return None

            href = link.get('href', '')
            if not href or href.startswith('#') or href.startswith('javascript'):
                return None

            if href.startswith('/'):
                full_url = self.base_url + href
            elif href.startswith('http'):
                full_url = href
            elif href.startswith('..'):
                search_base = "https://www.miit.gov.cn/search/"
                full_url = urljoin(search_base, href)
            else:
                full_url = urljoin(self.base_url, href)

            if '/search/index.html' in full_url:
                return None

            date_str = ""
            spans = item.find_all('span')
            for span in spans:
                span_text = span.get_text(strip=True)
                if '发布时间：' in span_text or '发布时间:' in span_text:
                    if '发布时间：' in span_text:
                        date_str = span_text.split('发布时间：')[-1].strip()
                    else:
                        date_str = span_text.split('发布时间:')[-1].strip()
                    date_str = date_str.split()[0] if date_str else ""
                    break

            content = ""
            content_p = item.find('p')
            if content_p:
                content = content_p.get_text(strip=True)

            return {
                "title": title,
                "url": full_url,
                "date": date_str,
                "content": content,
            }

        except Exception as e:
            return None

    def _click_next_page(self, driver, current_page):
        next_page = current_page + 1

        try:
            try:
                next_page_element = driver.find_element(By.CSS_SELECTOR, '[paged="下一页"]')
                tag_name = next_page_element.tag_name
                class_attr = next_page_element.get_attribute('class') or ''

                if tag_name == 'span' and 'disabled' in class_attr:
                    return False

                if tag_name == 'a':
                    driver.execute_script("arguments[0].click();", next_page_element)
                    self.log(f"✓ 成功点击「下一页」按钮翻到第 {next_page} 页")
                    time.sleep(4)
                    return True
            except:
                pass

            try:
                next_link = driver.find_element(By.CSS_SELECTOR, f'#pagination a[paged="{next_page}"]')
                if next_link and next_link.is_displayed():
                    driver.execute_script("arguments[0].click();", next_link)
                    time.sleep(4)
                    return True
            except:
                pass

            try:
                js_code = f'''
                    var pagination = document.getElementById('pagination');
                    if (!pagination) return false;
                    var nextBtn = pagination.querySelector('[paged="下一页"]');
                    if (nextBtn && nextBtn.tagName === 'SPAN' && nextBtn.classList.contains('disabled')) {{
                        return false;
                    }}
                    var pageLink = pagination.querySelector('a[paged="{next_page}"]');
                    if (pageLink) {{
                        pageLink.click();
                        return true;
                    }}
                    if (nextBtn && nextBtn.tagName === 'A') {{
                        nextBtn.click();
                        return true;
                    }}
                    return false;
                '''
                clicked = driver.execute_script(js_code)
                if clicked:
                    time.sleep(4)
                    return True
            except:
                pass

        except Exception:
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

                skipped_by_date = 0
                for item in search_results:
                    try:
                        title = item.get("title", "")
                        url = item.get("url", "")
                        date_str = item.get("date", "")
                        content = item.get("content", "")

                        if not title or not url:
                            continue

                        if url in seen_urls:
                            seen_urls.add(url)
                        seen_urls.add(url)
                        total_processed += 1

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
                            "keyword_contexts": [{"keyword": keyword, "context": content[:200] if content else f"通过搜索【{keyword}】找到此结果"}],
                            "url": url,
                            "matched_keywords": [keyword],
                        }

                        results.append(result)
                        total_matched += 1

                    except Exception as e:
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