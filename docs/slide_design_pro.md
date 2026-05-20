# Slide 生成方案优化版（最终收束版）

## 1. 修改目标

本轮修改目标是继续提升当前两种版式的成品感和展示质量，重点解决以下问题：

1. `image_text` 页文字区域层次不足，信息块边界不清晰。
2. `image_text` 页如果继续拆成 3 个小块，页面会过于碎片化。
3. `image_text` 页内容类型有差异，页面不适合固定成“核心解释 + 要点 + 例子”三段式。
4. `visual_summary` 页主图区域仍然偏紧，图片主体感不足。
5. 底部总结条存在固定前缀，页面风格偏机械。
6. 图片风格与布局适配仍需继续收紧。

本轮方案保持两种稳定版式，并进一步优化为：

* `image_text`：**左侧双卡片文本区 + 右侧单图 + 底部一句总结**
* `visual_summary`：**上方大图主展示区 + 底部一句总结**

---

## 2. 总体设计原则

## 2.1 继续保留 2 种固定布局

当前版本继续只保留以下两种布局：

1. `image_text`
2. `visual_summary`

所有 slide spec 只能使用这两种 layout。

---

## 2.2 `image_text` 文本区采用“双卡片”设计

`image_text` 页的文本区固定为两张卡片，不再拆成 3 张。

这样做的好处是：

1. 页面结构更稳。
2. 左右两个主视觉区已经足够饱满。
3. 卡片内容可以灵活变化，适配不同教学内容。
4. 页面风格统一，渲染逻辑更简单。

---

## 2.3 文本卡片语义可配置

每一页的两张文本卡片不再固定写死为某一类内容。
改为由 spec 指定每张卡片的**内容类型**和**展示标题**。

例如：

* 卡片 1：核心解释
* 卡片 2：关键要点

或：

* 卡片 1：案例说明
* 卡片 2：启发

或：

* 卡片 1：机制说明
* 卡片 2：过程要点

或：

* 卡片 1：例子
* 卡片 2：关键结论

这样页面内容会更自然，也更贴合不同主题。

---

## 2.4 `visual_summary` 页突出大图主体

`visual_summary` 页中，图片承担主体表达功能。
页面结构固定为：

* 顶部：标题
* 中上部：大图，尽量占满主区域
* 底部：一句总结

该页不再出现右侧总结卡，不再出现额外 takeaway 块。

---

## 2.5 底部总结去掉固定前缀

所有页面底部总结统一改为**纯一句话总结**，不再显示：

* `核心点：`
* `总结：`
* `结论：`

底部条只展示内容本身，视觉上更加干净。

---

# 3. 固定布局定义

## 3.1 布局 A：`image_text`

### 适用场景

* 概念解释
* 案例说明
* 应用场景
* 机制介绍
* 技术原理说明
* 流程中的单步骤说明

### 页面结构

```text
标题
------------------------------------------------

左侧：双卡片文本区        右侧：单张图片

底部：一句总结
```

### 左侧双卡片文本区

固定包含两张卡片：

1. `lead_card`：主信息卡片
2. `support_card`：补充信息卡片

### 两张卡片的可选内容类型

#### `lead_card` 可选类型

* 核心解释
* 定义说明
* 案例说明
* 机制说明
* 例子
* 关键结论

#### `support_card` 可选类型

* 关键要点
* 例子
* 启发
* 过程要点
* 应用提示
* 关键区别

### 页面要求

* 文本区只保留两张卡片。
* 右侧只保留一张图。
* 图片承担辅助说明作用。
* 底部保留一句总结。
* 页面内不再出现第三张独立文本卡片。

### 文本预算

#### `lead_card`

* 标题标签：不超过 6 个中文字符
* 内容：

  * 段落型：不超过 2 句
  * 要点型：不超过 3 条 bullet

#### `support_card`

* 标题标签：不超过 6 个中文字符
* 内容：

  * 段落型：不超过 2 句
  * 要点型：不超过 4 条 bullet
  * 例子型：不超过 1 句，最长 42 个中文字符

#### 底部总结

* 不超过 32 个中文字符

---

## 3.2 布局 B：`visual_summary`

### 适用场景

* 流程总结
* 结构总览
* 方法归纳
* 阶段复盘
* 知识框架总结
* 系统组成说明

### 页面结构

```text
标题
------------------------------------------------

上部：大图主展示区

底部：一句总结
```

### 页面要求

* 页面主视觉为一张大图。
* 图片占据页面的主要可视区域。
* 底部只保留一句总结。
* 不再显示右侧 summary card。
* 不再显示底部 takeaway 卡片。
* 图片优先完整展示，减少压缩感。

### 文本预算

* 标题：不超过 20 个中文字符
* 底部总结：不超过 36 个中文字符

---

# 4. Schema 修改方案

建议重点修改：`app/schemas/specs/slide.py`

---

## 4.1 修改 `SlideLayout`

保留：

