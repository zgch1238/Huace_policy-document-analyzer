# 服务器部署指南

本文档介绍如何在服务器上部署华测政策文档分析系统。

## 一、服务器环境要求

| 配置项 | 最低要求 | 推荐配置 |
|--------|---------|---------|
| CPU | 2 核 | 4 核及以上 |
| 内存 | 4 GB | 8 GB 及以上 |
| 磁盘 | 20 GB | 50 GB 及以上 |
| 操作系统 | Windows Server / Linux | Windows Server 2019+ 或 Ubuntu 20.04+ |

## 二、准备工作

### 2.1 安装 Python

```bash
# Windows
# 下载地址: https://www.python.org/downloads/
# 安装时勾选 "Add Python to PATH"

# Linux (Ubuntu/Debian)
sudo apt update
sudo apt install python3 python3-pip python3-venv

# 验证安装
python3 --version
```

### 2.2 安装 Git

```bash
# Windows
# 下载地址: https://git-scm.com/download/win

# Linux (Ubuntu/Debian)
sudo apt install git
```

### 2.3 安装 OpenCode

OpenCode 是提供 AI 能力的服务器。

```bash
# 方式一: pip 安装
pip install opencode

# 方式二: 手动安装
# 下载地址: https://github.com/opencode-ai/opencode
```

### 2.4 安装 Node.js (前端构建)

```bash
# Windows
# 下载地址: https://nodejs.org/download/

# Linux (Ubuntu/Debian)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# 验证安装
node --version
npm --version
```

## 三、部署步骤

### 3.1 获取项目代码

```bash
# 克隆项目
git clone <your-repository-url>
cd Huace_policy-document-analyzer

# 如果是压缩包上传，直接解压
# unzip Huace_policy-document-analyzer.zip
```

### 3.2 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
.\venv\Scripts\activate

# Linux
source venv/bin/activate
```

### 3.3 安装后端依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
```

主要依赖包括：
- Flask==3.0.0
- requests==2.31.0
- python-dotenv==1.0.0
- Flask-CORS==4.0.0
- Flask-Limiter==3.5.0
- gunicorn==21.2.0
- python-docx==1.1.2

### 3.4 安装前端依赖并构建

```bash
cd policy-doc-frontend

# 安装依赖
npm install

# 构建生产版本
npm run build
```

构建完成后，`dist/` 目录将包含所有静态文件。

### 3.5 配置环境变量

创建或编辑 `.env` 文件：

```env
# OpenCode 服务器地址
OPENCODE_SERVER_URL=http://127.0.0.1:4096

# Flask 服务端口
FLASK_PORT=5000

# Flask 调试模式 (生产环境设为 false)
FLASK_DEBUG=false

# 服务器地址 (用于生成完整 URL)
SERVER_HOST=0.0.0.0
```

### 3.6 准备数据目录

```bash
# 确保以下目录存在
mkdir -p data
mkdir -p policy_document
mkdir -p analyze_result
mkdir -p policy_document_word
mkdir -p sessions
```

## 四、启动服务

### 4.1 方式一: 开发模式 (仅测试用)

```bash
# 终端 1: 启动 OpenCode
opencode serve --port 4096

# 终端 2: 启动 Flask
cd Huace_policy-document-analyzer
.\venv\Scripts\activate
python app.py
```

访问: http://localhost:5000

### 4.2 方式二: 生产模式 (推荐)

使用 Gunicorn 作为 WSGI 服务器。

#### Windows 生产部署

由于 Gunicorn 不支持 Windows，生产环境建议使用以下方式：

**方式 A: 使用 Waitress**

```bash
pip install waitress

# 创建启动脚本 start_server.py
```

**方式 B: 使用 IIS 托管**

1. 安装 IIS 和 FastCGI
2. 配置 URL 重写规则

#### Linux 生产部署

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动服务 (4 个工作进程)
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# 或使用 systemd 管理服务
```

**创建 systemd 服务文件** `/etc/systemd/system/flask-app.service`:

```ini
[Unit]
Description=Policy Document Analyzer
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/Huace_policy-document-analyzer
Environment="PATH=/path/to/Huace_policy-document-analyzer/venv/bin"
ExecStart=/path/to/Huace_policy-document-analyzer/venv/bin/gunicorn \
    -w 4 \
    -b 127.0.0.1:5000 \
    --capture-output \
    app:app

Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable flask-app
sudo systemctl start flask-app

# 查看状态
sudo systemctl status flask-app

# 查看日志
sudo journalctl -u flask-app -f
```

### 4.3 方式三: 使用 Docker (推荐)

创建 `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 构建前端
WORKDIR /app/policy-doc-frontend
RUN npm install && npm run build
WORKDIR /app

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "app.py"]
```

```bash
# 构建镜像
docker build -t policy-analyzer .

