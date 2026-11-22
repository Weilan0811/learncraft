# Interactive HTML 设计需求文档

## 1. 文档定位

本文档定义 `interactive_html` 内容类型的产品目标、输出形态、生成边界、自适应学习能力和阶段性交付要求。

`interactive_html` 面向互动式学习材料生成，核心产物包括在线互动 HTML 与离线 HTML 讲义。在线互动 HTML 承担完整教学讲解与学习交互，离线 HTML 讲义承担学习记录沉淀、总结复盘和个性化补充。

---

## 2. 产品定位

`interactive_html` 用于生成固定形态的互动式课程页面：

```text
纵向教材式页面
+
对话导师式互动引导
```

系统需要支持从用户请求和知识库内容出发，生成一份可阅读、可互动、可记录学习过程的在线课程，并在学习后生成学生专属离线讲义。

核心目标包括：

1. 生成完整、清楚、可持续阅读的在线互动课程。
2. 支持流程动画、案例对比、概念卡片、启发式问答、情景教学、练习题等模板化教学模块。
3. 记录学生在学习过程中的选择、简答、排序、拖拽、求助、困惑等学习事件。
4. 基于在线课程内容派生离线 HTML 讲义。
5. 在离线讲义中加入学生答题记录摘要、总结知识卡片和个性化补充内容。
6. 保持现有 `outline -> spec -> renderer -> exporter` 主流程的稳定性。

---

## 3. 双版本输出形态

### 3.1 在线互动 HTML

在线互动 HTML 用于真实学习过程。页面需要完整讲清楚课程内容，包含充分的讲解、示例、流程展示、案例分析和互动引导。

在线互动 HTML 包含：

| 类型 | 内容 |
|---|---|
| 课程讲解 | 标题、段落、概念卡片、重点提示、示例说明 |
| 展示增强 | 流程动画、案例对比、上下文拆解、步骤展示 |
| 互动练习 | 单选、多选、简答、拖拽匹配、排序、翻卡 |
| 对话教学 | 启发式多轮问答、情景任务、选择反馈 |
| 学习记录 | 完成进度、互动结果、学习事件、临时草稿 |

在线互动 HTML 的设计原则：

1. 课程内容具备完整教学闭环。
2. 互动模块穿插在正文教学过程中。
3. 页面表达优先使用 HTML 组件、卡片、动画、对话和练习题。
4. 组件样式、动画和交互行为由前端 Renderer 统一控制。
5. 初始生成阶段输出结构化课程规格，前端负责稳定渲染。
6. 学习过程反馈以即时反馈、模板提示和学习事件记录为主。

### 3.2 离线 HTML 讲义

离线 HTML 讲义用于课后复习与学习沉淀。离线讲义基于在线互动课程派生生成。

离线讲义生成规则：

```text
在线互动课程内容
- 互动控件与课堂操作模块
+ 学生答题记录摘要
+ 总结知识卡片
+ 个性化补充内容
= 学生专属离线 HTML 讲义
```

离线讲义包含：

| 类型 | 内容 |
|---|---|
| 基础讲解 | 在线课程中的核心讲解、概念卡片、案例、流程和总结 |
| 答题记录 | 学生选择题、简答题、求助、困惑等学习记录摘要 |
| 总结卡片 | 概括整节课内容的手绘风知识卡片 |
| 个性化补充 | 针对误解点、薄弱点和回答质量生成的解释、例子和提醒 |
| 复习增强 | 推荐复习点、拓展学习指引、后续练习建议 |

离线讲义的设计原则：

1. 以在线互动课程内容为基础派生。
2. 移除答题控件、拖拽控件、输入框、播放操作等学习过程组件。
3. 保留可用于复习的核心讲解和静态化展示内容。
4. 将互动结果整理为清晰、客观、可复习的答题记录摘要。
5. 在总结回顾部分生成一张手绘风知识卡片。
6. 支持后续插入 Adaptive Agent 生成的个性化补充内容。

---

## 4. 内容生成边界

### 4.1 Outline 生成边界

Outline 只负责课程骨架。

Outline 需要生成：

1. 课程标题。
2. 课程目标。
3. 面向对象。
4. 难度等级。
5. Section 列表。
6. 每个 Section 的学习目标。
7. 每个 Section 的核心概念。
8. 每个 Section 的关键问题或知识范围。

Outline 生成约束：

1. 不指定具体 Block 类型。
2. 不指定互动检查点插入位置。
3. 不指定图片、示例、流程动画或练习题。
4. 不指定每个 Section 的互动密度。
5. 不指定 Adaptive Agent 的具体补丁动作。

### 4.2 Unit Spec 生成边界

Unit Spec 负责把一个 Section 转换为有序 `LessonBlock[]`。

Unit Spec 需要完成：

