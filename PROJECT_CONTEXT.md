# Project Context

最后更新：2026-03-31

## 项目定位

- 这是一个面向普通用户的运势分析网站
- 目标用户是希望快速获得简明建议的普通用户
- 当前阶段是 `v1.x`，优先保证输入到结果的主链路稳定、易懂、可执行

## 当前技术结构

- 前端：静态页面 + Vue 3 轻量交互
- 后端：Flask API
- 数据层：当前以轻量本地结构和结果对象返回为主
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
  - `analysis_context`
  - `mode_hint`

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
- `.github/workflows/deploy.yml`

## 当前约束

- 当前仍以 MVP 和可解释结果为主
- 暂不追求专业深度推演系统
- 暂不引入复杂账户体系
- 结果表达需要持续控制术语密度
- 页面表达遵循“先结论后细节、先整体后分段”的顺序

## 近期重点

- `v1.2` 已完成：结果页阅读模式、风险提示、页面版本标识
- 当前正在推进：`v1.3` 输入精度增强与结果差异提示

## v1.3 当前进展

- 已建立 `docs/releases/v1.3.md`
- 已新增出生地输入字段
- 已新增标准 / 进阶分析模式
- 已在结果中返回 `analysis_context` 与 `mode_hint`
- 已在结果页新增“本次分析依据”摘要

## 当前部署现状

- 已存在项目内 GitHub Actions 部署工作流：`.github/workflows/deploy.yml`
- 线上部署目录为 `/opt/hxz`
- `fortune.kiosk.pub` 已验证通过 Nginx 到 `127.0.0.1:5002` 的健康检查与路由访问
