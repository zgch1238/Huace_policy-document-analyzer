# 附件爬取功能集成说明

## 集成状态

附件爬取功能已成功集成到所有网站的爬虫中。

## 已集成的爬虫

### 上海市级网站（已集成）

1. **上海市科学技术委员会** (`shanghai_stcsm.py`)
   - ✅ 已集成附件提取功能
   - 内容选择器: `['#ivs_content', '.xxgk_content_nr', 'div.xxgk_content_nr']`

2. **上海市商务委员会** (`shanghai_sww.py`)
   - ✅ 已集成附件提取功能
   - 内容选择器: `['#ivs_content', '.xxgk_content_nr', 'div.xxgk_content_nr', '.article-content']`

3. **上海市交通委员会** (`shanghai_jtw.py`)
   - ✅ 已集成附件提取功能
   - 内容选择器: `['#ivs_content', '.xxgk_content_nr', 'div.xxgk_content_nr', '.article-content']`

4. **上海市规划和自然资源局** (`shanghai_ghzyj.py`)
   - ✅ 已集成附件提取功能
   - 内容选择器: `['#ivs_content', '.xxgk_content_nr', 'div.xxgk_content_nr', '.article-content']`

5. **上海市农业农村委员会** (`shanghai_nyncw.py`)
   - ✅ 已集成附件提取功能
   - 内容选择器: `['#ivs_content', '.xxgk_content_nr', 'div.xxgk_content_nr', '.article-content']`

6. **上海市发展和改革委员会** (`shanghai_fgw.py`)
   - ✅ 已集成附件提取功能
   - 内容选择器: `['#ivs_content', '.xxgk_content_nr', 'div.xxgk_content_nr', '.article-content']`

7. **上海市经济和信息化委员会** (`shanghai_sheitc.py`)
   - ✅ 已集成附件提取功能
   - 内容选择器: `['#ivs_content', '.xxgk_content_nr', 'div.xxgk_content_nr', '.article-content']`

### 国家级网站

1. **工业和信息化部** (`china_miit.py`)
   - ⚠️ 当前仅提取搜索结果摘要，未提取正文内容
   - 如需添加，可参考其他爬虫的实现方式

2. **国家发展和改革委员会** (`china_ndrc.py`)
   - ⚠️ 当前仅提取搜索结果摘要，未提取正文内容
   - 如需添加，可参考其他爬虫的实现方式

## 功能特性

### 1. 自动附件识别

- **识别规则**: 如果链接的 `href` 属性以文档扩展名结尾（`.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx` 等），自动识别为附件
- **无需关键词**: 不需要链接文本包含"附件"关键词
- **智能过滤**: 自动排除导航链接、搜索链接等非附件链接

### 2. 附件信息提取

每个附件包含以下信息：
- `name`: 附件名称
- `url`: 附件下载URL
- `file_type`: 文件类型（pdf, doc, docx等）
- `size`: 文件大小（下载后获取）

### 3. 附件下载

- 在保存Markdown文件时自动下载附件
- 附件保存在与Markdown文件相同的文件夹中
- 支持中文文件名

### 4. 结果保存

- **CSV文件**: 包含"附件"列，显示附件名称
- **Markdown文件**: 包含附件链接（相对路径）
- **文件夹结构**: 每个条目有独立文件夹，包含Markdown和附件文件

## 使用方法

### 通过Web界面

1. 选择地区和部门
2. 输入关键词
3. 设置时间范围
4. **勾选"爬取原文内容"**（附件提取功能会自动启用）
5. 点击"开始检索"

系统会自动：
- 提取正文内容
- 识别并提取附件信息
- 下载附件文件
- 保存到结果文件夹

### 通过代码

```python
from scrapers.shanghai_stcsm import ShanghaiSTCSMScraper

scraper = ShanghaiSTCSMScraper()
results = scraper.scrape(
    keywords=["关键词"],
    start_date=datetime(2025, 1, 1),
    fetch_content=True  # 启用正文和附件提取
)

# 结果中包含附件信息
for result in results:
    attachments = result.get('attachments', [])
    if attachments:
        print(f"找到 {len(attachments)} 个附件")
```

## 文件结构示例

```
result/
└── 20260131_173028_上海市_科学技术委员会_测试/
    └── 001_关于发布《上海市决策咨询委员会2025年公开招标课题指南》的通知/
        ├── 内容.md
        ├── 附件1：上海市决策咨询委员会2025年公开招标课题指南.doc
        └── 附件2：上海市决策咨询委员会课题申请书.doc
```

## 支持的附件格式

- `.pdf` - PDF文档
- `.doc`, `.docx` - Word文档
- `.xls`, `.xlsx` - Excel表格
- `.ppt`, `.pptx` - PowerPoint演示文稿
- `.zip`, `.rar` - 压缩文件
- `.txt`, `.csv`, `.xml` - 文本文件

## 技术实现

### 核心方法

- `BaseScraper.extract_article_content()`: 提取正文内容和附件
- `BaseScraper._extract_attachments_from_soup()`: 从HTML中提取附件链接
- `BaseScraper.download_attachment()`: 下载附件文件

### 修改的文件

所有爬虫文件都已修改，统一使用以下模式：

```python
content_result = self.extract_article_content(
    url,
    content_selectors=[...],
    extract_attachments=True  # 启用附件提取
)

# 处理返回结果
if isinstance(content_result, dict):
    result["full_content"] = content_result.get("content", "")
    result["attachments"] = content_result.get("attachments", [])
else:
    result["full_content"] = content_result
    result["attachments"] = []
```

## 注意事项

1. **性能**: 附件下载会增加爬取时间，请合理使用
2. **存储**: 附件文件会占用磁盘空间，请定期清理
3. **网络**: 确保网络连接稳定，附件下载失败时会记录错误但继续处理
4. **编码**: 支持中文文件名，自动处理URL编码

## 更新日期

2026-01-31
