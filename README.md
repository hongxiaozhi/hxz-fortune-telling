# HXZ Fortune Telling

这是 `HXZ` 工作区中的运势分析项目。

## 项目结构

- `backend/`：Flask API
- `frontend/`：静态前端页面
- `deploy/site-template/Dockerfile`：容器镜像模板
- `docs/`：路线图、版本计划、变更记录

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

## 文档分层

- `README.md`：如何运行项目
- `PROJECT_CONTEXT.md`：项目现状与技术背景
- `docs/ROADMAP.md`：后续版本规划
- `docs/releases/`：当前版本执行计划
- `docs/CHANGELOG.md`：实际发布记录

## 部署约定

当前仓库结构已经统一到根目录 `docker-compose.yml`。当前产品处于 `v1.4`，这一阶段聚焦历史记录增强、轻量结果对比、历史记录管理、输入回填复用和快捷时间段入口，不引入多设备同步或复杂账户能力。
