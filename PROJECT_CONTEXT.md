# XiaozhiBlog 项目上下文文档

> 用途：新对话 context 快速了解本项目背景、技术架构、当前状态和下一步计划
> 最后更新：2026-03-28，当前版本 v1.1.0

---

## 一、产品定位

**这是什么**：一个个人技术博客，作者是 h_xiaozhi，用于学习笔记归档和个人感悟输出。

**面向用户**：
- 作者（博主）：写文章、管理文章、删除评论
- 陌生访客：浏览文章、提交评论（无需注册，可匿名）

**设计风格目标**：iOS 风格界面，简洁、圆角、柔和阴影、流畅动效，避免信息堆砌。

**线上地址**：`https://blog.kiosk.pub`（暂用，待 ICP 备案域名到位后迁移至 `.cn` 域名）

---

## 二、技术架构

### 总体结构

```
前端（Vue 3 SPA）  ←→  Nginx  ←→  Gunicorn  ←→  Flask 后端  ←→  SQLite
```

### 前端

| 技术 | 说明 |
|------|------|
| Vue 3 | CDN 全局构建版（`vue.global.prod.js`），无需构建工具 |
| Axios | HTTP 请求库，通过 CDN 引入 |
| Marked.js | Markdown 渲染（文章详情页） |
| 单文件 SPA | `frontend/index.html` + `frontend/app.js` + `frontend/style.css` |

前端路由：纯前端路由（无 Vue Router），通过 `currentView` 变量切换页面组件。

认证：登录后将 `hx_token`（JWT）和 `hx_user`（用户名）存入 `localStorage`，后续请求通过 `Authorization: Bearer <token>` header 传递。

### 后端

| 技术 | 说明 |
|------|------|
| Python 3.8+ | 语言版本要求 |
| Flask | Web 框架 |
| Flask-SQLAlchemy | ORM，数据库访问 |
| Flask-JWT-Extended | JWT 认证，token 有效期 7 天 |
| Flask-CORS | 跨域配置，支持携带凭证 |
| bcrypt | 密码哈希（存储和校验） |
| python-markdown | Markdown → HTML 转换（后端渲染） |

所有后端代码在 `backend/` 目录下，入口为 `backend/app.py`。

### 数据库

- SQLite，文件路径：`backend/blog.db`
- 无 ORM 迁移工具，DDL 变更手动执行

**Post 表字段**：`id, title, content, category, tags(逗号分隔字符串), view_count, is_pinned, created_at, updated_at`

**Comment 表字段**：`id, post_id, author, content, created_at`

### 部署环境

| 组件 | 配置 |
|------|------|
| 操作系统 | Ubuntu 24.04 |
| Web 服务器 | Nginx，配置文件：`deploy/nginx-blog.kiosk.pub.conf` |
| 应用服务器 | Gunicorn，2 workers，监听 `127.0.0.1:8001` |
| 进程管理 | systemd，服务名：`hxz-blog`，配置：`deploy/hxz-blog.service` |
| SSL | Let's Encrypt，由 certbot 自动管理 |
| 项目路径 | `/opt/hxz-blog` |
| Python 虚拟环境 | `/opt/hxz-blog/backend/venv` |
| 日志 | `/var/log/hxz-blog/`（access.log、error.log） |

### 安全机制（v1.1.0 现状）

- **密码**：bcrypt 哈希，通过环境变量 `ADMIN_PASSWORD_HASH` 注入到 systemd service
- **JWT 密钥**：不硬编码，通过环境变量 `JWT_SECRET_KEY` 注入，`setup.sh` 自动生成
- **HTTPS**：全站强制 HTTPS，由 Nginx + certbot 保障
- **评论**：完全开放（陌生人可提交），限流尚未实现（v1.2 计划）

---

## 三、API 接口清单

### 认证
| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST | `/api/auth/login` | 公开 | 登录，返回 JWT token |

