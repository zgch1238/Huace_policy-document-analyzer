# 华测导航政策文档分析系统

政策文档 AI 分析助手，支持智能问答、文档管理、资源管理器风格浏览。

## 一、项目介绍

本系统基于 AI 技术，专为华测导航产业应用设计，能够：
- 自动分析政策文档，提取与华测导航产业相关的信息
- 评估政策文档与企业的相关度并打分
- 支持 AI 智能问答，快速获取政策要点
- 高亮显示文档中的关键内容

## 二、系统架构

```
┌─────────────────────────────────────────────────────┐
│                   用户浏览器                         │
│              (访问 http://localhost:5000)            │
└─────────────────────────┬───────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│              Flask Web 应用 (app.py)                 │
│                   端口: 5000                         │
│  - Vue 3 前端界面                                    │
│  - REST API                                          │
│  - 用户认证授权                                       │
└─────────────────────────┬───────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│              OpenCode Server                         │
│                   端口: 4096                         │
│  - AI 能力 (Claude)                                  │
│  - 政策文档分析                                       │
└─────────────────────────────────────────────────────┘
```

## 三、技术栈

### 后端
| 技术 | 用途 |
|------|------|
| **Flask 3.0** | Web 框架 |
| **SQLite** | 数据存储 |
| **OpenCode** | AI 能力提供 (Claude Skill) |
| **Flask-CORS** | 跨域支持 |
| **APScheduler** | 定时任务调度 |

### 前端
| 技术 | 用途 |
|------|------|
| **Vue 3.4** | 前端框架 |
| **Vite 5.0** | 构建工具 |

## 四、项目结构

```
Huace_policy-document-analyzer/
├── backend/                   # Flask 后端
│   ├── api/                   # REST API 端点
│   │   ├── analysis.py       # 分析结果接口
│   │   ├── auth.py           # 认证接口
│   │   ├── crawl.py          # 爬虫接口
│   │   ├── documents.py      # 文档管理接口
│   │   ├── keyword_categories.py # 关键词分类
│   │   └── system.py         # 系统管理接口
│   ├── services/              # 服务层
│   │   ├── file_service.py   # 文件操作服务
│   │   └── session_service.py # 会话服务
│   ├── auth.py               # 认证函数
│   └── database.py            # 数据库操作
├── core/                      # 核心模块
│   ├── analyzer.py           # 政策文档分析器
│   ├── highlight.py          # 高亮文档生成
│   ├── opencode_client.py    # OpenCode API 客户端
│   └── scheduler.py          # 定时任务调度器
├── policy-doc-frontend/       # Vue 前端项目
│   ├── src/
│   │   ├── components/      # Vue 组件
│   │   ├── views/           # 页面视图
│   │   └── utils/api.js     # API 封装
│   └── dist/                 # 构建输出
├── data/                      # 数据存储
│   └── policy_docs.db        # SQLite 数据库
├── policy_document/           # 原始政策文档
├── analyze_result/            # 分析结果 (Markdown)
├── policy_document_word/      # 高亮文档 (Word)
├── docs/                      # 项目文档
├── scrapers/                  # 爬虫模块
├── app.py                     # Flask 主入口
├── requirements.txt           # Python 依赖
└── .env                       # 环境变量配置
```

## 五、快速开始

### 5.1 前置条件

| 软件 | 要求 |
|------|------|
| Python | 3.8+ |
| OpenCode | 最新版 |

### 5.2 启动步骤

**步骤 1: 启动 OpenCode**

```bash
opencode serve --port 4096
```

**步骤 2: 启动 Flask 应用**

```bash
# 激活虚拟环境
.\venv\Scripts\activate

# 启动应用
python app.py
```

**步骤 3: 访问应用**

打开浏览器：`http://localhost:5000`

## 六、功能说明

### 6.1 政策文档管理
- 资源管理器风格浏览
- 文件夹导航（双击进入）
- 文件搜索和筛选
- 文件下载/删除（管理员）

### 6.2 分析结果
- 分析结果/高亮文档切换
- 分数筛选（60/70/80/90分以上）
- 分数颜色标识
  - 绿色: ≥90分
  - 橙色: 80-89分
  - 橙红: 70-79分
  - 红色: <70分
- 查看详细分析内容

### 6.3 AI 问答
- 基于政策文档的智能问答
- 调用 OpenCode Claude 能力
- 会话管理（创建/加载/删除）

### 6.4 手动分析
- 触发政策文档重新分析
- 并行处理多个文档

### 6.5 数据爬虫
- 网页内容抓取
- 关键词分类
- CSV 结果导出

## 七、API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/documents/list` | GET | 资源管理器风格列出文档 |
| `/api/documents` | GET | 获取文档列表（兼容旧接口） |
| `/api/download-documents` | POST | 下载文档 |
| `/api/delete-documents` | POST | 删除文档（管理员） |
| `/api/analysis/list` | GET | 列出分析结果 |
| `/api/analysis-results` | GET | 获取分析结果列表 |
| `/api/highlight-docs` | GET | 获取高亮文档列表 |
| `/api/download-analysis` | POST | 下载分析结果 |
| `/api/delete-analysis` | POST | 删除分析结果（管理员） |
| `/api/analyze-status` | GET | 获取分析状态 |
| `/api/analyze-progress` | GET | 获取分析进度 |
| `/api/trigger-analyze` | POST | 手动触发分析 |
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/crawl` | POST | 执行爬虫任务 |
| `/api/sessions` | GET | 获取会话列表 |
| `/api/sync-data` | POST | 同步数据 |
| `/health` | GET | 健康检查 |
| `/ask` | POST | AI 问答 |

## 八、配置说明

### 8.1 环境变量 (.env)

```env
OPENCODE_SERVER_URL=http://127.0.0.1:4096
FLASK_PORT=5000
FLASK_DEBUG=false
```

### 8.2 数据库初始化

```bash
python core/init_db.py
```

## 九、常见问题

**Q: 提示 "无法连接到 OpenCode 服务器"**

A: 确保 OpenCode 正在运行：`opencode serve --port 4096`

**Q: 页面显示 "连接失败"**

A: 检查 Flask 应用是否运行，确认端口 5000 可用

**Q: 分析功能不可用**

A: 检查 `policy_document` 目录是否存在政策文档

**Q: 分数筛选不生效**

A: 确保文件名格式正确，系统从文件名末尾提取分数（如 `xxx_58.0.md`）

## 十、更新日志

| 版本 | 日期 | 说明 |
|-----|------|------|
| v2.0 | 2026-02-04 | 优化日志输出，修复分数筛选 |
| v1.5 | 2026-02-03 | 添加数据爬虫功能 |
| v1.0 | 2026-01-20 | 初始版本 |

---

**Powered by Claude Code & OpenCode Server**
