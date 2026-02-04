# -*- coding: utf-8 -*-
"""
爬虫API接口
提供政府网站政策信息爬取功能
"""

import sys
import io
import os
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_cors import CORS

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

crawl_bp = Blueprint('crawl', __name__)
CORS(crawl_bp)

# 爬取结果存储基础目录
BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'policy_document')
CSV_DIR = os.path.join(BASE_DIR, 'csv')
os.makedirs(CSV_DIR, exist_ok=True)


def save_results_to_csv(results, keywords, region, department):
    """保存爬取结果到CSV文件"""
    if not results:
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    keywords_str = "_".join(keywords[:3])
    safe_keywords = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in keywords_str)
    filename = f"{timestamp}_{region}_{department}_{safe_keywords}.csv"

    filepath = os.path.join(CSV_DIR, filename)

    try:
        csv_lines = ["发布日期,发布年月,发布机构,文件名称,文件编号,分类,关键词匹配,原文链接,附件"]

        for r in results:
            contexts = r.get('keyword_contexts', [])
            context_text = "; ".join([c.get('context', '')[:100] for c in contexts[:3]])
            context_text = context_text.replace('"', "'").replace('\n', ' ')

            full_date = r.get("publish_date_full", "") or r.get("publish_date", "") or "未知"
            year_month = r.get("publish_date", "") or "未知"

            attachments = r.get('attachments', [])
            if attachments:
                attachment_names = [att.get('name', '未知') for att in attachments]
                attachment_text = "; ".join(attachment_names)
                attachment_text = attachment_text.replace('"', "'").replace('\n', ' ')
            else:
                attachment_text = ""

            line = f'"{full_date}","{year_month}","{r.get("publisher", "")}","{r.get("title", "")}","{r.get("doc_number", "")}","{r.get("category", "")}","{context_text}","{r.get("url", "")}","{attachment_text}"'
            csv_lines.append(line)

        csv_content = "\n".join(csv_lines)

        with open(filepath, 'w', encoding='utf-8-sig') as f:
            f.write(csv_content)

        logger.info(f"CSV结果已保存到: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"保存CSV失败: {e}")
        return None


def sanitize_filename(filename, max_length=100):
    """清理文件名"""
    import re
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)
    filename = re.sub(r'\s+', '_', filename)
    filename = filename.strip('. ')
    if len(filename) > max_length:
        filename = filename[:max_length]
    return filename or "无标题"