1. 根据 Section 学习目标选择合适的 Block。
2. 在讲解、案例、流程和互动之间组织清晰顺序。
3. 设置互动题的题干、选项、反馈和目标概念。
4. 设置对话导师式引导文案。
5. 设置互动结果是否允许 Adaptive Agent 后续处理。
6. 保持内容适合纵向教材式阅读。

### 4.3 元素生成边界

在线互动 HTML 不承担过程性图片和思维导图生成。

元素生成策略：

| 位置 | 生成策略 |
|---|---|
| 在线课程正文 | 使用 HTML 组件、卡片、流程动画、Tabs、对话、练习题表达 |
| 在线 Section 过程内容 | 默认关闭图片和思维导图生成 |
| 在线课程总结 | 使用文本总结、概念卡片或静态组件完成总结 |
| 离线讲义总结 | 生成一张概括整节课内容的手绘风知识卡片 |
| 离线个性化补充 | 使用文本补充、例子、误区订正和学习指引 |

该策略用于降低在线课程生成成本，保护现有在线生成工作流的稳定性，并将视觉总结能力集中放入离线讲义生成流程。

---

## 5. LessonBlock 模块体系

`interactive_html` 使用 `LessonBlock[]` 作为核心内容组织单位。每个 Section 由多个有序 Block 构成。

### 5.1 在线课程 Block 分类

| 分类 | 典型 Block | 用途 |
|---|---|---|
| 基础阅读类 | heading、paragraph、concept_card、callout、example、summary | 承载课程正文与概念解释 |
| 展示增强类 | animated_flow、case_compare、context_inspector、stepper | 展示过程、对比、结构和上下文 |
| 互动练习类 | single_choice、multiple_choice、short_answer、drag_match、sequence、flashcard | 检查理解、诊断误解、推动参与 |
| 对话教学类 | socratic_chat、scenario | 形成多轮启发和情景化任务体验 |

### 5.2 离线讲义 Block 分类

| 分类 | 典型 Block | 用途 |
|---|---|---|
| 讲解保留类 | heading、paragraph、concept_card、callout、example、summary | 保留核心讲解 |
| 静态展示类 | static_stepper、static_case_compare、context_table | 将在线展示模块转为可复习内容 |
| 学习记录类 | answer_record_summary、scenario_record_summary | 沉淀学生互动结果 |
| 总结沉淀类 | summary_knowledge_card | 概括整节课内容 |
| 个性化补充类 | personalized_note、review_suggestion、extension_guide | 支持针对性复习 |

### 5.3 Block 选择原则

1. Block 由 Unit Spec 根据学习目标选择。
2. 每个 Section 需要包含清晰讲解和学习检查点。
3. 互动题服务于理解诊断、反思和迁移。
4. 情景教学的场景、任务、选择项和反馈保持一致。
5. 综合练习根据课程需要选择题型组合。
6. 前端组件以稳定渲染为优先，复杂视觉表现由组件内部完成。

---

## 6. Adaptive Agent 设计需求

### 6.1 工作定位

Adaptive Agent 负责处理学习事件，更新学习状态，并为学生专属离线讲义生成个性化补丁。

输入：

1. 当前课程规格。
2. 当前学生 Session。
3. 学生互动事件。
4. 当前学习状态。
5. 相关知识库上下文。

输出：

1. 即时反馈。
2. 更新后的学习状态。
3. 个性化讲义补丁。
4. 可选的轻量运行时提示。

### 6.2 决策原则

Adaptive Agent 根据上下文判断处理方式。系统提供通用规则和可用动作集合，由 Agent 在每次事件中选择合适动作。

可用动作包括：

| 动作 | 用途 |
|---|---|
| feedback_only | 返回即时反馈 |
| show_hint | 给出轻量提示 |
| insert_simplified_explanation | 在离线讲义中插入简化解释 |
| insert_concrete_example | 在离线讲义中插入具体例子 |
| insert_followup_question | 在离线讲义中加入追问与反思 |
| insert_misconception_note | 在离线讲义中加入误区订正 |
| rewrite_explanation_for_student | 在个性化讲义中改写局部讲解 |
| add_review_suggestion | 加入复习建议 |
| add_extension_guide | 加入拓展学习指引 |

### 6.3 个性化补丁目标

个性化补丁面向当前学生的离线讲义。

补丁内容包括：

1. 学生误区订正。
2. 学生薄弱概念补充。
3. 更具体的例子或类比。
4. 简答题参考评分点与学生回答差距。
5. 当前 Section 的个性化复习提示。
6. 后续拓展学习建议。

---

## 7. 工作流需求

### 7.1 P0 在线互动 HTML 生成闭环

```text
用户请求
  ↓
知识库检索
  ↓
生成课程 Outline
  ↓
逐 Section 生成 InteractiveHtmlSectionSpec
  ↓
校验 Section Spec
  ↓
组装 InteractiveHtmlSpec
  ↓
渲染在线互动 HTML
  ↓
创建学习 Session
  ↓
记录 LearningEvent
```

