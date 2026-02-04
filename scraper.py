# -*- coding: utf-8 -*-
"""
政府网站爬虫核心模块
根据不同的地区和部门，调用对应的爬虫实现
"""

import sys
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class GovScraper:
    """政府网站爬虫 - 调度器"""

    def __init__(self):
        pass

    def log(self, message, level="info"):
        """输出带时间戳的日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}", flush=True)
        if level == "error":
            logger.error(message)

    def scrape(self, region, department, keywords, start_date_str, end_date_str=None, date_filter=None, section_filter='all', fetch_content=True, only_title_with_quotes=False):
        """
        主爬取方法
        """
        # 解析日期
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else None
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else None

        # 打印任务信息
        print("\n" + "#"*60, flush=True)
        print(f"#  任务开始: {region} - {department}", flush=True)
        print(f"#  关键词: {keywords}", flush=True)
        print(f"#  日期: {start_date_str} 至 {end_date_str or '今天'}", flush=True)
        if date_filter:
            filter_names = {
                "3d": "最近3天", "7d": "最近7天", "30d": "最近1个月",
                "90d": "最近3个月", "cur-year": "今年", "pre-year": "去年"
            }
            print(f"#  网站筛选: {filter_names.get(date_filter, date_filter)}", flush=True)
        if section_filter and section_filter != 'all':
            section_names = {
                "all": "全部", "xwzx": "新闻中心", "xxgk": "政务公开",
                "hdpt": "互动平台", "flfg": "法律法规", "zmhd": "公众参与"
            }
            print(f"#  搜索板块: {section_names.get(section_filter, section_filter)}", flush=True)
        print(f"#  爬取原文: {'是' if fetch_content else '否'}", flush=True)
        if only_title_with_quotes:
            print(f"#  标题筛选: 仅爬取包含书名号的条目", flush=True)
        print("#"*60 + "\n", flush=True)

        # 根据地区和部门获取对应的爬虫
        from scrapers import get_scraper

        scraper_class = get_scraper(region, department)

        if scraper_class:
            scraper = scraper_class()
            self.log(f"使用专用爬虫: {scraper.name}")
            return scraper.scrape(
                keywords, start_date, end_date, date_filter,
                section_filter=section_filter, fetch_content=fetch_content,
                only_title_with_quotes=only_title_with_quotes
            )
        else:
            self.log(f"[警告] 未找到 {region} - {department} 的专用爬虫")
            return self._scrape_generic(region, department, keywords, start_date, end_date, date_filter)

    def _scrape_generic(self, region, department, keywords, start_date, end_date, date_filter):
        """通用爬虫（暂未实现）"""
        from gov_sites import get_site_config

        site_config = get_site_config(region, department)
        if site_config:
            self.log(f"找到站点配置: {site_config.get('name', '未知')}")
            self.log(f"通用爬虫功能暂未实现，请为该站点添加专用爬虫")
        else:
            self.log(f"[错误] 未找到 {region} - {department} 的配置", "error")

        return []


if __name__ == "__main__":
    # 测试
    scraper = GovScraper()
    results = scraper.scrape(
        region="上海市",
        department="科学技术委员会",
        keywords=["北斗", "人工智能"],
        start_date_str="2025-01-01",
        date_filter="cur-year"
    )

    print(f"\n共找到 {len(results)} 条结果:")
    for r in results[:5]:
        print(f"\n标题: {r['title']}")
        print(f"发布日期: {r['publish_date']}")
        print(f"链接: {r['url']}")