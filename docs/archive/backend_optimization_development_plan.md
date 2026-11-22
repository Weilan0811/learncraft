# Backend Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 降低内容生成后端复杂度，提升生成任务可观测性和执行速度，并将数据库结构从开发期大 JSON 状态表演进为可接入平台后端的产品化生成产物模型。

**Architecture:** 保留“一会话一主产物”的产品规则。平台后端继续作为用户、会话、权限和生成入口的主系统，内容生成模块保留独立服务和独立数据库，通过 `platform_user_id`、`platform_session_id`、`platform_log_id` 与平台侧 `content_generation_log.external_content_id` 关联，不做跨库外键。生成模块内部拆分为轻量任务主表、阶段产物表、检索引用表、资产表和事件/观测表，避免每个节点全量重写任务大 JSON。

**Tech Stack:** FastAPI, SQLModel, SQLAlchemy, Alembic, LangGraph, Pydantic v2, httpx, MySQL 8, pytest.

---

## 1. 当前问题和设计原则

### 1.1 当前问题

- `backend/app/generators/unit_spec_generators.py` 同时承载 lecture、slide、interactive_html 的 LLM 调用、fallback、normalize、图片需求构造和大量交互 HTML fallback，文件体积过大，后续维护风险高。
- `backend/app/services/llm_service.py` 中 Bailian 和 Deepseek 都是 OpenAI-compatible 接口，但请求、重试、解析、修复逻辑重复。
- 真实 provider 失败后，部分生成路径会无条件 fallback，开发演示体验好，但产品环境会掩盖真实失败原因。
- 任务过程缺少结构化性能观测。当前能看到 logs 和 debug artifacts，但不能稳定按节点统计耗时、token、重试次数和 fallback 原因。
- 慢 I/O 仍以串行为主，尤其 unit 生成、图片生成和播客 TTS。长内容任务耗时会随单元数近似线性增加。
- `content_generation_task` 主表保存过多大 JSON，包括 outline、content_spec、render_model、unit_results、render_units、stream_events、logs、elements。每次 state update 都可能造成 DB 写放大。

### 1.2 产品和数据库边界

- 平台后端保留“一会话一主产物”规则：平台侧 `content_generation_log.session_id` 继续保持唯一约束。
- 生成模块保留独立 `content_generator` 数据库。平台库只保存生成记录索引和外部任务 ID，不直接存储完整生成产物。
- 生成模块数据库不建立跨库外键，只保存平台关联 ID 字段并加索引。
- 产品态必须能查询三类核心内容：
  - 大纲内容以及 planning 阶段检索引用。
  - spec 内容以及对应 unit/direct 生成阶段检索引用。
  - 最终渲染结果。
- 开发态仍保留本地 debug artifacts，但默认不把完整 debug trace 写入主业务表。

---

## 2. 预期项目目录结构

以下是优化后建议形成的后端结构。文件名可在实现时微调，但职责边界应保持一致。

```text
backend/app/
  generators/
    __init__.py
    common/
      __init__.py
      prompt_loader.py
      retrieval_formatter.py
      unit_prompt_builder.py
    unit_specs/
      __init__.py
      lecture.py
      slide.py
      interactive_html.py
      slide_normalizer.py
      element_requirements.py
      fallback_lecture.py
      fallback_slide.py
      fallback_interactive_html.py
      repair.py
    direct/
      __init__.py
      social_post.py
      podcast.py
  services/
    llm/
      __init__.py
      base.py
      openai_compatible.py
      factory.py
      schema_contract.py
    image_generation_service.py
    rag_service.py
    task_repository.py
    artifact_repository.py
    telemetry_repository.py
  models/
    content_generation_task.py
    content_generation_artifact.py
    content_generation_reference.py
    content_generation_asset.py
    content_generation_event.py
    content_generation_metric.py
  schemas/
    artifacts.py
    observability.py
  workflows/
    content_generation_graph.py
    parallel_units.py
    nodes/
      ...
  core/
    telemetry.py
    fallback.py
  alembic/
    versions/
      YYYYMMDD_0004_content_generation_artifacts.py
      YYYYMMDD_0005_content_generation_observability.py
```

兼容策略：

- `backend/app/services/llm_service.py` 第一阶段保留，改成 re-export 新 `services/llm/factory.py` 中的 `get_llm_service`、`LLMGenerationError` 和协议类型，减少一次性修改面。
- `backend/app/generators/unit_spec_generators.py` 第一阶段保留为兼容 facade，只导入并转发到 `generators/unit_specs/*`。等调用方全部迁移并稳定后，再删除大文件。
- API 路由第一阶段保持响应结构兼容。新增读取 artifact/reference 的接口可以作为增量 API，不破坏平台当前 `task_id`、`preview_url`、`refresh` 接入模式。