### 文章
| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/posts` | 公开 | 文章列表，支持 `query/tag/category/page/per_page` 参数 |
| GET | `/api/posts/<id>` | 公开 | 文章详情，每次访问 +1 阅读量，返回 HTML 渲染内容 |
| POST | `/api/posts` | JWT | 新建文章 |
| PUT | `/api/posts/<id>` | JWT | 更新文章 |
| DELETE | `/api/posts/<id>` | JWT | 删除文章（级联删除评论） |

### 评论
| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/posts/<id>/comments` | 公开 | 获取评论列表（按时间倒序） |
| POST | `/api/posts/<id>/comments` | 公开 | 提交评论（`author` 可为空，默认"匿名"） |
| DELETE | `/api/posts/<id>/comments/<cid>` | JWT | 删除评论 |

---

## 四、文件结构

```
XiaozhiBlog/
├── backend/
│   ├── app.py          # Flask 主程序，所有路由
│   ├── models.py       # SQLAlchemy 模型（Post、Comment）
│   ├── init_db.py      # 数据库初始化脚本
│   ├── check_db.py     # 数据库状态检查工具
│   ├── requirements.txt
│   └── blog.db         # SQLite 数据库（不入 git）
├── frontend/
│   ├── index.html      # 单页应用入口
│   ├── app.js          # Vue 3 应用逻辑（所有页面组件）
│   └── style.css       # 全局样式
├── deploy/
│   ├── nginx-blog.kiosk.pub.conf  # Nginx 站点配置
│   ├── hxz-blog.service           # systemd 服务配置（含环境变量占位符）
│   ├── setup.sh                   # 首次部署脚本（生成密钥、安装依赖、启动服务）
│   └── update.sh                  # 增量更新脚本（git pull + pip install + 重启）
├── IMPLEMENTATION_PLAN.md  # 版本规划和验收清单（主要规划文档）
├── PROJECT_CONTEXT.md      # 本文档
└── README.md
```

---

## 五、版本规划概览

**版本号规则**：`v主版本.功能版本.补丁版本`，第三位仅用于线上 bug 修复，不在计划中预排。

| 版本 | 目标 | 状态 |
|------|------|------|
| v1.1 | 安全上线版（bcrypt + JWT 隔离 + 评论删除） | ✅ 已验收，tag v1.1.0 已打 |
| v1.2 | 防刷与排序（Flask-Limiter + 排序穿通） | ⏳ 未开始 |
| v1.3 | 体验优化（加载更多分页 + 评论展开式输入 + 移动端） | ⏳ 未开始 |
| v1.4 | UI 进阶（编辑器双栏 + 移动端 320/375/414 深度适配） | ⏳ 未开始 |
| v1.5 | UI 收口（统一 loading/成功/失败反馈 + 文案一致性） | ⏳ 未开始 |
| v1.6 | 文章管理（草稿/发布/归档状态，可选） | ⏳ 未开始 |
| v1.7 | 图片上传（Markdown 编辑器内嵌，可选） | ⏳ 未开始 |

详细任务拆解和验收清单见 `IMPLEMENTATION_PLAN.md`。

---

## 六、开发工作流

### 本地开发
```bash
# 后端
cd backend && python -m venv venv && venv\Scripts\activate  # Windows
pip install -r requirements.txt
python app.py  # http://localhost:5000

# 前端（另一个终端）
cd frontend && python -m http.server 8080  # http://localhost:8080
```

### 发布流程
1. 本地开发 + 验收 → `git commit`
2. 全部功能通过 → `git tag -a v1.X.0 -m "release: ..."` → `git push origin main && git push origin v1.X.0`
3. 服务器执行：`bash /opt/hxz-blog/deploy/update.sh`

### 代理配置（中国大陆推送 GitHub）
```powershell
git config --global http.proxy http://127.0.0.1:7897  # 根据实际端口调整
git config --global https.proxy http://127.0.0.1:7897
```

---

## 七、已知约束与决策记录

| 决策 | 内容 |
|------|------|
| 域名 | 暂用 `blog.kiosk.pub`，待 ICP 备案新域名到位后迁移 |
| 评论限流强度 | 同一 IP 每分钟 5 条、每小时 100 条（v1.2 实现） |
| 前端框架 | Vue 3 CDN，不引入构建工具（保持低复杂度） |
| 数据库 | SQLite，不考虑迁移到 PostgreSQL，除非有明确性能瓶颈 |
| 单管理员 | 只有一个博主账号，不做多用户系统 |
| 评论开放 | 陌生人可直接评论，无需注册，仅靠限流防刷 |
| JWT 有效期 | 7 天，避免频繁重新登录打断写作流 |
