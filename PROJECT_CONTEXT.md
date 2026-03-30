# Project Context

最后更新：2026-03-30

## 项目定位

- 这是一个面向普通用户的运势分析网站
- 目标用户是希望快速获得简明建议的普通用户
- 当前阶段是 `v1.x`，优先保证输入到结果的主链路稳定、易懂、可执行

## 当前技术结构

- 前端：静态页面 + 轻量交互脚本
- 后端：Flask API
- 数据库：当前以轻量本地数据和结果结构为主
- 部署方式：根目录统一 `docker compose` 编排，线上由 Nginx 反向代理到容器端口
- 核心接口：
  - `POST /api/fortune/analyze`
  - `GET /api/fortune/health`
- 当前结果对象核心结构：
  - `bazi_summary`
  - `wuxing_score`
  - `overall_advice`
  - `segments`
  - `upgrade_hint`

## 当前运行方式

- 本地启动：在工作区根目录执行 `docker compose up -d --build hxz-fortune`
- 本地访问：`http://127.0.0.1:5002`
- 健康检查：`http://127.0.0.1:5002/api/fortune/health`
- 根目录统一编排入口：`../docker-compose.yml`

## 关键目录

- `backend/`
- `frontend/`
- `deploy/site-template/Dockerfile`
- `docs/`

## 当前约束

- 当前仍以 MVP 和可解释结果为主
- 暂不追求专业深度推演系统
- 暂不引入复杂账户体系
- 结果表达需要持续控制术语密度
- 页面表达遵循“先结论后细节、先整体后分段”的顺序

## 近期重点

- 当前版本重点：`v1.1` 主链路、时间段建议、输入精度说明
- 下一个版本重点：`v1.2` 结果表达优化与阅读模式优化