---

## 3. 数据库目标设计

### 3.1 `content_generation_task`

任务主表只保存轻量元信息和平台关联。

```text
id: int primary key
task_id: varchar(64) unique index
platform_log_id: varchar(64) nullable index
platform_user_id: varchar(64) nullable index
platform_session_id: varchar(64) nullable index
content_type: varchar(32) index
topic: varchar(255) nullable
status: varchar(32) index
current_node: varchar(128) nullable
progress: JSON not null
request_payload: JSON not null
generation_options: JSON not null default {}
preview_url: varchar(512) nullable
error_summary: varchar(1000) nullable
asset_ids: JSON not null default []
export_files: JSON not null default []
errors: JSON not null default []
created_at / updated_at / started_at / completed_at
```

保留旧字段的迁移策略：

- `outline`、`content_spec`、`render_model`、`partial_render_model`、`unit_results`、`render_units`、`stream_events`、`logs`、`elements` 先保留一版，迁移脚本把历史数据复制到新表。
- 代码切到新 repository 后，再用后续迁移删除旧大字段。避免一次迁移过猛。

### 3.2 `content_generation_artifact`

阶段产物表保存大纲、单元 spec、完整 spec、单元渲染和最终渲染。

```text
id: varchar(64) primary key
task_id: varchar(64) index
artifact_type: varchar(32) index
unit_id: varchar(128) nullable index
unit_order: int nullable
version: int not null default 1
status: varchar(32) not null
schema_name: varchar(128) nullable
schema_version: varchar(32) nullable
payload: JSON not null
payload_hash: varchar(64) not null index
source_node: varchar(128) nullable
created_at: datetime not null
updated_at: datetime not null
```

建议 `artifact_type`：

- `outline`
- `unit_spec`
- `content_spec`
- `unit_render`
- `partial_render`
- `final_render`
- `export_manifest`

### 3.3 `content_generation_reference`

检索引用表保存每个阶段使用的知识库参考。

```text
id: varchar(64) primary key
task_id: varchar(64) index
artifact_id: varchar(64) nullable index
stage: varchar(32) index
unit_id: varchar(128) nullable index
knowledge_base_id: varchar(128) nullable index
chunk_id: varchar(255) not null index
source_id: varchar(255) nullable
source_title: varchar(512) nullable
score: float nullable
retrieval_query: text nullable
content_excerpt: text nullable
content_hash: varchar(64) nullable index
metadata: JSON not null default {}
created_at: datetime not null
```

保存原则：

- 默认保存 chunk id、title、score、query、摘要和 hash。
- 不默认保存完整 chunk 正文，避免数据库膨胀和知识库内容重复。
- 如果产品要求审计复现，可以在 `metadata.persist_full_text=true` 时额外写完整快照，或保存到对象存储再在 `metadata.storage_key` 中引用。

### 3.4 `content_generation_asset`

资产表保存图片、音频、HTML、PDF、slide JSON、zip 等资源。

```text
id: varchar(64) primary key
task_id: varchar(64) index
unit_id: varchar(128) nullable index
asset_type: varchar(32) index
provider: varchar(64) nullable
model: varchar(128) nullable
asset_url: varchar(512) not null
storage_key: varchar(512) nullable
mime_type: varchar(128) nullable
status: varchar(32) index
metadata: JSON not null default {}
created_at: datetime not null
updated_at: datetime not null
```

### 3.5 `content_generation_event`

事件表用于前端轮询和过程回放，append-only。

```text
id: varchar(64) primary key
task_id: varchar(64) index
event_type: varchar(64) index
node: varchar(128) nullable index
unit_id: varchar(128) nullable index
payload: JSON not null
created_at: datetime not null index
```

### 3.6 `content_generation_metric`

观测表记录节点耗时、LLM token、provider 重试和 fallback。

```text
id: varchar(64) primary key
task_id: varchar(64) index
node: varchar(128) index
unit_id: varchar(128) nullable index
provider: varchar(64) nullable
model: varchar(128) nullable
duration_ms: int nullable
prompt_tokens: int nullable
completion_tokens: int nullable
total_tokens: int nullable
retry_count: int not null default 0
fallback_used: bool not null default false
fallback_reason: varchar(1000) nullable
error_type: varchar(128) nullable
metadata: JSON not null default {}
created_at: datetime not null
```

---

## 4. 修改计划总览

### Task 1: 建立基线和兼容测试

**Files:**

- Modify: `backend/tests/test_workflow_structure.py`
- Modify: `backend/tests/test_provider_services.py`
- Create: `backend/tests/test_content_generation_repository_contract.py`

**方案:**

先用测试锁定现有行为，避免后续拆文件和改数据库时无意破坏 API。重点覆盖 `create_task`、`save_state`、`get_task`、`preview_url`、`content_type`、`status`、旧字段兼容读取。

