# aihub-web-vue

GICI 助手 - GNSS/INS 组合导航专家 (Vue 3 + Vite)

面向 GICI-lib 的 AI 知识库

前端基于 Vue3.js+Vite 实现，后端基于 OpenCode 实现

![](./assets/demo.png)

## 部署说明

### 环境准备
- Node.js (建议 v18+)
- npm 或 yarn

### 快速开始
1. **安装依赖**
   ```sh
   npm install
   ```

2. **本地开发**
   ```sh
   npm run dev
   ```

3. **生产构建**
   ```sh
   npm run build
   ```
   构建完成后，静态文件将生成在 `dist` 目录中。

## 环境变量设置

本项目使用 Vite 的环境变量管理机制。你可以通过创建 `.env` 文件来配置系统。

### 配置文件
在项目根目录下创建以下文件（根据需要）：
- `.env`                # 所有环境生效
- `.env.local`          # 本地覆盖，不进入版本控制
- `.env.development`    # 仅开发模式生效
- `.env.production`     # 仅生产模式生效

### 可用变量
| 变量名 | 说明 | 默认值 |
| :--- | :--- | :--- |
| `VITE_PORT` | 开发服务器端口 | `5173` |
| `VITE_HOST` | 开发服务器主机地址 | `127.0.0.1` |
| `VITE_API_BASE_URL` | 后端 API 代理地址 | `http://127.0.0.1:5000` |

### 示例 `.env.local`
```env
VITE_PORT=8080
VITE_API_BASE_URL=https://api.example.com
```

## 技术架构
- **前端框架**: Vue 3 (Composition API)
- **构建工具**: Vite
- **图标库**: Font Awesome 6 (本地化部署)
- **字体**: 本地化部署 (Open Sans & Poppins)

## 项目结构
- `src/components`: UI 组件
- `public/fonts`: 本地化字体资源
- `public/fontawesome`: 本地化 Font Awesome 资源
- `index.html`: 入口 HTML

## 离线支持
本项目所有静态资源（字体、图标等）均已本地化，支持在无外网环境下部署和使用。
