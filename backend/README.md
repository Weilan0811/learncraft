# LearnCraft 后端

FastAPI 提供 HTTP API，LangGraph 编排内容生成，Pydantic 定义请求与产物契约，SQLModel 和 Alembic 管理任务与学习记录。

安装及服务商配置见[根 README](../README.md)。从仓库根目录启动：

```powershell
uv run python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

接口文档：<http://127.0.0.1:8000/docs>。

## 模块职责

| 目录 | 职责 |
|---|---|
| `app/api` | 请求、响应、错误状态 |
| `app/schemas` | 请求、任务、内容规格与渲染契约 |
| `app/content_types` | 内容类型注册、生成器和导出能力 |
| `app/workflows` | 标准化、检索、大纲、单元生成、校验与组装 |
| `app/services` | 模型服务、资源生成、任务仓储、知识库适配及学习服务 |
| `app/renderers` | 将规格和章节结果转为前端可用的渲染数据 |
| `app/exporters` | HTML、PDF、Markdown、音频等导出 |
| `app/models`、`alembic` | 数据模型与迁移 |

知识库引擎位于仓库根目录 `knowledge/engine`，可以独立使用；`LocalKBService` 将其适配为后端的检索契约。

## 任务执行

单文档类型直接生成整体规格，多章节类型按大纲并行生成单元。已完成单元立即保存，并通过 SSE（服务端事件流）触发前端刷新。

任务、产物、资源、引用和学习数据分别保存。进程重启时可将遗留运行任务标记为中断，保留已有结果；资源失败可以单独重试。数据库迁移、任务恢复与状态结构见[架构说明](../docs/architecture.md)。

## 主要接口

以下路径前缀为 `/api/content-generation`：

| 接口 | 用途 |
|---|---|
| `POST /tasks` | 创建生成任务 |
| `GET /tasks` | 分页查询历史任务 |
| `GET /tasks/{task_id}` | 查询任务状态 |
| `GET /tasks/{task_id}/preview` | 获取最终预览 |
| `GET /tasks/{task_id}/preview/partial` | 获取部分预览 |
| `GET /tasks/{task_id}/events/stream` | 订阅生成进度 |
| `GET /tasks/{task_id}/failed-resources` | 查询失败资源 |
| `POST /tasks/{task_id}/resources/{resource_id}/retry` | 重试资源 |
| `POST /tasks/{task_id}/export` | 导出任务产物 |

完整字段以 OpenAPI 为准。平台请求头、学习会话、摘要和复习接口见[平台契约](../docs/reference/platform-contract.md)及[学习记录说明](../docs/design/learning-loop.md)。

## 知识库与任务材料

检索默认关闭。设置 `CONTENT_GENERATOR_KB_PROVIDER=local` 后启用自托管检索。初始化失败、检索失败和空结果使用明确状态，不提供虚构引用。

| `kb_mode` | 检索范围 |
|---|---|
| `platform` | 本地平台知识库 |
| `materials_only` | 只检索 `attachments` 中的本次材料 |
| `fused` | 两者独立检索后融合排名 |

附件格式为 `[{"filename":"材料.md","content":"正文"}]`，最多 10 份，每份最多 200,000 个字符。仅附件模式无需平台语料；复习任务继续使用原附件和模式。`knowledge_base_ids` 保留在请求结构中，当前不承担按库授权。

配置、示例和索引维护见[知识库使用说明](../knowledge/README.md)，职责与设计依据见[知识库设计](../docs/design/knowledge-base-design.md)。

## 开发验证

```powershell
uv run python -m pytest backend/tests/test_kb_runtime.py backend/tests/test_learning_persistence.py backend/tests/test_learning_summary.py
```

这些检查使用实际关键词检索和隔离的 SQLite。真实模型调用需要相应配置；开发检查不等于已验证所有服务商或全部内容类型的真实生成质量。