**步骤:**

- [ ] 运行当前后端测试，记录基线。

  Run:

  ```powershell
  .\.venv\Scripts\python.exe -m pytest backend/tests -q -p no:cacheprovider
  ```

  Expected: 当前主分支测试通过，或记录已有失败作为非本计划引入问题。

- [ ] 新增 repository contract 测试，使用 sqlite 临时库创建任务、保存 outline/content_spec/render_model 后能读取到同等数据。

  Test outline:

  ```python
  def test_repository_saves_generation_artifacts_without_losing_task_summary(tmp_path):
      repository = SQLModelTaskRepository(database_url=f"sqlite:///{tmp_path / 'test.db'}", create_tables=True)
      request = ContentGenerationRequest(content_type="lecture", topic="T", user_prompt="P")
      task = repository.create_task(request, task_id="task_contract")
      assert task.task_id == "task_contract"
      # Build a minimal ContentGenerationState with outline/content_spec/render_model.
      # Save it and assert task summary remains readable through get_task().
  ```

- [ ] 新测试先只约束外部行为，不绑定旧表内部字段。后续 Task 6 改 repository 时复用这些测试。

- [ ] 提交基线测试。

  ```powershell
  git add backend/tests/test_content_generation_repository_contract.py backend/tests/test_workflow_structure.py backend/tests/test_provider_services.py
  git commit -m "test: lock content generation backend contracts"
  ```

---

### Task 2: 拆分 `unit_spec_generators.py`

**Files:**

- Create: `backend/app/generators/common/prompt_loader.py`
- Create: `backend/app/generators/common/retrieval_formatter.py`
- Create: `backend/app/generators/common/unit_prompt_builder.py`
- Create: `backend/app/generators/unit_specs/lecture.py`
- Create: `backend/app/generators/unit_specs/slide.py`
- Create: `backend/app/generators/unit_specs/interactive_html.py`
- Create: `backend/app/generators/unit_specs/slide_normalizer.py`
- Create: `backend/app/generators/unit_specs/element_requirements.py`
- Create: `backend/app/generators/unit_specs/fallback_lecture.py`
- Create: `backend/app/generators/unit_specs/fallback_slide.py`
- Create: `backend/app/generators/unit_specs/fallback_interactive_html.py`
- Create: `backend/app/generators/unit_specs/repair.py`
- Modify: `backend/app/generators/unit_spec_generators.py`
- Modify: `backend/app/workflows/nodes/unit_spec_generator_node.py`
- Modify: `backend/app/workflows/nodes/unit_spec_repair_node.py`
- Test: `backend/tests/test_interactive_html_prompts.py`
- Test: `backend/tests/test_slide_design_pro.py`
- Test: `backend/tests/test_workflow.py`

**方案:**

分两步拆。第一步搬迁纯函数和 fallback，保留旧文件作为 facade。第二步将 workflow 调用迁移到新模块。这样每次移动都有测试保护。

**目标职责:**

- `prompt_loader.py`: 只负责按 group/name 读取 prompt 模板。
- `retrieval_formatter.py`: 只负责把 `RetrievedChunk` 格式化为 prompt 可用摘要。
- `unit_prompt_builder.py`: 只负责构建 unit spec 和 repair prompt。
- `lecture.py`: lecture unit spec 的 LLM 调用和 fallback 调度。
- `slide.py`: slide unit spec 的 LLM 调用和 fallback 调度。
- `interactive_html.py`: interactive_html unit spec 的 LLM 调用和 fallback 调度。
- `slide_normalizer.py`: slide spec normalize 和文本预算裁剪。
- `element_requirements.py`: 图片和 mindmap requirement 构造。
- `fallback_*`: 各内容类型 deterministic fallback。
- `repair.py`: unit spec repair prompt 和 repair 调用。

**步骤:**

- [ ] 新建 `generators/common/retrieval_formatter.py`，迁移 `_format_retrieval_results`。

  Expected API:

  ```python
  def format_retrieval_results(chunks: list, *, max_chars_per_chunk: int = 500) -> str:
      ...
  ```

- [ ] 为 `format_retrieval_results` 添加单元测试，覆盖空 chunks、含 title、内容截断。

  Run:

  ```powershell
  .\.venv\Scripts\python.exe -m pytest backend/tests/test_interactive_html_prompts.py -q -p no:cacheprovider
  ```