```python
SlideLayout = Literal["image_text", "visual_summary"]
```

---

## 4.2 修改元素 role 设计

建议将原来的：

* `explanation`
* `bullet_list`
* `example`
* `takeaway`

统一收束为更稳定的结构化角色：

```python
SlideElementRole = Literal[
    "title",
    "lead_card",
    "support_card",
    "summary_text",
    "visual",
]
```

---

## 4.3 为文本卡片增加元数据字段

建议 `metadata` 增加：

```python
{
  "role": "lead_card",
  "display_label": "核心解释",
  "content_format": "paragraph"
}
```

或：

```python
{
  "role": "support_card",
  "display_label": "关键要点",
  "content_format": "bullets"
}
```

### 字段说明

#### `display_label`

控制卡片小标题，例如：

* 核心解释
* 关键要点
* 例子
* 案例说明
* 启发
* 机制说明

#### `content_format`

控制渲染方式：

* `paragraph`
* `bullets`

---

## 4.4 layout 契约

### `image_text` 必须包含

* `title`
* `lead_card`
* `support_card`
* `summary_text`
* `visual`

### `visual_summary` 必须包含

* `title`
* `visual`
* `summary_text`

---

# 5. Prompt 修改方案

建议重点修改：`app/prompts/generator/slide_deck_spec.md`

---

## 5.1 `image_text` 契约改写

改为：

```text
image_text 页必须包含：
- title
- lead_card
- support_card
- summary_text
- visual
```

并增加说明：

```text
lead_card 和 support_card 是两张独立信息卡片。

每张卡片必须提供：
- display_label：卡片标题，如“核心解释”“关键要点”“例子”“案例说明”
- content_format：paragraph 或 bullets
- content：卡片正文
```

---

## 5.2 `image_text` 内容生成规则

补充：

```text
1. lead_card 与 support_card 的内容类型应当不同。
2. 页面可根据内容选择合适卡片组合。
3. 常见组合包括：
   - 核心解释 + 关键要点
   - 核心解释 + 例子
   - 案例说明 + 启发
   - 机制说明 + 过程要点
4. 不要生成第三张文本卡片。
5. 不要把全部内容写进一整段正文。
6. visual 仅承担辅助说明作用。
7. 底部 summary_text 只保留一句总结。
```

---

## 5.3 `visual_summary` 契约改写

改为：

```text
visual_summary 页必须包含：
- title
- visual
- summary_text
```

补充：

```text
1. visual 是页面主体。
2. visual 应适合横向大图展示。
3. summary_text 只保留 1 句总结。
4. 不生成额外 summary card。
5. 不生成 takeaway 块。
```

---

# 6. `unit_spec_generators.py` 修改方案

建议重点修改：`app/generators/unit_spec_generators.py`

---

## 6.1 新增双卡片标准化逻辑

新增：

```python
normalize_image_text_cards(spec, unit, state)
```

功能：

1. 将原有 `explanation / bullet_list / example / takeaway` 等旧角色归一到：

   * `lead_card`
   * `support_card`
   * `summary_text`

2. 自动确定两张卡片的内容结构。

---

## 6.2 旧角色映射规则

建议规则：

* `explanation` → `lead_card`
* `bullet_list` → `support_card`
* `example`

  * 若 `lead_card` 已存在：映射到 `support_card`
  * 若 `lead_card` 不存在：映射到 `lead_card`
* `takeaway` → `summary_text`

---

## 6.3 自动补齐卡片

如果 `image_text` 缺少某张卡片：

### 缺 `lead_card`

优先用：

* `core_message`
* `unit.title + core_message`

### 缺 `support_card`

优先用：

* `key_points`
* 或补一个简短例子

---

## 6.4 自动确定 `display_label`

根据内容类型自动设置：

### `lead_card`

* 概念类：`核心解释`
* 案例类：`案例说明`
* 机制类：`机制说明`
* 示例类：`例子`

### `support_card`

* 要点类：`关键要点`
* 示例类：`例子`
* 启发类：`启发`
* 步骤类：`过程要点`

---

## 6.5 `visual_summary` 清理规则

对于 `visual_summary`：

* 删除多余文本块
* 仅保留：

  * `title`
  * `visual`
  * `summary_text`

---

# 7. 图片生成方案

建议重点修改：`app/services/image_generation_service.py`
以及 required element prompt 构造逻辑。

---

## 7.1 `image_text` 图片要求

目标：生成适合右侧小图嵌入的低信息密度图片。

### prompt 要求

```text
Create a low-density teaching illustration for a slide.
The image will appear in a medium-sized right-side panel.
Show one clear scene, object, metaphor, or simple action.
Use realistic illustration, hand-drawn sketch, or clean educational illustration style.
No infographic. No flowchart. No architecture diagram. No mind map.
No dense arrows. No multiple panels. No small text.
Use at most 1-3 short labels only if necessary.
The image must remain readable in a compact slide image area.
```

