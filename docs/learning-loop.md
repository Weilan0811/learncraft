# 学习闭环

学习闭环把“生成互动讲义”扩展为“生成 → 学习 → 诊断 → 再生成”。当前实现是最小可用版本：数据持久化、规则摘要、规则 brief；LLM brief 与长期学习画像在接口上已预留。

## 数据模型

### interactive_learning_session

| 字段 | 类型 | 说明 |
|---|---|---|
| `session_id` | string(64) PK | `session_` + 12 位随机串 |
| `lesson_id` | string(128) index | `lesson_{task_id}` 或 `partial_lesson_{task_id}` |
| `state` | JSON | 预留的会话状态 |
| `created_at` / `updated_at` | datetime | 事件提交时刷新 `updated_at` |

### interactive_learning_event

| 字段 | 类型 | 说明 |
|---|---|---|
| `event_id` | string(64) PK | `event_` + 12 位随机串 |
| `session_id` | string(64) FK/index | 归属会话 |
| `lesson_id` | string(128) index | 冗余便于按讲义查询 |
| `section_id` | string(128) index | 章节 |
| `block_id` | string(128) | 教学块 |
| `interaction_id` | string(128) | 互动 ID |
| `event_type` | string(64) index | 见下表 |
| `payload` | JSON | 作答内容、对错、用时等 |
| `created_at` | datetime | 提交时间 |

### 事件类型

答题类：`single_choice_answered`、`multiple_choice_answered`、`short_answer_submitted`、`scenario_discussion_submitted`、`drag_match_submitted`、`sequence_submitted`、`socratic_round_answered`、`scenario_choice_selected`。

求助类：`hint_requested`、`confused_clicked`。

## 接口

### 创建会话

```http
POST /api/interactive-lessons/{lesson_id}/sessions
Content-Type: application/json

{}
```

```json
{
  "session_id": "session_fff9c77aac06",
  "lesson_id": "lesson_task_50d8ee6ad2ac",
  "state": {}
}
```

### 提交事件

```http
POST /api/interactive-lessons/{lesson_id}/sessions/{session_id}/events
```

```json
{
  "section_id": "unit_2_why_it_works",
  "interaction_id": "unit_2_why_it_works_choice",
  "event_type": "single_choice_answered",
  "payload": {
    "selected_option_ids": ["b"],
    "is_correct": false,
    "time_spent_seconds": 40
  }
}
```

### 会话状态

`GET /api/interactive-lessons/{lesson_id}/sessions/{session_id}/state`

返回事件总数与 `total_answered / help_requested_count / total_events`。

### 学习摘要

`GET /api/interactive-lessons/{lesson_id}/sessions/{session_id}/summary`

```json
{
  "session_id": "session_fff9c77aac06",
  "lesson_id": "lesson_task_50d8ee6ad2ac",
  "total_events": 5,
  "total_answered": 4,
  "total_correct": 2,
  "total_scored": 3,
  "accuracy": 0.667,
  "help_requested_count": 1,
  "total_time_spent_seconds": 140,
  "answered_sections": 3,
  "total_sections": 4,
  "completion_rate": 0.75,
  "section_progress": [
    {
      "section_id": "unit_2_why_it_works",
      "title": "为什么有效：例子如何给模型“打样”",
      "answered_count": 1,
      "correct_count": 0,
      "scored_count": 1,
      "accuracy": 0.0,
      "help_requested_count": 1,
      "time_spent_seconds": 50,
      "is_weak": true
    }
  ],
  "weak_concepts": [
    { "concept": "少样本示例", "score": 3, "sections": ["unit_2_why_it_works"] }
  ],
  "review_sections": ["unit_2_why_it_works"],
  "summary_text": "已完成 3/4 个章节；答对 2/3 题；薄弱概念：少样本示例、格式约束、示例的局限性；建议重点复习：为什么有效：例子如何给模型“打样”。"
}
```

### adaptive brief

`POST /api/interactive-lessons/{lesson_id}/sessions/{session_id}/adaptive-brief`

```json
{ "difficulty": null }
```