- [ ] 新建 `prompt_loader.py` 和 `unit_prompt_builder.py`，迁移 `_get_unit_spec_template_path`、`_build_unit_spec_prompt`、`_build_unit_spec_repair_prompt`。

  Expected API:

  ```python
  def load_prompt_template(group: str, filename: str) -> str:
      ...

  def build_unit_spec_prompt(content_type: str, state: ContentGenerationState, unit: OutlineUnit, unit_spec_id: str) -> str:
      ...

  def build_unit_spec_repair_prompt(content_type: str, state: ContentGenerationState, unit: OutlineUnit, unit_spec_id: str, validation_errors: list[str]) -> str:
      ...
  ```

- [ ] 新建 `slide_normalizer.py` 和 `element_requirements.py`，迁移 slide normalize、文本预算和 element requirement 构造。

- [ ] 新建三个 fallback 文件，迁移 deterministic fallback。迁移后旧文件仅保留导入和转发。

- [ ] 新建 `lecture.py`、`slide.py`、`interactive_html.py`，分别暴露：

  ```python
  def build_lecture_unit_spec(state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]) -> LectureSection: ...
  def build_slide_unit_spec(state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]) -> SlideSpecPage: ...
  def build_interactive_html_unit_spec(state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]) -> InteractiveHtmlSectionSpec: ...
  ```

- [ ] 新建 `repair.py`，暴露：

  ```python
  def repair_unit_spec_with_llm(state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str], validation_errors: list[str]) -> LectureSection | SlideSpecPage | InteractiveHtmlSectionSpec: ...
  ```

- [ ] 将 `unit_spec_generators.py` 改为兼容 facade，从新模块 import 并 re-export 旧函数名。

- [ ] 将 workflow 节点 import 切到新模块。

- [ ] 运行相关测试。

  ```powershell
  .\.venv\Scripts\python.exe -m pytest backend/tests/test_slide_design_pro.py backend/tests/test_interactive_html_prompts.py backend/tests/test_workflow.py -q -p no:cacheprovider
  ```

- [ ] 提交拆分。

  ```powershell
  git add backend/app/generators backend/app/workflows/nodes backend/tests
  git commit -m "refactor: split unit spec generators"
  ```

---

### Task 3: 抽象 OpenAI-compatible LLM provider

**Files:**

- Create: `backend/app/services/llm/base.py`
- Create: `backend/app/services/llm/openai_compatible.py`
- Create: `backend/app/services/llm/schema_contract.py`
- Create: `backend/app/services/llm/factory.py`
- Modify: `backend/app/services/llm_service.py`
- Test: `backend/tests/test_provider_services.py`

**方案:**

抽象公共 OpenAI-compatible 逻辑，Bailian 和 Deepseek 变成配置差异。保留旧 `llm_service.py` 作为兼容入口，减少调用方修改。

**目标接口:**

```python
class LLMService(Protocol):
    last_usage: dict[str, object]
    last_retry_count: int

    def chat(self, user_message: str, system_prompt: str = "") -> str: ...
    def generate_structured(self, prompt: str, schema: type[StructuredModel]) -> StructuredModel: ...
```

**步骤:**

- [ ] 写 provider 测试：mock client 返回合法 JSON，Bailian/Deepseek 都能解析为 Pydantic schema。

- [ ] 写 retry 测试：第一次 HTTP error，第二次成功，`last_retry_count == 1`。

- [ ] 写 schema repair 测试：第一次返回非法 JSON，repair 后合法，最终返回 schema 实例。

- [ ] 实现 `OpenAICompatibleLLMService`，统一 `_post_with_retries`、`_extract_content`、`_parse_content`、`_repair_and_parse`。

- [ ] 实现 `schema_contract.py`。

  第一阶段仍可传完整 JSON Schema，但通过函数封装：

  ```python
  def build_schema_instruction(schema: type[BaseModel]) -> str:
      return json.dumps(schema.model_json_schema(), ensure_ascii=False)
  ```

  后续 token 优化可以在这里切换为压缩 schema，不影响调用方。

- [ ] 实现 `factory.py`，根据 settings 创建 provider。

- [ ] 将 `llm_service.py` 改为兼容导出：

  ```python
  from app.services.llm.base import LLMGenerationError, LLMService
  from app.services.llm.factory import get_llm_service
  ```

- [ ] 运行 provider 测试。

  ```powershell
  .\.venv\Scripts\python.exe -m pytest backend/tests/test_provider_services.py -q -p no:cacheprovider
  ```

- [ ] 提交 LLM 抽象。

  ```powershell
  git add backend/app/services/llm backend/app/services/llm_service.py backend/tests/test_provider_services.py
  git commit -m "refactor: unify openai compatible llm providers"
  ```

---

### Task 4: 调整 fallback 策略，让真实错误可见

**Files:**