def save_markdown_content(results, keywords, region, department):
    """保存爬取结果到Markdown文件"""
    if not results:
        return None

    content_results = [r for r in results if r.get('full_content', '').strip()]
    if not content_results:
        return None

    logger.info(f"保存 {len(content_results)} 条Markdown文件...")

    from scrapers.base import BaseScraper
    scraper = BaseScraper()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    keywords_str = "_".join(keywords[:3])
    safe_keywords = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in keywords_str)
    parent_folder_name = f"{timestamp}_{region}_{department}_{safe_keywords}"

    parent_folder_path = os.path.join(BASE_DIR, parent_folder_name)

    try:
        os.makedirs(parent_folder_path, exist_ok=True)

        saved_count = 0

        for idx, r in enumerate(results, 1):
            title = r.get('title', '无标题')
            url = r.get('url', '')
            publish_date = r.get('publish_date_full', '') or r.get('publish_date', '未知日期')
            publisher = r.get('publisher', '')
            full_content = r.get('full_content', '')

            if not full_content.strip():
                continue

            attachments = r.get('attachments', [])
            safe_title = sanitize_filename(title, max_length=100)
            folder_name = f"{idx:03d}_{safe_title}"

            # 有附件时创建子文件夹，无附件时不创建
            if attachments:
                item_folder = os.path.join(parent_folder_path, folder_name)
                os.makedirs(item_folder, exist_ok=True)
            else:
                item_folder = None

            # md文件始终保存在父目录
            md_filepath = os.path.join(parent_folder_path, f"{folder_name}.md")

            try:
                md_lines = []
                md_lines.append(f"# {title}")
                md_lines.append("")
                md_lines.append(f"**发布日期**: {publish_date}")
                md_lines.append(f"**发布机构**: {publisher}")
                md_lines.append(f"**原文链接**: [{url}]({url})")
                md_lines.append(f"**检索时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                md_lines.append(f"**检索关键词**: {', '.join(keywords)}")

                downloaded_attachments = []

                if attachments:
                    md_lines.append("")
                    md_lines.append("**附件:**")

                    for att in attachments:
                        att_name = att.get('name', '未知')
                        att_url = att.get('url', '')
                        att_type = att.get('file_type', '')

                        if att_url:
                            try:
                                safe_att_name = sanitize_filename(att_name, max_length=150)
                                if att_type and '.' not in safe_att_name:
                                    safe_att_name = f"{safe_att_name}.{att_type}"

                                download_path = scraper.download_attachment(
                                    attachment_url=att_url,
                                    save_dir=item_folder,
                                    filename=safe_att_name
                                )

                                if download_path:
                                    downloaded_attachments.append(os.path.basename(download_path))
                                    md_lines.append(f"- [{att_name}](./{os.path.basename(download_path)})" if att_type else f"- [{att_name}](./{os.path.basename(download_path)})")
                                else:
                                    md_lines.append(f"- [{att_name}]({att_url})" if att_type else f"- [{att_name}]({att_url})")
                            except:
                                md_lines.append(f"- [{att_name}]({att_url})" if att_type else f"- [{att_name}]({att_url})")
                        else:
                            md_lines.append(f"- {att_name} ({att_type})" if att_type else f"- {att_name}")

                md_lines.append("")
                md_lines.append("---")
                md_lines.append("")
                md_lines.append(full_content)

                md_content = "\n".join(md_lines)
                with open(md_filepath, 'w', encoding='utf-8') as f:
                    f.write(md_content)

                if os.path.exists(md_filepath):
                    saved_count += 1

            except Exception as e:
                logger.error(f"保存文件失败: {e}")
                continue

        scraper.close_browser()

        if saved_count > 0:
            logger.info(f"成功保存 {saved_count} 个Markdown文件到: {parent_folder_path}")
            return parent_folder_path

    except Exception as e:
        logger.error(f"保存Markdown失败: {e}")
        scraper.close_browser()

    return None


@crawl_bp.route('/api/crawl/regions', methods=['GET'])
def get_regions():
    """获取所有支持的地区"""
    from scrapers.gov_sites import get_all_regions
    regions = get_all_regions()
    return jsonify({
        "success": True,
        "data": regions
    })


@crawl_bp.route('/api/crawl/departments/<region>', methods=['GET'])
def get_departments(region):
    """获取指定地区的所有部门"""
    from scrapers.gov_sites import get_departments_by_region
    departments = get_departments_by_region(region)
    return jsonify({
        "success": True,
        "data": departments
    })


@crawl_bp.route('/api/crawl/keyword-categories', methods=['GET'])
def get_keyword_categories():
    """获取所有关键词分类"""
    from scrapers.keyword_categories import KEYWORD_CATEGORIES
    return jsonify({
        "success": True,
        "data": KEYWORD_CATEGORIES
    })


@crawl_bp.route('/api/crawl/sections/<region>/<path:department>', methods=['GET'])
def get_sections(region, department):
    """获取指定地区和部门的板块选项"""
    from scrapers import get_scraper

    # URL解码部门名称
    from urllib.parse import unquote
    department = unquote(department)

    ScraperClass = get_scraper(region, department)

    if ScraperClass and hasattr(ScraperClass, 'SECTION_OPTIONS'):
        return jsonify({
            "success": True,
            "data": ScraperClass.SECTION_OPTIONS
        })

    # 如果没有对应爬虫或爬虫没有板块选项，返回空
    return jsonify({
        "success": True,
        "data": {}
    })


@crawl_bp.route('/api/crawl/keywords/<category>', methods=['GET'])
def get_keywords_by_category(category):
    """获取指定分类的关键词"""
    from scrapers.keyword_categories import get_keywords
    from scrapers.keyword_categories import get_subcategories
    subcategory = request.args.get('subcategory')
    keywords = get_keywords(category, subcategory)
    subcategories = get_subcategories(category) if not subcategory else []
    return jsonify({
        "success": True,
        "data": keywords,
        "subcategories": subcategories
    })


@crawl_bp.route('/api/crawl', methods=['POST'])
def crawl():
    """执行爬取任务"""
    try:
        from scrapers import get_scraper

        data = request.get_json()

        region = data.get('region', '')
        department = data.get('department', '')
        keywords_str = data.get('keywords', '')
        start_date = data.get('start_date', '2025-01-01')
        end_date = data.get('end_date', '')

        # 解析日期
        try:
            from datetime import datetime
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d') if start_date else datetime(2025, 1, 1)
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
        except ValueError:
            start_date_obj = datetime(2025, 1, 1)
            end_date_obj = None
        date_filter = data.get('date_filter', '')
        section_filter = data.get('section_filter', 'all')
        fetch_content = data.get('fetch_content', True)

        # 解析关键词
        keywords = [k.strip() for k in keywords_str.split('、') if k.strip()]
        if not keywords:
            keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
        if not keywords:
            keywords = [k.strip() for k in keywords_str.split('，') if k.strip()]

        if not region or not department:
            return jsonify({
                "success": False,
                "error": "请选择地区和部门"
            })

        if not keywords:
            return jsonify({
                "success": False,
                "error": "请输入至少一个关键词"
            })

        logger.info(f"开始爬取: {region} - {department}, 关键词: {keywords}")

        # 调用爬虫
        from scrapers import get_scraper
        ScraperClass = get_scraper(region, department)

        if not ScraperClass:
            return jsonify({
                "success": False,
                "error": f"未找到 {region} - {department} 对应的爬虫"
            })

        scraper = ScraperClass()

        results = scraper.scrape(
            keywords=keywords,
            start_date=start_date_obj,
            end_date=end_date_obj,
            date_filter=date_filter if date_filter else None,
            section_filter=section_filter if section_filter else 'all',
            fetch_content=fetch_content
        )

        # 保存结果
        saved_csv_file = None
        saved_md_file = None
        if results:
            saved_csv_file = save_results_to_csv(results, keywords, region, department)
            saved_md_file = save_markdown_content(results, keywords, region, department)

        return jsonify({
            "success": True,
            "data": results,
            "count": len(results),
            "message": f"共找到 {len(results)} 条相关信息",
            "saved_csv_file": os.path.basename(saved_csv_file) if saved_csv_file else None,
            "saved_md_file": os.path.basename(saved_md_file) if saved_md_file else None
        })

    except Exception as e:
        logger.error(f"爬取失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })


@crawl_bp.route('/api/crawl/site-info', methods=['GET'])
def get_site_info():
    """获取所有支持的网站信息"""
    from scrapers.gov_sites import GOV_SITES
    site_info = []
    for region, departments in GOV_SITES.items():
        for dept, config in departments.items():
            site_info.append({
                "region": region,
                "department": dept,
                "name": config.get('name', ''),
                "base_url": config.get('base_url', '')
            })
    return jsonify({
        "success": True,
        "data": site_info
    })


@crawl_bp.route('/api/crawl/export', methods=['POST'])
def export_results():
    """导出结果为CSV"""
    try:
        data = request.get_json()
        results = data.get('results', [])

        if not results:
            return jsonify({
                "success": False,
                "error": "没有可导出的数据"
            })

        csv_lines = ["发布日期,发布年月,发布机构,文件名称,文件编号,分类,关键词匹配,原文链接,附件"]

        for r in results:
            contexts = r.get('keyword_contexts', [])
            context_text = "; ".join([c.get('context', '')[:100] for c in contexts[:3]])
            context_text = context_text.replace('"', "'").replace('\n', ' ')

            full_date = r.get("publish_date_full", "") or r.get("publish_date", "") or "未知"
            year_month = r.get("publish_date", "") or "未知"

            attachments = r.get('attachments', [])
            if attachments:
                attachment_names = [att.get('name', '未知') for att in attachments]
                attachment_text = "; ".join(attachment_names)
                attachment_text = attachment_text.replace('"', "'").replace('\n', ' ')
            else:
                attachment_text = ""

            line = f'"{full_date}","{year_month}","{r.get("publisher", "")}","{r.get("title", "")}","{r.get("doc_number", "")}","{r.get("category", "")}","{context_text}","{r.get("url", "")}","{attachment_text}"'
            csv_lines.append(line)

        csv_content = "\n".join(csv_lines)

        return jsonify({
            "success": True,
            "data": csv_content
        })

    except Exception as e:
        logger.error(f"导出失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })