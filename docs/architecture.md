# 内容生成组件骨架说明

本项目采用 `backend/ + frontend/` monorepo 结构。

## 后端边界

- `schemas/` 定义统一 Pydantic v2 schema，是当前契约单一真源。
- `workflows/` 保留 LangGraph 节点边界，当前使用顺序 stub 串起完整流程。
- `services/` 定义 LLM、RAG、图片生成、资源、存储、任务服务接口。
- `renderers/` 按内容类型拆分讲义与 Slide 渲染适配。
- `exporters/` 按导出格式拆分 PDF、Slide JSON、Markdown、资源导出适配。

## 前端边界

- `types/` 手写镜像后端 schema，后续可替换为 JSON Schema/OpenAPI 自动生成。
- `api/` 封装后端内容生成与资源接口。
- `stores/` 管理任务、预览和导出状态。
- `components/renderers/` 保留 Lecture、Slide 以及多模态元素渲染入口。

## 当前 stub 行为

- 创建任务会同步跑完整占位 workflow，并返回 `completed`。
- preview 返回符合 schema 的最小渲染模型。
- export 返回占位文件 URL。
- 真实能力应替换服务和 workflow node 内部实现，不改变 API 契约。