- Create: `backend/app/core/fallback.py`
- Modify: `backend/app/generators/unit_specs/lecture.py`
- Modify: `backend/app/generators/unit_specs/slide.py`
- Modify: `backend/app/generators/unit_specs/interactive_html.py`
- Modify: `backend/app/generators/direct/social_post.py`
- Modify: `backend/app/generators/direct/podcast.py`
- Modify: `backend/app/workflows/nodes/planner_node.py`
- Modify: `backend/app/workflows/nodes/unit_spec_generator_node.py`
- Test: `backend/tests/test_workflow.py`
- Test: `backend/tests/test_workflow_logs.py`

**方案:**

统一 fallback 决策：只有 `provider_mode == "stub"` 或 `generation_options.allow_fallback == true` 时使用 fallback。真实 provider 报错且未允许 fallback 时，错误必须进入 workflow error，并让任务失败或走已有 repair/fail 分支。

**目标接口:**

```python
def allow_generation_fallback(state: ContentGenerationState | None, normalized_request: dict | None, provider_mode: str) -> bool:
    return provider_mode == "stub" or bool((normalized_request or {}).get("allow_fallback", False))

def fallback_detail(stage: str, exc: Exception) -> dict[str, object]:
    return {
        "stage": stage,
        "code": type(exc).__name__,
        "message": str(exc),
        "recoverable": True,
    }
```

**步骤:**

- [ ] 写测试：`provider_mode=real` 且 `allow_fallback=False` 时，unit spec LLM 抛错不会返回 fallback spec。

- [ ] 写测试：`provider_mode=real` 且 `allow_fallback=True` 时，返回 fallback spec，并记录 `fallback_reason`。

- [ ] 实现 `core/fallback.py`。

- [ ] 修改三个 unit generator，删除裸 `except Exception: return fallback`，改成显式判断。

- [ ] 修改 direct generators，使 social_post / podcast 的 fallback 策略与 unit_loop 一致。

- [ ] 修改 planner：outline fallback 也遵循同一策略。开发 stub 可 fallback；真实模式默认暴露错误。

- [ ] 修改 workflow 节点，在捕获错误时写入 `workflow_errors`，字段包括 `stage`、`code`、`message`、`recoverable`、`fallback_used`。

- [ ] 运行 workflow 和日志测试。

  ```powershell
  .\.venv\Scripts\python.exe -m pytest backend/tests/test_workflow.py backend/tests/test_workflow_logs.py -q -p no:cacheprovider
  ```

- [ ] 提交 fallback 策略。

  ```powershell
  git add backend/app/core/fallback.py backend/app/generators backend/app/workflows/nodes backend/tests
  git commit -m "fix: make real provider fallback explicit"
  ```

---

### Task 5: 增加生成观测

**Files:**

- Create: `backend/app/core/telemetry.py`
- Create: `backend/app/schemas/observability.py`
- Create: `backend/app/services/telemetry_repository.py`
- Modify: `backend/app/workflows/content_generation_graph.py`
- Modify: `backend/app/services/llm/base.py`
- Modify: `backend/app/services/llm/openai_compatible.py`
- Modify: `backend/app/services/image_generation_service.py`
- Modify: `backend/app/services/tts_service.py`
- Test: `backend/tests/test_workflow_logs.py`
- Test: `backend/tests/test_provider_services.py`

**方案:**

建立统一 `GenerationMetric` 结构，记录节点耗时、provider、model、token、retry、fallback。工作流层记录节点耗时，provider 层记录调用级 usage/retry，repository 将指标写入 `content_generation_metric`。

**目标模型:**

```python
class GenerationMetric(SchemaModel):
    task_id: str
    node: str
    unit_id: str | None = None
    provider: str | None = None
    model: str | None = None
    duration_ms: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    retry_count: int = 0
    fallback_used: bool = False
    fallback_reason: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
```

**步骤:**

- [ ] 新增 schema 测试：`GenerationMetric` 能序列化 token 和 fallback 字段。

- [ ] 实现 `core/telemetry.py`，提供 `monotonic_ms()`、`build_node_metric()`、`build_provider_metric()`。

- [ ] 在 `OpenAICompatibleLLMService` 中记录 `last_usage` 和 `last_retry_count`。

- [ ] 在 image/TTS provider 中记录 retry count 和 provider metadata。

- [ ] 在 `stream_content_generation` 中围绕 `graph.stream` values update 记录节点耗时。每个 node 完成时生成 metric。

- [ ] 新增 `TelemetryRepository.append_metrics(task_id, metrics)`，第一阶段可被 `SQLModelTaskRepository.save_state` 调用。

- [ ] 将 fallback 策略中产生的 `fallback_reason` 写入 metric。

- [ ] 运行测试。

  ```powershell
  .\.venv\Scripts\python.exe -m pytest backend/tests/test_workflow_logs.py backend/tests/test_provider_services.py -q -p no:cacheprovider
  ```