P0 目标是跑通在线互动课程生成、预览、交互和事件记录。

### 7.2 P1 离线 HTML 讲义生成闭环

```text
InteractiveHtmlSpec
  ↓
移除互动控件和课堂操作模块
  ↓
保留课程核心讲解、案例、流程和总结
  ↓
加入学生答题记录摘要
  ↓
生成总结知识卡片
  ↓
生成 OfflineHandoutSpec
  ↓
渲染离线 HTML
```

P1 目标是基于在线课程派生可复习、可导出的离线 HTML 讲义。

### 7.3 P2 Adaptive Agent 个性化补充闭环

```text
LearningEvent[]
  ↓
LearnerState
  ↓
Adaptive Agent 分析学习过程
  ↓
生成 PersonalizedHandoutPatch
  ↓
校验并应用补丁
  ↓
生成带个性化补充的离线讲义
```

P2 目标是把学生交互反馈转化为个性化补充内容。

### 7.4 P3 个性化讲义改写与学习指引

```text
LearningEvent[] + LearnerState + OfflineHandoutSpec
  ↓
识别薄弱概念与学习需求
  ↓
改写个性化讲义中的局部讲解
  ↓
生成推荐复习点和拓展学习指引
  ↓
生成增强版个性化讲义
```

P3 目标是让离线讲义具备更强的个性化改写、复习规划和拓展学习能力。

---

## 8. 校验与质量要求

### 8.1 在线互动 HTML 校验

| 校验项 | 要求 |
|---|---|
| 内容完整性 | 每个 Section 具备明确学习目标和完整讲解 |
| Block 合法性 | 所有 Block 类型来自在线 Block Registry |
| 互动有效性 | 互动题服务于目标概念和理解诊断 |
| 对话一致性 | 情景、任务、选择项、反馈保持逻辑一致 |
| 渲染稳定性 | 所有 Block 可由前端组件渲染 |
| 引用覆盖 | 关键讲解内容可追溯到知识库来源 |
| 长度控制 | Section 长度适合纵向阅读 |

### 8.2 离线 HTML 讲义校验

| 校验项 | 要求 |
|---|---|
| 内容保留 | 保留在线课程中的核心讲解和关键案例 |
| 交互移除 | 移除答题控件、拖拽操作、对话输入框等课堂操作元素 |
| 记录摘要 | 答题记录摘要清晰、客观、可复习 |
| 总结卡片 | 知识卡片能概括整节课核心内容 |
| 补丁合法 | 补丁目标存在，内容长度受控 |
| 个性化相关 | 补充内容能追溯到具体学习事件 |
| 导出稳定 | 支持 HTML 预览和后续 PDF 导出 |

---

## 9. 阶段性交付

### P0：在线互动 HTML 闭环

1. 新增 `interactive_html` 内容类型。
2. 生成 `InteractiveHtmlOutline`。
3. 逐 Section 生成 `InteractiveHtmlSectionSpec`。
4. 支持基础阅读类、展示增强类、互动练习类和对话教学类 Block。
5. 渲染在线互动 HTML。
6. 创建学习 Session。
7. 记录 LearningEvent。
8. 支持在线预览和交互事件提交。

### P1：离线 HTML 讲义闭环

1. 从 `InteractiveHtmlSpec` 派生 `OfflineHandoutSpec`。
2. 移除互动控件和课堂操作模块。
3. 将展示增强模块转换为静态讲义内容。
4. 生成学生答题记录摘要。
5. 在总结回顾处生成手绘风知识卡片。
6. 渲染离线 HTML。
7. 支持离线 HTML 预览与导出。

### P2：Adaptive Agent 个性化补充

1. 分析学生答题、简答、求助和困惑事件。
2. 更新 LearnerState。
3. 生成误区订正、补充解释和具体例子。
4. 将 `PersonalizedHandoutPatch` 应用到离线讲义。
5. 支持补丁校验与修复。
6. 支持按 Section 查看个性化补充内容。

### P3：个性化讲义改写与学习指引

1. 根据学生反馈改写个性化讲义中的局部讲解。
2. 生成推荐复习点。
3. 生成拓展学习指引。
4. 生成后续练习建议。
5. 支持多次学习后的讲义更新。
6. 支持增强版离线讲义导出。

---

## 10. 最终产出

系统需要支持以下产物：

| 产物 | 说明 |
|---|---|
| Interactive HTML | 学习过程使用的在线互动式课程页面 |
| Offline HTML Handout | 基于在线课程派生的离线 HTML 讲义 |
| Personalized Offline HTML | 加入个性化补充后的学生专属离线讲义 |
| Personalized PDF Handout | 学生专属 PDF 讲义 |
| LearningEvent Log | 学生学习事件记录 |
| LearnerState | 学生当前学习状态 |
| PersonalizedHandoutPatch | 个性化讲义补丁 |
