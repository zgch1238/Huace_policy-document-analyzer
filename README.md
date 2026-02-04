<<<<<<< HEAD
# 华测导航政策文档分析系统

政策文档分析助手，支持 AI 问答、文档管理、资源管理器风格浏览。

## 一、系统架构

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
│  - Vue 前端界面                                      │
│  - REST API                                          │
│  - 认证授权                                          │
└─────────────────────────┬───────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│              OpenCode Server                         │
│                   端口: 4096                         │
│  - AI 能力                                          │
│  - Claude Skill 执行                                │
└─────────────────────────┬───────────────────────────┘
```

## 二、项目结构

```
AI Skill分析/
├── 根目录（入口和配置）
│   ├── app.py              # Flask 主入口
│   ├── init_db.py          # 数据库初始化工具
│   ├── pyproject.toml      # 项目依赖配置
│   ├── .env                # 环境变量
│   └── README.md           # 本文档
│
├── core/                   # 核心服务模块
│   ├── analyzer.py         # 政策文档分析器
│   ├── opencode_client.py  # OpenCode API 客户端
│   ├── scheduler.py        # 定时任务调度器
│   └── highlight.py        # 高亮文档生成
│
├── backend/                # 后端 API
│   ├── api/                # REST API 端点
│   │   ├── documents.py    # 文档管理接口
│   │   ├── analysis.py     # 分析结果接口
│   │   ├── auth.py         # 认证会话接口
│   │   └── system.py       # 系统管理接口
│   ├── services/           # 服务层
│   │   ├── file_service.py # 文件操作服务
│   │   └── session_service.py
│   ├── auth.py             # 认证函数
│   └── database.py         # 数据库操作
│
├── data/                   # 数据文件
│   ├── analyze_status.json # 分析状态记录
│   └── users.json          # 用户数据
│
├── venv/                   # Python 虚拟环境
│
├── policy-doc-frontend/    # Vue 前端项目
├── policy_document/        # 政策文档 (*.md)
├── analyze_result/         # 分析结果 (*.docx)
└── policy_document_word/   # 高亮文档 (*.docx)
```

## 三、快速开始

### 3.1 前置条件

| 软件 | 要求 |
|------|------|
| Python | 3.8+ |
| OpenCode | 最新版 |

### 3.2 启动步骤

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

## 四、功能说明

### 4.1 政策文档管理
- 资源管理器风格浏览
- 文件夹导航（双击进入）
- 文件搜索和筛选
- 文件下载/删除（管理员）

### 4.2 分析结果
- 分析结果/高亮文档切换
- 分数筛选（60/70/80/90分以上）
- 分数颜色标识（绿/橙/红）
- 查看详细分析内容

### 4.3 AI 问答
- 基于政策文档的智能问答
- 调用 OpenCode Claude 能力

### 4.4 手动分析
- 触发政策文档重新分析
- 并行处理多个文档

## 五、API 接口

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
| `/api/trigger-analyze` | POST | 手动触发分析 |
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/sessions` | GET | 获取会话列表 |
| `/api/sync-data` | POST | 同步数据 |
| `/health` | GET | 健康检查 |
| `/ask` | POST | AI 问答 |

## 六、配置说明

### 6.1 环境变量 (.env)

```env
OPENCODE_SERVER_URL=http://127.0.0.1:4096
FLASK_PORT=5000
FLASK_DEBUG=false
```

### 6.2 数据库初始化

```bash
python init_db.py
```

## 七、常见问题

**Q: 提示 "无法连接到 OpenCode 服务器"**

A: 确保 OpenCode 正在运行：`opencode serve --port 4096`

**Q: 页面显示 "连接失败"**

A: 检查 Flask 应用是否运行，确认端口 5000 可用

**Q: 分析功能不可用**

A: 检查 policy_document 目录是否存在政策文档

## 八、更新日志

| 版本 | 日期 | 说明 |
|-----|------|------|
| v2.0 | 2026-02-03 | 重构后端结构，使用 Flask Blueprint |
| v1.0 | 2026-01-20 | 初始版本 |

---

**Powered by Claude Code & OpenCode Server**
=======
# Huace_policy-document-analyzer
>>>>>>> 5a6cace1e82b97fc67e9945691ea81d789bf434e
