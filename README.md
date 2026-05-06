## 内容生成 Agent

这是一个可启动的内容生成组件骨架，后续业务能力会沿着统一流程逐步实现：

```text
content_request -> outline -> content_spec -> elements -> renderer -> exporter
```

当前阶段只提供框架、统一 schema、接口、抽象服务和 stub workflow，不包含真实 LLM、RAG、图片生成、PDF 或 Slide 导出能力。

### Backend

```powershell
uv run uvicorn app.main:app --app-dir backend --reload
uv run pytest backend/tests
```

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