- [ ] 提交观测改造。

  ```powershell
  git add backend/app/core/telemetry.py backend/app/schemas/observability.py backend/app/services backend/app/workflows backend/tests
  git commit -m "feat: add generation telemetry"
  ```

---

### Task 6: 修改数据库表结构并完成迁移

**Files:**

- Create: `backend/app/models/content_generation_artifact.py`
- Create: `backend/app/models/content_generation_reference.py`
- Create: `backend/app/models/content_generation_asset.py`
- Create: `backend/app/models/content_generation_event.py`
- Create: `backend/app/models/content_generation_metric.py`
- Create: `backend/app/schemas/artifacts.py`
- Create: `backend/app/services/artifact_repository.py`
- Create: `backend/alembic/versions/YYYYMMDD_0004_content_generation_artifacts.py`
- Create: `backend/alembic/versions/YYYYMMDD_0005_content_generation_observability.py`
- Modify: `backend/app/models/content_generation_task.py`
- Modify: `backend/app/services/task_repository.py`
- Modify: `backend/app/services/task_service.py`
- Test: `backend/tests/test_task_persistence.py`
- Test: `backend/tests/test_unit_streaming.py`
- Test: `backend/tests/test_content_generation_repository_contract.py`

**方案:**

先新增表和新 repository，保留旧字段兼容读取；再把写路径切到 artifact/reference/event/metric；最后在后续版本删除旧大 JSON 字段。迁移必须支持 MySQL 和测试用 sqlite。

**步骤:**

- [ ] 新增五个 SQLModel 模型。

  Required table names:

  ```text
  content_generation_artifact
  content_generation_reference
  content_generation_asset
  content_generation_event
  content_generation_metric
  ```

- [ ] 扩展 `ContentGenerationTask`，新增平台关联字段和轻量摘要字段。

  Required fields:

  ```python
  platform_log_id: str | None
  platform_user_id: str | None
  platform_session_id: str | None
  topic: str | None
  generation_options: dict[str, Any]
  preview_url: str | None
  error_summary: str | None
  ```

- [ ] 新增 Alembic revision `0004`，创建 artifact/reference/asset 表，并给 `content_generation_task` 添加平台关联字段。

- [ ] 新增 Alembic revision `0005`，创建 event/metric 表。

- [ ] 在 `0004` 中添加历史数据迁移：

  - 旧 `outline` 非空时写入 `content_generation_artifact(type='outline')`。
  - 旧 `content_spec` 非空时写入 `content_generation_artifact(type='content_spec')`。
  - 旧 `render_model` 非空时写入 `content_generation_artifact(type='final_render')`。
  - 旧 `render_units` 非空时按 unit 写入 `content_generation_artifact(type='unit_render')`。
  - 旧 `unit_results` 非空时按 unit 写入 `content_generation_artifact(type='unit_spec')`。

- [ ] 实现 `ArtifactRepository`。

  Required methods:

  ```python
  def upsert_artifact(self, task_id: str, artifact_type: str, payload: dict, unit_id: str | None = None, unit_order: int | None = None, status: str = "final", source_node: str | None = None) -> ContentGenerationArtifact: ...
  def append_references(self, task_id: str, stage: str, chunks: list, artifact_id: str | None = None, unit_id: str | None = None, retrieval_query: str | None = None) -> list[ContentGenerationReference]: ...
  def append_event(self, task_id: str, event: dict) -> ContentGenerationEvent: ...
  def append_metric(self, task_id: str, metric: dict) -> ContentGenerationMetric: ...
  def get_latest_artifact(self, task_id: str, artifact_type: str, unit_id: str | None = None) -> ContentGenerationArtifact | None: ...
  ```

- [ ] 修改 `SQLModelTaskRepository.save_state`：

  - 主任务表只更新 status/current_node/progress/errors/asset_ids/export_files/preview_url。
  - outline/content_spec/render_model/partial_render_model/render_units/unit_results 通过 `ArtifactRepository` 写入。
  - planning_chunks/current_unit_context 通过 `append_references` 写入。
  - stream_events 通过 `append_event` 写入。
  - metrics 通过 `append_metric` 写入。

- [ ] 修改读取逻辑：

  - `get_preview` 优先读 `artifact_type='final_render'`。
  - `get_partial_preview` 优先读 `artifact_type='partial_render'` 或最新 `unit_render` 聚合。
  - `get_units` 从 `artifact_type='unit_render'` 查询。
  - 旧字段保留 fallback 读取，确保老任务不坏。

- [ ] 增加平台关联入参。

  `ContentGenerationRequest` 可不直接包含平台字段；建议新增内部创建任务参数：

  ```python
  def create_task(self, request: ContentGenerationRequest, task_id: str | None = None, platform_context: PlatformContext | None = None) -> ContentGenerationTask:
      ...
  ```

  `PlatformContext` 包含 `platform_log_id`、`platform_user_id`、`platform_session_id`。

