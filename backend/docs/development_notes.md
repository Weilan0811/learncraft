# LearnCraft 后端开发说明

本文记录当前运行方式和开发入口。安装、供应商密钥、图片、语音与知识库的完整步骤见[配置指南](../../docs/configuration.md)。以下命令从仓库根目录执行。

## 1. 本地开发模式

正式使用在 `.env` 中设置 `CONTENT_GENERATOR_PROVIDER_MODE=real`，并配置文本服务。`stub` 是开发占位模式，不调用真实生成服务，不能用于展示真实生成质量。检索是否启用由 `CONTENT_GENERATOR_KB_PROVIDER` 单独控制；默认检索关闭，不提供模拟引用。

请求中的 `generation_options.allow_fallback` 可覆盖全局设置。允许替代内容时，生成或渲染失败可能返回预设内容；质量评估应关闭该选项。

## 2. 真实服务模式

供应商、模型名与默认值见根目录 `.env.example` 和 `backend/app/core/config.py`。文本支持百炼和 DeepSeek，图片支持 APIMart 和百炼，语音使用百炼。当前默认语音模型是 `qwen3-tts-flash`；分章生成、图片生成和语音生成的默认并发分别为 3、3、4。

设置 `CONTENT_GENERATOR_KB_PROVIDER=local` 启用本地检索适配器。大纲前由文本模型规划查询，章节直接执行大纲提供的查询；材料范围由 `kb_mode` 与 `attachments` 决定。`knowledge_base_ids` 是保留关联字段，不承担分库授权。详见[知识查询流程](../../docs/design/retrieval-workflow.md)。

## 3. 数据库配置

推荐本地运行配置：

```dotenv
CONTENT_GENERATOR_DATABASE_URL=sqlite:///storage/tasks.db
```

相对 SQLite 路径与资源路径以仓库根目录为基准。SQLite 启动通过 Alembic 执行迁移，已有无版本记录的兼容库按实际结构登记后升级。当前迁移至 `20260702_0008`。没有显式数据库 URL 时，设置类会根据 `DB_*` 字段组成 MySQL 地址；根目录示例文件明确选择 SQLite。

| 数据 | 保存位置 |
| --- | --- |
| 任务请求、状态、进度 | `content_generation_task` |
| 大纲、单元规格、渲染、检索计划与执行记录 | `content_generation_artifact` |
| 引用正文缓存 | `knowledge_chunk_cache` |
| 任务与缓存片段的来源关系 | `content_generation_reference` |
| 图片与语音资源的状态、错误和重试次数 | `content_generation_asset` |
| 学习会话与作答事件 | `interactive_learning_session`、`interactive_learning_event` |

`0006` 迁移重建任务、产物、引用和资产结构，并移除独立事件与指标表。任务事件由 `TaskEventStore` 保存为日志目录下的 JSON 文件，重启后可以读取；指标兼容接口当前返回空列表。调用用量可从检索记录、大纲等任务产物及调试记录检查。资源状态由资产表与渲染结果保存，文件元数据另保存在本地 manifest。

非 SQLite 部署需先准备相应数据库与迁移；手动升级时执行：

```powershell
Set-Location backend
uv run alembic upgrade head
```

## 4. 资源存储

| 路径 | 用途 |
| --- | --- |
| `storage/files/` | 图片、音频、HTML 与其他生成文件 |
| `storage/manifest.json` | 文件元数据与资源地址 |
| `storage/debug_workflow/` | 工作流调试快照 |
| `storage/logs/` | 应用日志 |

生成文件通过 `LocalStorageService` 保存，通过 `/api/assets/{asset_id}` 和 `/api/assets/{asset_id}/download` 读取。manifest 写入使用进程内锁；当前本地部署按单进程使用。备份应同时保存数据库、manifest 和关联文件。

## 5. 测试

不调用模型的检索与学习记录检查：

```powershell
uv run python -m pytest backend/tests/test_kb_runtime.py backend/tests/test_learning_persistence.py backend/tests/test_learning_summary.py backend/tests/test_final_rag_contract.py backend/tests/test_explicit_retrieval_queries.py
```

其他测试与开发脚本可能使用当前模型配置并产生调用费用，执行前查看对应文件。有关交互讲义和播客的专项入口见各自专题文档。

## 6. Schema 导出

`backend/scripts/export_json_schema.py` 将显式登记的模型导出到 `backend/schema_exports/`。当前列表没有覆盖全部交互讲义与学习接口模型；完整 HTTP 请求和响应以运行服务的 OpenAPI 为准，不能把已有导出目录当作完整契约。

## 7. Prompt 开发约定

提示位于 `backend/app/prompts/`。大纲负责内容和查询规划，单元规格负责教学顺序与互动题目，讲解渲染只生成受限 HTML/CSS。结构化输出绑定 Pydantic 模型；约束、引用要求和修复方式应与当前校验器一致。

## 8. Validator 开发约定

校验器检查结构、章节顺序、来源引用、所需资源及渲染约束。交互讲义另检查 HTML、CSS 作用域和清单对应。修复有明确次数上限；无法通过时，按请求设置使用替代内容或结束任务。结构通过不等于知识内容准确。

## 9. Renderer 开发约定

普通渲染器转换规格与展示数据。交互讲义的 `ExplanationHtmlComposer` 调用模型生成讲解 HTML/CSS，`InteractionTemplateRenderer` 生成四种互动控件，`UnitHtmlAssembler` 按教学顺序组装。播客渲染包含语音生成和音频合成。详见[生成工作流](content_generation_workflow.md)。

## 10. 导出

交互讲义 HTML 导出要求有效的 `export_options.session_id`，保留讲解、学生回答、参考答案与引用，移除在线互动控件。当前 profile 仅声明 `html`。`docs/examples/` 中可点击练习的静态展示副本另带轻量运行脚本，与正式静态讲义导出的功能范围分别说明。

## 11. Learning Session 开发约定

`LearningService` 使用 `SQLModelLearningRepository` 保存会话与事件，复用任务仓储的引擎。服务重启后记录保留。学习摘要与规则复习要求通过正式接口读取原任务和作答记录；复习生成沿用原附件、检索模式与生成选项。`InMemoryLearningService` 仅用于独立检查。

单选、多选在前端判定答案；简答和讨论保存文本与参考要点。未评分回答不计入正确率分母。章节完成指标表示作答覆盖情况。详见[学习记录与复习](../../docs/design/learning-loop.md)。

## 12. 前后端联调注意事项

请求使用 `generation_options`。交互讲义通过 `max_section_count` 设置章节上限，默认 8；大纲至少 1 章，不固定生成 4—8 章。`section_count` 对图文讲义会同步为上限，交互讲义不具有相同的请求级强制转换。

生成期间读取部分预览与单元结果。已有资源可以单独重试；最终失败的单元没有用户侧独立重新生成入口。服务重启会将遗留任务标记为中断，保留已有产物，不自动从任意节点继续生成。接口见[API 说明](api.md)。

## 13. PowerShell API 调用

使用 `Invoke-RestMethod`，将请求对象通过 `ConvertTo-Json -Depth 10` 序列化。完整创建任务示例见 [API 说明](api.md)。不要在提交记录中保存真实密钥和个人材料。

## 14. 常见问题

配置、限流、资源失败及 Qdrant 占用的处理见[配置指南](../../docs/configuration.md)。查询规划、章节补充检索与来源记录见[知识查询流程](../../docs/design/retrieval-workflow.md)。
