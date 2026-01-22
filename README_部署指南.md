# 华测导航政策文档分析助手 - 部署指南

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
│  - 前后端界面                                        │
│  - 消息转发                                          │
│  - 错误处理                                          │
└─────────────────────────┬───────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│              OpenCode Server                         │
│                   端口: 4096                         │
│  - AI 能力                                          │
│  - Claude Skill 执行                                │
│  - 工具调用                                         │
└─────────────────────────┬───────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│              policy_document/ 目录                            │
│  - 政策文档 (*.md)                                  │
│  - 分析结果 (*_分析结果.md)                         │
└─────────────────────────────────────────────────────┘
```

## 二、前置条件

### 2.1 必需软件

| 软件 | 版本要求 | 说明 |
|------|---------|------|
| Python | 3.8+ | 编程语言环境 |
| OpenCode | 最新版 | Claude Code 终端 |

### 2.2 Python 依赖

```bash
pip install -r requirements.txt
```

主要依赖：
- Flask==3.0.0 - Web 框架
- requests==2.31.0 - HTTP 请求
- python-dotenv==1.0.0 - 环境变量

## 三、安装步骤

### 步骤 1: 安装 Python 依赖

```bash
cd C:\Users\admin\Desktop\AI快速工作流\AI Skill分析
pip install -r requirements.txt
```

### 步骤 2: 启动 OpenCode

在新终端中运行：

```bash
opencode serve --port 4096
```

### 步骤 3: 启动 Web 应用

#### 方式 A: 使用启动脚本（推荐）

```bash
start.bat
```

#### 方式 B: 手动启动

```bash
python app.py
```

### 步骤 4: 访问应用

打开浏览器，访问：`http://localhost:5000`

## 四、使用方法

### 4.1 基础对话

在输入框中输入问题，按 Enter 或点击发送按钮。

**示例问题**：
```
分析 policy_document 目录中的所有政策文档
分析 document_1.md
帮我找精准农业相关的政策
为北斗芯片项目提取政策支撑
```

### 4.2 预期结果

1. 系统会调用 `policy-search` Skill
2. 读取 policy_document 目录中的政策文档
3. 执行四步分析流程
4. 生成分析结果
5. 保存到 `policy_document/*_分析结果.md`

## 五、文件说明

### 5.1 目录结构

```
AI Skill分析/
├── app.py                    # Flask 后端主文件
├── requirements.txt          # Python 依赖
├── .env                      # 环境变量配置
├── start.bat                 # Windows 启动脚本
│
├── templates/
│   └── index.html            # 前端页面
│
├── static/
│   ├── css/
│   │   └── style.css         # 样式文件
│   └── js/
│       └── main.js           # 前端交互逻辑
│
├── .claude/
│   └── skills/
│       └── policy-search.md  # Claude Skill
│
└── policy_document/
    ├── document_1.md         # 政策文档
    ├── document_1_分析结果.md # 分析结果
    └── ...
```

### 5.2 配置文件说明

**.env 文件**：
```env
OPENCODE_SERVER_URL=http://127.0.0.1:4096  # OpenCode 地址
FLASK_PORT=5000                            # Web 端口
FLASK_DEBUG=False                          # 调试模式
```

## 六、常见问题

### Q1: 提示 "无法连接到 OpenCode 服务器"

**原因**：OpenCode 服务未运行

**解决**：
1. 打开新终端
2. 运行 `opencode serve --port 4096`
3. 确认显示 "Server running on http://127.0.0.1:4096"

### Q2: 页面显示 "连接失败"

**原因**：Flask 应用未运行或端口被占用

**解决**：
1. 确认 Flask 在运行：`python app.py`
2. 尝试更换端口：修改 .env 中的 `FLASK_PORT`
3. 检查端口是否被占用：`netstat -ano | findstr :5000`

### Q3: 依赖安装失败

**原因**：Python 环境问题

**解决**：
1. 确认 Python 已安装：`python --version`
2. 升级 pip：`pip install --upgrade pip`
3. 单独安装依赖：`pip install Flask requests python-dotenv`

### Q4: 分析结果没有保存

**原因**：Skill 执行异常

**解决**：
1. 检查 policy_document 目录是否存在
2. 检查文档格式是否正确
3. 查看控制台日志

## 七、开发说明

### 7.1 修改前端

- 页面结构：`templates/index.html`
- 样式文件：`static/css/style.css`
- 交互逻辑：`static/js/main.js`

修改后刷新浏览器即可看到效果。

### 7.2 修改后端

- 主文件：`app.py`
- 配置：`.env`

修改后需要重启 Flask 应用。

### 7.3 修改 Skill

- 文件：`.claude/skills/policy-search.md`

修改后立即生效。

## 八、生产部署（可选）

### 8.1 使用 Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 8.2 使用 Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### 8.3 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 九、技术支持

如有问题，请检查：
1. OpenCode 是否正常运行
2. 端口 4096 和 5000 是否可用
3. Python 依赖是否安装完整
4. 日志输出中的错误信息

## 十、更新日志

| 版本 | 日期 | 更新内容 |
|-----|------|---------|
| v1.0 | 2026-01-20 | 初始版本，基础功能完成 |

---

**Powered by Claude Code & OpenCode Server**