### 图片比例

建议：

* `4:3`

---

## 7.2 `visual_summary` 图片要求

目标：生成适合上部主展示区的宽幅结构图。

### prompt 要求

```text
Create a wide landscape summary diagram for the upper area of a teaching slide.
Use a clear framework diagram, flowchart, process diagram, or structured summary diagram.
The diagram should fit a wide horizontal canvas.
Use 3-5 major nodes and at most 2 hierarchy levels.
Use large readable labels.
Avoid dense small text, poster layout, and full PowerPoint slide screenshot.
```

### 图片比例

建议：

* `21:9`

---

# 8. Renderer 修改方案

建议重点修改：`app/renderers/slide_renderer.py`

---

## 8.1 `image_text` 新布局

### 页面结构

```text
顶部：title

左侧：两张卡片
- lead_card
- support_card

右侧：一张图片

底部：一句总结
```

---

## 8.2 `image_text` 渲染规则

### 左侧文本区

固定两张卡片：

#### 卡片 1

* 使用 `lead_card.display_label`
* 渲染 `lead_card.content`

#### 卡片 2

* 使用 `support_card.display_label`
* 渲染 `support_card.content`

### 渲染样式

建议：

* 卡片 1：浅蓝底
* 卡片 2：白底或浅灰底
* 每张卡片都有标题小标签
* 卡片间距明确

### 右侧图片区

* 单图
* 图片比例按 `4:3` 区域设计
* 不与文字区重叠

### 底部总结

* 只显示 `summary_text`
* 不加任何前缀

---

## 8.3 `visual_summary` 新布局

### 页面结构

```text
顶部：title
中上部：大图
底部：一句总结
```

### 渲染规则

* visual 占主要空间
* summary_text 放底部单行区域
* 不渲染右侧总结卡
* 不渲染 takeaway bar

---

## 8.4 删除固定前缀逻辑

删除或修改以下逻辑：

* `_takeaway_bar()` 中的 `"核心点："`

建议改为统一函数：

```python
_summary_bar(text)
```

仅输出文本内容本身。

---

# 9. Validator 修改方案

建议重点修改：`app/workflows/nodes/validator_node.py`

---

## 9.1 规则校验

### `image_text` 校验项

1. 是否包含：

   * title
   * lead_card
   * support_card
   * summary_text
   * visual

2. 是否只有两张文本卡片

3. `lead_card` 和 `support_card` 的 `display_label` 是否存在

4. `summary_text` 是否超过长度限制

5. 是否还残留旧式 `takeaway` 前缀内容

---

## 9.2 `visual_summary` 校验项

1. 是否包含：

   * title
   * visual
   * summary_text

2. 是否没有多余文本卡片

3. 是否没有右侧总结卡逻辑遗留

4. 是否没有 `核心点：` 前缀

---

# 10. LLM Review 质量检查

建议保留 `review_unit_spec` 和 `review_rendered_slide` 两级质量校对。

---

## 10.1 spec review 重点

检查：

1. 两张文本卡片内容是否有区分度
2. 卡片标题是否贴合内容
3. 页面是否过空或过满
4. summary_text 是否重复前文

---

## 10.2 render review 重点

检查：

1. 页面是否具备明确层次
2. 两张卡片和图片是否形成均衡布局
3. `image_text` 图片是否仍然过于复杂
4. `visual_summary` 图片是否足够突出
5. 底部总结是否简洁自然

---

# 11. P0 / P1 实施顺序

## P0

1. 修改 `slide.py`

   * role 改为 `lead_card / support_card / summary_text / visual`

2. 修改 `slide_deck_spec.md`

   * 重写两种 layout 契约

3. 修改 `unit_spec_generators.py`

   * 新增双卡片归一化逻辑
   * `visual_summary` 只保留主图 + 总结

4. 修改 `image_generation_service.py`

   * 收紧 `image_text` 图片 prompt
   * 强化 `visual_summary` 宽图 prompt

5. 修改 `slide_renderer.py`

   * `image_text` 改成双卡片 + 单图
   * `visual_summary` 改成大图 + 底部一句总结
   * 去掉“核心点：”

6. 修改 `validator_node.py`

   * 补充新结构校验

---

## P1

1. 加强 `review_unit_spec_node.py`

   * 检查两张卡片内容区分度

2. 加强 `review_rendered_slide_node.py`

   * 检查主图是否可读、卡片是否层次清楚

3. 增加重复内容消解

   * summary 与卡片内容重复时自动压缩或改写

---

# 12. 修改后的页面预期

## `image_text`

```text
标题
------------------------------------------------

左侧：
[卡片 1：核心解释 / 案例说明 / 机制说明]
[卡片 2：关键要点 / 例子 / 启发]

右侧：
[一张中等尺寸示意图]

底部：
[一句总结]
```

---

## `visual_summary`

```text
标题
------------------------------------------------

[上方大幅横向结构图]

[底部一句总结]
```

---