# 运行容器
docker run -d \
    --name policy-analyzer \
    -p 5000:5000 \
    -p 4096:4096 \
    -v $(pwd)/data:/app/data \
    -v $(pwd)/policy_document:/app/policy_document \
    -v $(pwd)/analyze_result:/app/analyze_result \
    policy-analyzer
```

**使用 Docker Compose** (推荐):

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
      - ./policy_document:/app/policy_document
      - ./analyze_result:/app/analyze_result
      - ./policy_document_word:/app/policy_document_word
    environment:
      - OPENCODE_SERVER_URL=http://host.docker.internal:4096
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  opencode:
    image: opencodeai/opencode:latest
    ports:
      - "4096:4096"
    restart: unless-stopped
```

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 五、配置 Nginx 反向代理 (Linux)

生产环境建议使用 Nginx 作为反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;

    # 前端静态文件
    location / {
        root /var/www/policy-analyzer/dist;
        try_files $uri $uri/ /index.html;
    }

    # Flask API
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:5000;
    }
}
```

## 六、配置防火墙

```bash
# Ubuntu UFW
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 5000/tcp
sudo ufw enable

# 或开放特定 IP
sudo ufw allow from 192.168.1.0/24 to any port 5000
```

## 七、数据备份

### 7.1 备份策略

```bash
# 创建备份脚本 backup.sh
#!/bin/bash

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backup/policy-analyzer

mkdir -p $BACKUP_DIR

# 备份数据库
cp data/policy_docs.db $BACKUP_DIR/policy_docs_$DATE.db

# 备份分析结果
tar -czf $BACKUP_DIR/analyze_result_$DATE.tar.gz analyze_result/

# 备份配置
cp .env $BACKUP_DIR/.env_$DATE

# 保留最近 7 天的备份
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

```bash
# 添加定时任务
crontab -e

# 每天凌晨 2 点执行备份
0 2 * * * /path/to/backup.sh
```

## 八、监控与日志

### 8.1 应用日志

日志保存在 `logs/` 目录：

```bash
# 查看最近日志
tail -f logs/flask.log
```

### 8.2 系统监控

```bash
# 使用 pm2 管理进程 (Node.js 方式)
npm install -g pm2
pm2 start app.py --name policy-analyzer
pm2 monit

# 使用 supervisor
sudo apt install supervisor
sudo systemctl enable supervisor
sudo systemctl start supervisor
```

### 8.3 健康检查

```bash
# 检查服务状态
curl http://localhost:5000/health

# 检查 OpenCode 连接
curl http://localhost:4096/health
```

## 九、更新部署

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 更新依赖
.\venv\Scripts\activate
pip install -r requirements.txt

# 3. 重建前端
cd policy-doc-frontend
npm install
npm run build

# 4. 重启服务
# systemd
sudo systemctl restart flask-app

# 或 docker
docker-compose down
docker-compose up -d
```

## 十、故障排查

### 10.1 常见问题

**Q: 无法连接到 OpenCode**

```bash
# 检查 OpenCode 服务
curl http://127.0.0.1:4096/health

# 确认 .env 配置
cat .env
```

**Q: 页面显示 500 错误**

```bash
# 查看 Flask 日志
tail -f logs/flask.log

# 检查权限
chmod -R 755 data/ policy_document/ analyze_result/
```

**Q: 前端资源加载失败**

```bash
# 检查 dist 目录
ls -la policy-doc-frontend/dist/

# 重新构建前端
cd policy-doc-frontend
npm run build
```

### 10.2 日志级别调整

编辑 `.env`:

```env
FLASK_DEBUG=true  # 开发环境开启详细日志
```

或在代码中调整 logging 配置。

## 十一、性能优化

### 11.1 Gunicorn 调优

```bash
# 根据 CPU 核心数调整工作进程
# 公式: 2 * CPU 核心数 + 1

gunicorn -w 9 -b 127.0.0.1:5000 app:app --worker-class sync --max-requests 1000 --timeout 120
```

### 11.2 数据库优化

```bash
# 定期清理数据库
sqlite3 data/policy_docs.db "VACUUM;"
```

## 十二、安全建议

1. **修改默认密钥**: 在 `.env` 中设置 `SECRET_KEY`
2. **启用 HTTPS**: 使用 SSL 证书
3. **限制 API 访问**: 使用防火墙规则
4. **定期更新依赖**: `pip install --upgrade -r requirements.txt`
5. **启用日志审计**: 记录所有管理操作

---

**如有问题，请联系系统管理员**