- [ ] 运行数据库测试。

  ```powershell
  .\.venv\Scripts\python.exe -m pytest backend/tests/test_task_persistence.py backend/tests/test_unit_streaming.py backend/tests/test_content_generation_repository_contract.py -q -p no:cacheprovider
  ```

- [ ] 运行迁移。

  ```powershell
  uv run alembic -c backend/alembic.ini upgrade head
  ```

- [ ] 提交数据库改造。

  ```powershell
  git add backend/app/models backend/app/schemas/artifacts.py backend/app/services backend/alembic/versions backend/tests
  git commit -m "feat: normalize content generation persistence"
  ```

---

### Task 7: 慢 I/O 改成有限并发

**Files:**

- Create: `backend/app/workflows/parallel_units.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/workflows/content_generation_graph.py`
- Modify: `backend/app/workflows/nodes/unit_loop_node.py`
- Modify: `backend/app/services/image_generation_service.py`
- Modify: `backend/app/generators/direct/social_post.py`
- Modify: `backend/app/renderers/podcast_renderer.py`
- Test: `backend/tests/test_unit_streaming.py`
- Test: `backend/tests/test_podcast_renderer.py`
- Test: `backend/tests/test_social_post_renderer.py`

**方案:**

分阶段并发，不一次性改完整 graph。

第一阶段：

- 图片 slot 并发。
- 播客 TTS segment 并发。

第二阶段：

- unit spec 生成有限并发。
- unit render 发布仍按 `unit_order` 排序，保持前端体验稳定。

**新增配置:**

```python
generation_unit_concurrency: int = 3
image_generation_concurrency: int = 3
tts_generation_concurrency: int = 4
provider_rate_limit_backoff_seconds: float = 2.0
```

**步骤:**

- [ ] 为 social post 图片生成写并发测试：三个 image slots 的 fake service 记录调用，输出资产顺序按 slot 顺序稳定。

- [ ] 用 `concurrent.futures.ThreadPoolExecutor` 或 async gather 改造 `_generate_image_assets`，并发上限来自 settings。

- [ ] 为 podcast TTS 写并发测试：segments 并发合成，最终 `PodcastRenderModel.segments` 按 order 排序。

- [ ] 改造 `PodcastRenderer.render`，TTS 并发执行，失败仍绑定原 segment。

- [ ] 新增 `parallel_units.py`，封装 unit 批处理策略。

  Required behavior:

  ```python
  def build_unit_batches(unit_ids: list[str], concurrency: int) -> list[list[str]]:
      ...
  ```

- [ ] 先不改变 LangGraph 主流程，增加可测试的批处理服务函数，为后续 graph 并发打基础。

- [ ] 第二阶段再把 `retrieve_for_unit -> generate_unit_spec -> render_unit` 改成 batch/Send 模式。要求：

  - 单元内状态隔离，避免共享 `current_unit_id` 造成竞态。
  - DB 写入按 unit artifact 追加，不依赖主 state 大 JSON。
  - `publish_unit_render` 事件按完成时间发送，但 `get_units` 按 `unit_order` 返回。

- [ ] 运行相关测试。

  ```powershell
  .\.venv\Scripts\python.exe -m pytest backend/tests/test_unit_streaming.py backend/tests/test_podcast_renderer.py backend/tests/test_social_post_renderer.py -q -p no:cacheprovider
  ```

- [ ] 提交有限并发改造。

  ```powershell
  git add backend/app/core/config.py backend/app/workflows backend/app/generators backend/app/renderers backend/tests
  git commit -m "perf: add bounded concurrency for slow generation io"
  ```

---

### Task 8: API 和平台接入补充

**Files:**

- Modify: `backend/app/api/content_generation.py`
- Modify: `backend/app/schemas/request.py`
- Modify: `backend/app/schemas/task.py`
- Create: `backend/app/schemas/artifacts.py`
- Test: `backend/tests/test_api.py`
- Test: `backend/tests/test_unit_streaming.py`

**方案:**

保持现有任务 API 兼容，同时新增产品需要的 artifact/reference 查询能力。平台当前可以继续只用 create/refresh/preview；后续前端需要展示大纲、引用、spec 时再接新增接口。

**新增建议接口:**

```text
GET /api/content-generation/tasks/{task_id}/artifacts
GET /api/content-generation/tasks/{task_id}/artifacts/{artifact_id}
GET /api/content-generation/tasks/{task_id}/outline
GET /api/content-generation/tasks/{task_id}/references?stage=planning&unit_id=...
GET /api/content-generation/tasks/{task_id}/metrics
```

**步骤:**

