# -*- coding: utf-8 -*-
"""
爬虫模块初始化
根据不同的地区和部门，提供对应的爬虫实现
"""

from .base import BaseScraper

def get_scraper(region, department):
    """
    根据地区和部门获取对应的爬虫类
    """
    scraper_mapping = {
        "中国": {
            "科学技术部": ("BaseScraper", "base"),
            "工业和信息化部": ("ChinaMIITScraper", "china_miit"),
            "发展和改革委员会": ("ChinaNDRCScraper", "china_ndrc"),
        },
        "上海市": {
            "科学技术委员会": ("ShanghaiSTCSMScraper", "shanghai_stcsm"),
            "发展和改革委员会": ("ShanghaiFGWScraper", "shanghai_fgw"),
            "经济和信息化委员会": ("ShanghaiSHEITCScraper", "shanghai_sheitc"),
            "农业农村委员会": ("ShanghaiNYNCWScraper", "shanghai_nyncw"),
            "规划和自然资源局": ("ShanghaiGHZYJScraper", "shanghai_ghzyj"),
            "交通委员会": ("ShanghaiJTWScraper", "shanghai_jtw"),
            "商务委员会": ("ShanghaiSWWScraper", "shanghai_sww"),
        },
        "北京市": {
            "科学技术委员会": ("BaseScraper", "base"),
        },
        "广东省": {
            "科学技术厅": ("BaseScraper", "base"),
        },
        "江苏省": {
            "科学技术厅": ("BaseScraper", "base"),
        },
        "浙江省": {
            "科学技术厅": ("BaseScraper", "base"),
        },
        "四川省": {
            "科学技术厅": ("BaseScraper", "base"),
        },
        "重庆市": {
            "科学技术局": ("BaseScraper", "base"),
        },
        "湖北省": {
            "科学技术厅": ("BaseScraper", "base"),
        },
        "湖南省": {
            "科学技术厅": ("BaseScraper", "base"),
        },
    }

    if region in scraper_mapping and department in scraper_mapping[region]:
        class_name, module_name = scraper_mapping[region][department]
        return _import_scraper(class_name, module_name)
    return None


def _import_scraper(class_name, module_name):
    """动态导入爬虫类"""
    try:
        module = __import__(f"scrapers.{module_name}", fromlist=[class_name])
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        print(f"[警告] 无法导入爬虫 {class_name}: {e}")
        return None