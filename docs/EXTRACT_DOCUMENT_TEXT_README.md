# 文档文本提取工具使用说明

## 功能说明

`extract_document_text.py` 是一个用于提取Word和PDF文档中文字内容的工具脚本。

## 支持的格式

- **PDF文件** (`.pdf`) - 使用 `pdfplumber` 库提取
- **Word文档** (`.docx`) - 使用 `python-docx` 库提取
- **Word旧格式** (`.doc`) - 使用 `pywin32` (Windows COM接口) 提取

## 安装依赖

```bash
pip install pdfplumber python-docx pywin32
```

或者使用项目的 requirements.txt：

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 直接运行（使用测试文件）

```bash
python extract_document_text.py
```

脚本会自动查找测试文件并提取文本。

### 2. 指定文件路径

```bash
# 提取单个文件
python extract_document_text.py "文件路径.pdf"

# 提取多个文件
python extract_document_text.py "文件1.pdf" "文件2.docx" "文件3.doc"
```

### 3. 保存到文件

```bash
# 保存所有结果到一个文件
python extract_document_text.py "文件1.pdf" "文件2.docx" -o output.txt

# 为每个文件单独保存（文件名.txt）
python extract_document_text.py "文件1.pdf" "文件2.docx" --save-individual
```

## 测试结果

### PDF文件提取

**测试文件**: `上海市2025年度关键技术研发计划"元宇宙"专项项目立项清单.pdf`

**结果**:
- ✅ 成功提取文本
- 文本长度: 1309 字符
- 保存位置: 同目录下的 `.txt` 文件

**提取内容示例**:
```
--- 第 1 页 ---

附件
上海市 2025 年度关键技术研发计划"元宇宙"专项项目立项清单
项目
序号 项目编号 项目名称 承担单位 项目周期
...
```

### Word文件提取

**测试文件**: `1.科学数据资源统计表.doc`

**结果**:
- ✅ 成功提取文本
- 文本长度: 292 字符
- 保存位置: 同目录下的 `.txt` 文件

**提取内容示例**:
```
附件1
科学数据资源统计表
填报单位：
联 络 人：                     职务：
联系方式：
序号
单位名称
数据所属机构
...
```

## 输出格式

提取的文本会保存为UTF-8编码的文本文件，包含：

1. **PDF文件**: 按页面分隔，每页前有标记 `--- 第 X 页 ---`
2. **Word文件**: 包含段落文本和表格内容
3. **表格**: 表格内容以 `|` 分隔

## 注意事项

1. **.doc文件提取**:
   - 在Windows系统上使用COM接口（需要安装pywin32）
   - 需要系统已安装Microsoft Word
   - 如果Word未安装，可以考虑将文件转换为.docx格式

2. **PDF文件提取**:
   - 优先使用 `pdfplumber`（更好的表格提取）
   - 如果未安装，会尝试使用 `PyPDF2`
   - 扫描版PDF（图片）无法提取文本

3. **编码问题**:
   - 所有输出文件使用UTF-8编码
   - 支持中文文件名和路径

## 命令行参数

```
positional arguments:
  files                 要提取的文件路径（支持多个文件）

optional arguments:
  -h, --help            显示帮助信息
  -o OUTPUT, --output OUTPUT
                        输出文件路径（可选，默认输出到控制台）
  --save-individual     为每个文件单独保存文本文件（文件名.txt）
```

## 示例

```bash
# 提取单个PDF文件并保存
python extract_document_text.py "document.pdf" --save-individual

# 提取多个文件并合并到一个文件
python extract_document_text.py "file1.pdf" "file2.docx" -o combined.txt

# 批量提取某个文件夹下的所有PDF和Word文件
python extract_document_text.py result/**/*.pdf result/**/*.docx --save-individual
```

## 错误处理

脚本会处理以下错误情况：

- 文件不存在
- 不支持的文件格式
- 库未安装
- 文件损坏或无法读取

所有错误都会在控制台显示，不会中断整个提取过程。

## 技术实现

- **PDF提取**: `pdfplumber` 或 `PyPDF2`
- **DOCX提取**: `python-docx`
- **DOC提取**: `win32com.client` (Windows COM接口)