- [ ] 扩展任务创建内部能力，支持保存 `platform_context`。外部 API 可通过 header 或 request metadata 传入：

  ```text
  X-Platform-Log-Id
  X-Platform-User-Id
  X-Platform-Session-Id
  ```

  如果平台不传这些 header，任务仍可独立运行。

- [ ] 新增 artifact list/detail schema。

- [ ] 新增 reference list schema。

- [ ] 新增 API 测试：创建任务后能读取 outline artifact 和 planning references。

- [ ] 新增 API 测试：旧 preview API 仍返回原结构。

- [ ] 运行 API 测试。

  ```powershell
  .\.venv\Scripts\python.exe -m pytest backend/tests/test_api.py backend/tests/test_unit_streaming.py -q -p no:cacheprovider
  ```

- [ ] 提交 API 补充。

  ```powershell
  git add backend/app/api backend/app/schemas backend/tests
  git commit -m "feat: expose generation artifacts and references"
  ```

---

### Task 9: 文档和运维收口

**Files:**

- Modify: `backend/docs/content_generation_workflow.md`
- Modify: `backend/docs/api.md`
- Modify: `backend/docs/development_notes.md`
- Modify: `README.md`

**方案:**

更新开发文档，明确新持久化模型、平台接入边界、debug artifacts 和 DB 产物的区别。

**步骤:**

- [ ] 更新 workflow 文档，说明 unit artifact、reference、metric 的写入时机。

- [ ] 更新 API 文档，列出新增 artifact/reference/metrics 接口。

- [ ] 更新 development notes，说明：

  - 开发期本地 JSON debug artifacts 只用于排障。
  - 产品态可信数据源是 DB artifact/reference。
  - 平台后端保持一会话一主产物，生成模块用 platform IDs 关联。

- [ ] 更新 README 的 provider 和数据库迁移说明。

- [ ] 运行全量测试。

  ```powershell
  .\.venv\Scripts\python.exe -m pytest backend/tests -q -p no:cacheprovider
  ```

- [ ] 提交文档。

  ```powershell
  git add README.md backend/docs
  git commit -m "docs: describe optimized generation persistence"
  ```

---

## 5. 推荐实施顺序

建议按以下顺序推进，避免多个高风险改造同时发生：

1. Task 1: 建立基线和兼容测试。
2. Task 2: 拆分 `unit_spec_generators.py`。
3. Task 3: 抽象 OpenAI-compatible LLM provider。
4. Task 4: 调整 fallback 策略。
5. Task 5: 增加生成观测。
6. Task 6: 修改数据库表结构并完成迁移。
7. Task 8: API 和平台接入补充。
8. Task 7: 慢 I/O 有限并发。
9. Task 9: 文档和运维收口。

说明：并发改造建议放在数据库归一化之后，因为 unit 并发需要更细粒度的 artifact 写入作为支撑。如果先改并发，当前以 `current_unit_id` 和主 state 大 JSON 为中心的状态模型会增加竞态风险。

---

## 6. 风险和验收标准

### 6.1 主要风险

- 数据库迁移风险：旧任务大 JSON 迁移到 artifact 表时可能遇到 schema 版本不一致。
- 并发风险：unit 并发后，事件顺序和渲染顺序可能不同，需要前端按 `unit_order` 展示。
- fallback 策略风险：真实 provider 错误暴露后，短期任务失败率可能上升，但这是产品质量评估必须看到的信息。
- token 观测风险：不同 provider 的 usage 字段可能不完全一致，需要容忍缺失。

### 6.2 验收标准

- `unit_spec_generators.py` 不再承载主要业务逻辑，只作为兼容 facade 或被删除。
- Bailian 和 Deepseek 共用 OpenAI-compatible provider 基类。
- `allow_fallback=false` 时，真实 provider 失败不会静默生成 fallback 内容。
- 每个任务能查询节点耗时、LLM token、provider retry 次数和 fallback 原因。
- 大纲、unit spec、最终 render 都存入 `content_generation_artifact`。
- 大纲和 spec 对应的检索引用存入 `content_generation_reference`。
- 主任务表不再因每个节点 update 反复重写完整 render/spec/log/event 大 JSON。
- 平台仍可通过 `external_content_id` 查询任务和预览，一会话一主产物规则不变。
- 后端全量测试通过。

---

## 7. Self-Review

- Spec coverage: 六个用户指定改造点均已覆盖：生成器拆分、LLM provider 抽象、fallback 策略、生成观测、有限并发、数据库表结构和迁移。
- Platform rule coverage: 明确保留“一会话一主产物”，生成模块不做跨库外键，通过 platform IDs 与平台日志关联。
- Placeholder scan: 本计划没有使用 TBD、TODO 或未定义的后续占位步骤。
- Type consistency: 表名、字段名、artifact 类型和 repository 方法在文档内保持一致。
