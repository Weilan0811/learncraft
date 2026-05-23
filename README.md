## 内容生成 Agent

这是一个可启动的内容生成组件骨架，后续业务能力会沿着统一流程逐步实现：

```text
content_request -> outline -> content_spec -> elements -> renderer -> exporter
```

当前阶段已提供框架、统一 schema、接口、抽象服务、stub workflow、Local 资源存储、基础导出链路，以及可配置的外部 provider service。默认运行仍使用 stub，避免开发和测试时误调用付费 API；切换到真实 provider 后，文本生成使用百炼兼容 OpenAI 接口，图片生成默认使用 APIMart GPT-Image-2，检索调用外部知识库 HTTP API。

---
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
CONTENT_GENERATOR_KB_API_BASE_URL=
CONTENT_GENERATOR_KB_API_KEY=
CONTENT_GENERATOR_KB_RETRIEVAL_TOP_K=5
```

---
### 检索服务配置

真实检索依赖外部知识库 HTTP API，需要配置以下环境变量：

```env
CONTENT_GENERATOR_KB_API_BASE_URL=https://your-kb-api.example.com
CONTENT_GENERATOR_KB_API_KEY=your-api-key
CONTENT_GENERATOR_KB_RETRIEVAL_TOP_K=5
CONTENT_GENERATOR_KB_MAX_CHARS_PER_ITEM=8000
```

将 `CONTENT_GENERATOR_PROVIDER_MODE` 设置为 `real` 后，后端 service factory 会按 provider 配置创建真实服务。默认图片 provider 为 APIMart `gpt-image-2`，会轮询任务结果并把图片转存到 Local storage；百炼图片 provider 仍可通过 `CONTENT_GENERATOR_IMAGE_PROVIDER=bailian` 切换。当前 workflow 仍显式使用 stub 节点，真实 service 已就绪但尚未贯穿完整生成流程。

核心入口：

- `POST /api/content-generation/tasks`
- `GET /api/content-generation/tasks/{task_id}`
- `GET /api/content-generation/tasks/{task_id}/preview`
- `POST /api/content-generation/tasks/{task_id}/export`
- `GET /api/assets/{asset_id}`

---
### Frontend

```powershell
cd frontend
npm install
npm run dev
npm run build
```

Vite dev server 默认代理 `/api` 到 `http://127.0.0.1:8000`。

---
### Schema

Pydantic v2 是当前 schema 单一真源。后端 schema 位于 `backend/app/schemas/`，可用下面命令导出 JSON Schema：

```powershell
uv run python backend/scripts/export_json_schema.py
```

---
### Tests

后端测试默认使用 mock 或 stub，不会调用 APIMart、百炼或真实 Qdrant 服务：

```powershell
uv run pytest backend/tests
```

如在受限 Windows 环境中遇到 pytest 临时目录权限问题，可使用项目虚拟环境直接运行：

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q -p no:cacheprovider
```

---
### Workflow debug test

`backend/tests/test_workflow_debug.py` 是手动真实生成调试测试，不属于默认稳定测试入口。运行前请确认：

- `.env` 已配置真实 provider 所需 API key，并设置 `CONTENT_GENERATOR_PROVIDER_MODE=real`。
- 已配置外部知识库 API（`CONTENT_GENERATOR_KB_API_BASE_URL`）。
- 真实图片生成可能产生外部 API 调用和费用。

运行 lecture 全流程 debug：

```powershell
$env:CONTENT_GENERATOR_PROVIDER_MODE="real"
.\.venv\Scripts\python.exe -m pytest backend/tests/test_workflow_debug.py::test_lecture -q -s -p no:cacheprovider
```

运行 slide deck 全流程 debug：

```powershell
$env:CONTENT_GENERATOR_PROVIDER_MODE="real"
.\.venv\Scripts\python.exe -m pytest backend/tests/test_workflow_debug.py::test_slides -q -s -p no:cacheprovider
```

运行全部 workflow debug：

```powershell
$env:CONTENT_GENERATOR_PROVIDER_MODE="real"
.\.venv\Scripts\python.exe -m pytest backend/tests/test_workflow_debug.py -q -s -p no:cacheprovider
```

测试会在 stdout 显式打印 workflow 每一步输出，并把调试结果保存到 `storage/debug_workflow/<request_id>/`：

- `steps/NN_<node>.json`：每个 LangGraph 节点的 update 输出。
- `trace.json`：按顺序汇总的节点输出。
- `final_state.json`、`content_spec.json`、`render_model.json`、`elements.json`：最终工作流产物。
- `assets/`、`generated_assets.json`：真实生成资产及 manifest。

---
### TODO

现在存在的问题：前端没有办法持久化记录答案，答案可以随意修改，和我的设计想法有冲突，需要调整，但目前优先级不高。
