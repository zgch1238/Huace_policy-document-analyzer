# -*- coding: utf-8 -*-
"""
政府网站配置文件
包含各级政府科技部门的网站地址和爬取规则
"""

# 政府网站配置
GOV_SITES = {
    "中国": {
        "科学技术部": {
            "base_url": "https://www.most.gov.cn",
            "search_url": "https://www.most.gov.cn/search/index.html",
            "list_urls": [
                "https://www.most.gov.cn/xxgk/xinxifenlei/fdzdgknr/fgzc/",
                "https://www.most.gov.cn/xxgk/xinxifenlei/fdzdgknr/qtwj/",
            ],
            "name": "科学技术部"
        },
        "工业和信息化部": {
            "base_url": "https://www.miit.gov.cn",
            "list_urls": [
                "https://www.miit.gov.cn/xwdt/gxdt/",  # 工信动态
                "https://www.miit.gov.cn/zwgk/zcwj/",  # 政策文件
            ],
            "search_url": "https://www.miit.gov.cn/search/index.html?websiteid=110000000000000&ssl=1&token=&qt=",
            "name": "中华人民共和国工业和信息化部"
        },
        "发展和改革委员会": {
            "base_url": "https://www.ndrc.gov.cn",
            "list_urls": [
                "https://www.ndrc.gov.cn/fggz/",  # 发改工作
                "https://www.ndrc.gov.cn/fzggz/zcfg/",  # 政策法规
            ],
            "search_url": "https://so.ndrc.gov.cn/s?siteCode=bm04000007&ssl=1&token=&qt=",
            "name": "中华人民共和国国家发展和改革委员会"
        }
    },
    "上海市": {
        "科学技术委员会": {
            "base_url": "https://stcsm.sh.gov.cn",
            "list_urls": [
                "https://stcsm.sh.gov.cn/zwgk/tzgs/",  # 通知告示
                "https://stcsm.sh.gov.cn/zwgk/kjzc/",  # 科技政策
                "https://stcsm.sh.gov.cn/xmsb/",       # 项目申报
            ],
            "search_patterns": {
                "list_item": "li",
                "title_selector": "a",
                "date_selector": "span",
                "link_attr": "href"
            },
            "name": "上海市科学技术委员会"
        },
        "发展和改革委员会": {
            "base_url": "https://fgw.sh.gov.cn",
            "list_urls": [
                "https://fgw.sh.gov.cn/fgw/xxgk_new/tzgg/",  # 通知公告
                "https://fgw.sh.gov.cn/fgw/xxgk_new/zcwj/",  # 政策文件
            ],
            "search_url": "https://fgw.sh.gov.cn/websearch/#search/query=",
            "name": "上海市发展和改革委员会"
        },
        "经济和信息化委员会": {
            "base_url": "https://mhapi.sheitc.sh.gov.cn",
            "list_urls": [
                "https://mhapi.sheitc.sh.gov.cn/tzgg/",  # 通知公告
                "https://mhapi.sheitc.sh.gov.cn/zcfg/",  # 政策法规
            ],
            "search_url": "https://mhapi.sheitc.sh.gov.cn/websearch.html#search/query=",
            "name": "上海市经济和信息化委员会"
        },
        "农业农村委员会": {
            "base_url": "https://nyncw.sh.gov.cn",
            "list_urls": [
                "https://nyncw.sh.gov.cn/tzgg/",  # 通知公告
                "https://nyncw.sh.gov.cn/zcfg/",  # 政策法规
            ],
            "search_url": "https://nyncw.sh.gov.cn/websearch.html#search/query=",
            "name": "上海市农业农村委员会"
        },
        "规划和自然资源局": {
            "base_url": "https://ghzyj.sh.gov.cn",
            "list_urls": [
                "https://ghzyj.sh.gov.cn/xxgk/tzgg/",  # 通知公告
                "https://ghzyj.sh.gov.cn/xxgk/zcfg/",  # 政策法规
            ],
            "search_url": "https://ghzyj.sh.gov.cn/websearch/#search/query=",
            "name": "上海市规划和自然资源局"
        },
        "交通委员会": {
            "base_url": "https://jtw.sh.gov.cn",
            "list_urls": [
                "https://jtw.sh.gov.cn/xxgk/tzgg/",  # 通知公告
                "https://jtw.sh.gov.cn/xxgk/zcfg/",  # 政策法规
            ],
            "search_url": "https://jtw.sh.gov.cn/websearch/index.html#search/query=",
            "name": "上海市交通委员会"
        },
        "商务委员会": {
            "base_url": "https://sww.sh.gov.cn",
            "list_urls": [
                "https://sww.sh.gov.cn/xxgk/tzgg/",  # 通知公告
                "https://sww.sh.gov.cn/xxgk/zcfg/",  # 政策法规
            ],
            "search_url": "https://sww.sh.gov.cn/websearch.html#search/query=",
            "name": "上海市商务委员会"
        }
    },
    "北京市": {
        "科学技术委员会": {
            "base_url": "https://kw.beijing.gov.cn",
            "list_urls": [
                "https://kw.beijing.gov.cn/col/col2963/index.html",
            ],
            "name": "北京市科学技术委员会"
        }
    },
    "广东省": {
        "科学技术厅": {
            "base_url": "https://gdstc.gd.gov.cn",
            "list_urls": [
                "https://gdstc.gd.gov.cn/zwgk_n/tzgg/",
            ],
            "name": "广东省科学技术厅"
        }
    },
    "江苏省": {
        "科学技术厅": {
            "base_url": "https://kxjst.jiangsu.gov.cn",
            "list_urls": [
                "https://kxjst.jiangsu.gov.cn/col/col84870/index.html",
            ],
            "name": "江苏省科学技术厅"
        }
    },
    "浙江省": {
        "科学技术厅": {
            "base_url": "https://kjt.zj.gov.cn",
            "list_urls": [
                "https://kjt.zj.gov.cn/col/col1229124964/index.html",
            ],
            "name": "浙江省科学技术厅"
        }
    },
    "四川省": {
        "科学技术厅": {
            "base_url": "https://kjt.sc.gov.cn",
            "list_urls": [
                "https://kjt.sc.gov.cn/scst/c100495/common_list.shtml",
            ],
            "name": "四川省科学技术厅"
        }
    },
    "重庆市": {
        "科学技术局": {
            "base_url": "https://kjj.cq.gov.cn",
            "list_urls": [
                "https://kjj.cq.gov.cn/zwgk_249/zfxxgkml/zcwj/",
            ],
            "name": "重庆市科学技术局"
        }
    },
    "湖北省": {
        "科学技术厅": {
            "base_url": "https://kjt.hubei.gov.cn",
            "list_urls": [
                "https://kjt.hubei.gov.cn/kjdt/tzgg/",
            ],
            "name": "湖北省科学技术厅"
        }
    },
    "湖南省": {
        "科学技术厅": {
            "base_url": "https://kjt.hunan.gov.cn",
            "list_urls": [
                "https://kjt.hunan.gov.cn/kjt/xxgk/tzgg/",
            ],
            "name": "湖南省科学技术厅"
        }
    }
}

# 行政级别选项
ADMIN_LEVELS = {
    "国家级": ["中国"],
    "省级/直辖市": ["上海市", "北京市", "广东省", "江苏省", "浙江省", "四川省", "重庆市", "湖北省", "湖南省"],
}

def get_site_config(region, department):
    """获取指定地区和部门的网站配置"""
    if region in GOV_SITES and department in GOV_SITES[region]:
        return GOV_SITES[region][department]
    return None

def get_all_regions():
    """获取所有支持的地区"""
    return list(GOV_SITES.keys())

def get_departments_by_region(region):
    """获取指定地区的所有部门"""
    if region in GOV_SITES:
        return list(GOV_SITES[region].keys())
    return []