```json
{
  "lesson_id": "lesson_task_50d8ee6ad2ac",
  "session_id": "session_fff9c77aac06",
  "topic_suggestion": "少样本示例入门：用例子教会模型做任务：薄弱点复习（少样本示例、格式约束、示例的局限性）",
  "focus_prompt": "请为同一位学习者生成一份复习型互动讲义。重点讲清以下薄弱概念：少样本示例、格式约束、示例的局限性。优先重讲章节：为什么有效：例子如何给模型“打样”。针对易错点补充讲解、例题与即时反馈，保持原讲义的教学语气与知识范围，不要引入未学过的前置知识。",
  "weak_concepts": ["少样本示例", "格式约束", "示例的局限性"],
  "review_sections": ["unit_2_why_it_works"],
  "suggested_difficulty": "introductory",
  "evidence": {
    "accuracy": 0.667,
    "total_answered": 4,
    "help_requested_count": 1,
    "weak_concepts": ["少样本示例", "格式约束", "示例的局限性"],
    "review_sections": ["unit_2_why_it_works"]
  }
}
```

无答题记录时返回 `409`；会话不存在或不属于该讲义时返回 `404`。

响应还包含 `source_request`，即从原任务数据库读取的完整生成请求，结构与 `POST /api/content-generation/tasks` 的请求相同。原请求缺失或无法解析时为 `null`，前端会提示无法生成复习讲义。

## 摘要算法

### 正确性判定

1. `payload.is_correct` 为布尔：直接使用；
2. 否则 `payload.heuristic_score` 为整数：`>= 60` 视为正确；
3. 否则计为“已作答但未评分”，不计入正确率分母。

### 章节指标

- `accuracy = correct_count / scored_count`，无评分时为 `null`；
- `is_weak = (scored_count > 0 且 accuracy < 0.6) 或 help_requested_count > 0`；
- 用时累加 `payload.time_spent_seconds`。

### 薄弱概念

- 每个错误/低分答题，为其 `interaction_id` 对应的 `target_concepts` 各加 2 分；
- 每个带 `interaction_id` 的求助事件，各加 1 分；
- 按分数降序取前 5；
- 概念映射优先读 `content_spec`，缺失时回退 `final_render`；映射不到时跳过，不编造概念名。

### 复习章节

取 `is_weak` 章节，按 `accuracy` 升序（无评分排后）、求助次数降序排序。

### 完成度

`answered_sections / total_sections`。`total_sections` 取自讲义中有互动的章节；历史任务缺少规格时，以事件中出现的章节数为准。

## brief 规则

- **主题**：有薄弱概念 → `{标题}：薄弱点复习（概念1、概念2、概念3）`；否则 → `{标题}：重点章节复习`；再否则 → `{标题}：巩固练习`。
- **补充提示**：中文模板，包含薄弱概念、优先重讲章节、补充例题与即时反馈的约束。
- **建议难度**：
  1. 显式传入优先；
  2. 无有效正确率 → 沿用原讲义难度；
  3. `accuracy < 0.5` → `introductory`；
  4. `accuracy >= 0.85` 且求助 ≤ 1 → `advanced`；
  5. 其它 → 沿用原讲义难度。

## 前端

摘要面板只在 `InteractiveHtmlRenderer` 内渲染，因此只出现在互动讲义预览（工作台预览区与全屏预览）。当 `total_answered > 0` 时显示完成度、正确率、求助、用时、薄弱概念与建议复习章节。

点击“针对薄弱点再生成”：

1. 调用 adaptive brief，读取响应中的 `source_request` 作为原始配置，支持刷新后和历史记录中的讲义；
2. 以 `topic_suggestion` 作为新主题；
3. 把 `focus_prompt` 追加到原 `user_prompt`；
4. 沿用 `system_prompt`、`knowledge_base_ids` 和全部 `generation_options`，更新其中的建议难度；
5. 提交新的 `interactive_html` 任务。

## 演进方向

- **LLM brief**：保留同一响应结构，把 `AdaptiveBriefService.build` 内部替换为 LLM 生成，并可用规则结果作为约束与兜底。
- **学生长期画像**：把会话摘要按 `platform_user_id` 聚合，形成概念掌握度、偏好难度与常见错因；生成请求可携带画像摘要，brief 也可读取画像。
- **平台回写**：摘要与 brief 作为学习结果回写教育平台，更新学生档案与推荐策略。
