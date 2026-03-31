# HXZ Fortune Telling

这是 `HXZ` 工作区中的运势分析项目。

## 项目结构

- `backend/`: Flask API
- `frontend/`: 静态前端页面
- `deploy/site-template/Dockerfile`: 容器镜像模板
- `docs/`: 路线图、版本计划、变更记录

## 运行方式

当前推荐使用工作区根目录的统一编排，在根目录执行：

```bash
docker compose up -d --build hxz-fortune
```

本地默认访问地址：

- 页面：`http://127.0.0.1:5002`
- 健康检查：`http://127.0.0.1:5002/api/fortune/health`

## 开发入口

- 后端入口：`backend/app.py`
- 测试入口：`backend/tests/test_fortune_api.py`
- 前端入口：`frontend/index.html`

运行测试：

```bash
pytest backend/tests/test_fortune_api.py
```

如果本地未安装 `pytest`，先执行：

```bash
pip install pytest
```

## 文档分层

- `README.md`: 如何运行项目
- `PROJECT_CONTEXT.md`: 项目现状与技术背景
- `docs/ROADMAP.md`: 后续版本规划
- `docs/releases/`: 当前版本执行计划
- `docs/CHANGELOG.md`: 实际发布记录

## 文档规范

- 所有 Markdown 文档统一使用 `UTF-8`
- 行尾统一使用 `LF`
- 不再额外维护旧版本总计划、单独执行说明、线框说明或文档风格说明文件

## 部署约定

当前仓库结构已经统一到根目录 `docker-compose.yml`，不再推荐：

- 在子项目内单独维护启动脚本
- 使用旧的 `systemd + gunicorn` 模板

当前线上部署链路：

- GitHub Actions 工作流：`.github/workflows/deploy.yml`
- 服务器部署目录：`/opt/hxz`
- 服务启动方式：根目录 `docker compose up -d --build hxz-fortune`
- 对外入口：Nginx 反向代理到 `127.0.0.1:5002`

当前产品已进入 `v1.3`，第一批优化聚焦出生地输入、标准 / 进阶分析模式，以及结果页“本次分析依据”摘要，不引入历史对比或复杂账户能力。

如需查看线上问题处理过程，可参考：

[`../ops-notes/FORTUNE_线上故障排查记录_2026-03-30.md`](../ops-notes/FORTUNE_线上故障排查记录_2026-03-30.md)
