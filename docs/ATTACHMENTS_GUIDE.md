# 附件爬取功能使用指南

## 功能概述

爬虫现在支持自动识别和提取网页中的附件信息。当爬取包含附件的页面时，系统会自动：

1. **识别附件链接**：自动查找页面中包含"附件"、"下载"等关键词的链接，或指向常见文件类型（.doc, .pdf, .xlsx等）的链接
2. **提取附件信息**：获取附件的名称、URL、文件类型等信息
3. **保存附件信息**：将附件信息保存到CSV和Markdown文件中

## 支持的附件类型

系统会自动识别以下类型的附件：

- 文档：`.doc`, `.docx`, `.pdf`
- 表格：`.xls`, `.xlsx`, `.csv`
- 演示文稿：`.ppt`, `.pptx`
- 压缩文件：`.zip`, `.rar`
- 其他：`.txt`, `.xml`, `.html`

## 使用方法

### 1. 通过Web界面使用

在Web界面中正常进行爬取，系统会自动提取附件信息：

1. 选择地区和部门
2. 输入关键词
3. 设置时间范围
4. 勾选"爬取原文内容"（附件提取功能会自动启用）
5. 点击"开始检索"

### 2. 通过代码使用

```python
from scrapers.shanghai_stcsm import ShanghaiSTCSMScraper
from datetime import datetime

scraper = ShanghaiSTCSMScraper()

# 提取正文内容和附件
result = scraper.extract_article_content(
    url="https://stcsm.sh.gov.cn/zwgk/kyjhxm/xmsb/20250620/906b3ff715ec435fad0db04f1470e9e0.html",
    content_selectors=['#ivs_content', '.xxgk_content_nr'],
    extract_attachments=True  # 启用附件提取
)

if isinstance(result, dict):
    content = result.get("content", "")
    attachments = result.get("attachments", [])

    print(f"找到 {len(attachments)} 个附件")
    for att in attachments:
        print(f"- {att['name']}: {att['url']}")
```

### 3. 下载附件文件

如果需要下载附件到本地：

```python
from scrapers.base import BaseScraper

scraper = BaseScraper()

# 下载附件到指定目录
save_path = scraper.download_attachment(
    attachment_url="https://example.com/file.doc",
    save_dir="./downloads",  # 保存目录
    filename="文件.doc"  # 可选，默认从URL提取
)

if save_path:
    print(f"附件已保存到: {save_path}")
```

## 结果格式

### CSV文件

CSV文件现在包含"附件"列，显示所有附件的名称（多个附件用分号分隔）：

```csv
发布日期,发布年月,发布机构,文件名称,文件编号,分类,关键词匹配,原文链接,附件
2025-06-20,2025年06月,上海市科学技术委员会,关于发布...,,搜索结果,关键词匹配内容,https://...,附件1.doc; 附件2.doc
```

### Markdown文件

Markdown文件在文档头部包含附件信息：

```markdown
# 文件标题

**发布日期**: 2025-06-20
**发布机构**: 上海市科学技术委员会
**原文链接**: [链接](https://...)
**检索时间**: 2025-01-29 10:00:00
**检索关键词**: 关键词1, 关键词2

**附件**:
- [附件1.doc](https://...) (doc)
- [附件2.doc](https://...) (doc)

---

正文内容...
```

### JSON结果

爬取结果中的每条记录现在包含 `attachments` 字段：

```json
{
  "title": "文件标题",
  "url": "https://...",
  "attachments": [
    {
      "name": "附件1.doc",
      "url": "https://...",
      "file_type": "doc",
      "size": null
    }
  ],
  "full_content": "...",
  ...
}
```

## 附件识别规则

系统使用以下规则识别附件：

1. **关键词匹配**：查找包含以下关键词的链接
   - "附件"、"下载"、"相关附件"、"附件下载"、"附件："、"附件1"、"附件2"等

2. **文件扩展名**：查找指向常见文件类型的链接
   - `.doc`, `.docx`, `.pdf`, `.xls`, `.xlsx` 等

3. **附件区域**：查找包含"相关附件"等关键词的区域内的链接

## 注意事项

1. **附件URL**：附件信息中包含的是附件链接，不会自动下载附件文件
2. **文件大小**：文件大小信息通常需要下载后才能获取，默认显示为 `null`
3. **相对链接**：系统会自动将相对链接转换为绝对URL
4. **去重**：相同URL的附件只会记录一次

## 测试

运行测试脚本查看附件提取功能：

```bash
python test_attachments.py
```

## 示例

查看 `test_attachments.py` 文件了解完整的使用示例。
