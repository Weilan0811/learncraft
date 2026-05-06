## 内容生成 Agent

这是一个可启动的内容生成组件骨架，后续业务能力会沿着统一流程逐步实现：

```text
content_request -> outline -> content_spec -> elements -> renderer -> exporter
```

当前阶段已提供框架、统一 schema、接口、抽象服务、stub workflow、Local 资源存储、基础导出链路，以及可配置的外部 provider service。默认运行仍使用 stub，避免开发和测试时误调用付费 API；切换到真实 provider 后，文本生成使用百炼兼容 OpenAI 接口，图片生成默认使用 APIMart GPT-Image-2，检索使用 `langchain_qdrant` 连接本地 Qdrant 数据目录。

### Backend

```powershell
uv run uvicorn app.main:app --app-dir backend --reload
uv run pytest backend/tests
```

本地配置从根目录 `.env` 读取，可从 `.env.example` 复制后填写。`.env` 已被 `.gitignore` 忽略，API key 不应提交到仓库。

常用 provider 配置：

```env
CONTENT_GENERATOR_PROVIDER_MODE=stub
CONTENT_GENERATOR_TEXT_PROVIDER=bailian
CONTENT_GENERATOR_TEXT_MODEL=qwen3.5-flash
CONTENT_GENERATOR_IMAGE_PROVIDER=apimart
CONTENT_GENERATOR_IMAGE_MODEL=gpt-image-2
CONTENT_GENERATOR_IMAGE_RESOLUTION=1k
CONTENT_GENERATOR_EMBEDDING_PROVIDER=bailian
CONTENT_GENERATOR_EMBEDDING_MODEL=text-embedding-v3
CONTENT_GENERATOR_QDRANT_PATH=storage/qdrant_data
```

将 `CONTENT_GENERATOR_PROVIDER_MODE` 设置为 `real` 后，后端 service factory 会按 provider 配置创建真实服务。默认图片 provider 为 APIMart `gpt-image-2`，会轮询任务结果并把图片转存到 Local storage；百炼图片 provider 仍可通过 `CONTENT_GENERATOR_IMAGE_PROVIDER=bailian` 切换。当前 workflow 仍显式使用 stub 节点，真实 service 已就绪但尚未贯穿完整生成流程。

核心入口：

- `POST /api/content-generation/tasks`
- `GET /api/content-generation/tasks/{task_id}`
- `GET /api/content-generation/tasks/{task_id}/preview`
- `POST /api/content-generation/tasks/{task_id}/export`
- `GET /api/assets/{asset_id}`

### Frontend

```powershell
cd frontend
npm install
npm run dev
npm run build
```

Vite dev server 默认代理 `/api` 到 `http://127.0.0.1:8000`。

### Schema

Pydantic v2 是当前 schema 单一真源。后端 schema 位于 `backend/app/schemas/`，可用下面命令导出 JSON Schema：

```powershell
uv run python backend/scripts/export_json_schema.py
```

### Tests

后端测试默认使用 mock 或 stub，不会调用 APIMart、百炼或真实 Qdrant 服务：

```powershell
uv run pytest backend/tests
```

如在受限 Windows 环境中遇到 pytest 临时目录权限问题，可使用项目虚拟环境直接运行：

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q -p no:cacheprovider
```
