从你现在的截图看，问题已经不再是“能不能渲染”，而是 **spec 生成策略 + renderer 版式策略同时偏保守**：

1. **页面太死板**：每页几乎都是“顶部标题 + 三张灰卡 + 底部核心点”，缺少版式变化。
2. **图片太少**：现在 prompt 过度强调“不要每页都加图”，导致模型只在极少页面声明 image。
3. **文字被截断**：renderer 的文本框高度固定，且 prompt 没有限制每个文本块长度。
4. **图片被截断**：图片框比例与生成图片比例不一致，且容器较小，容易裁切。
5. **内容块过多但每块太满**：三张卡片每张都塞较长段落，视觉上像被裁掉的讲义。

我的建议是：**先改 prompt，让 spec 更适合 PPT；再微调 renderer 的布局规则。**

---

# 一、先给你一版优化后的 slide spec prompt

这版可以直接替换 `backend/app/prompts/generator/slide_deck_spec.md`。
重点变化是：

* 图片改为“多数页面使用”，但不是每页强制。
* mindmap 继续极低频。
* 限制每个文本块字数，避免截断。
* 强制页面版式多样化。
* 明确不同 slide 类型该怎么排版。
* 要求文字“精炼但有内容”，不是一句话，也不是长段落。
* 明确普通教学 PPT 的推荐结构。

---

````md
# Slide Deck Unit Spec Generator

你是内容生成 Agent 中负责生成单页 PPT 规格的生成器。  
你的任务是：基于当前 outline unit、检索结果和生成参数，生成 **一个 `SlideSpecPage`**。

输出必须是 **合法 JSON**，并且能够通过后端 `SlideSpecPage` schema 校验。  
不要输出 Markdown 代码块，不要输出解释文字。

---

## 一、总体目标

生成的 slide spec 应接近真实课堂教学 PPT 或汇报 PPT，而不是“标题 + 一句话 + 固定卡片”的模板页。

每页 PPT 必须：
- 聚焦一个核心信息
- 内容精炼但不空洞
- 页面结构有层次
- 根据内容选择合适版式
- 多数普通内容页应配一张辅助图片
- 只有少数概念解释页、总结页或对比页可以不配图
- mindmap 只在极少数结构总览页使用

---

## 二、页面内容原则

### 1. 一页一个核心信息
每页只讲一个主要观点。  
`core_message` 必须是一句完整判断，说明这页最希望观众记住什么。

### 2. 页面正文要“短而有内容”
PPT 不是讲义，不要生成长段落。  
页面上的文字应当适合直接展示：

- 每个文本块控制在 1~3 行
- 每个要点控制在 20~45 个中文字符
- 每页正文总字数建议控制在 120~220 个中文字符
- 更详细解释放入 `speaker_notes`

不要生成大段连续文字。  
不要在一个卡片里塞入多个复杂概念。

### 3. 每页应包含 2~4 个信息块
根据内容需要，组合以下信息块：

- 核心解释
- 关键要点
- 例子
- 对比
- 案例
- 小结
- 图示说明
- takeaway

不要所有页面都生成三个灰色卡片。  
不同页面应有不同的信息组织方式。

---

## 三、图片与思维导图策略

### 1. 图片使用策略

如果 `generation_options.include_images` 为 true，通常应优先考虑为页面声明一张 image。

推荐使用图片的页面：
- 案例页
- 技术演化页
- 概念引入页
- 机制说明页
- 架构说明页
- 场景说明页
- 应用说明页
- 观点论证页
- 非纯定义类页面

可以不使用图片的页面：
- 纯概念定义页
- 简单对比页
- 小节总结页
- 封面页
- 需要用 summary-cards 表达的并列要点页

整体要求：
- 一套 slide deck 中，大约 60%~80% 的普通内容页应包含一张 image
- 不要每页都用图片，但也不要只在一两页使用图片
- 一页最多声明一个 image
- 图片应是页面中的局部视觉资产，不是整页 PPT

图片 instruction 必须说明：
- 画面主体
- 视觉形式：概念图、流程图、场景图、架构图、时间线、对比图、案例图等
- 需要强调的信息
- 是否需要少量标签
- 避免生成完整 PPT 页面、标题栏、页脚、大段文字、复杂表格

### 2. 思维导图使用策略

mindmap 在 PPT 中是极低频元素。

只有在以下页面才允许使用 mindmap：
- 知识框架总览
- 章节结构总览
- 分类体系
- 总结复盘页

普通内容页、案例页、定义页、机制页、图文页不要使用 mindmap。

如果 image 和 mindmap 都可用：
- 普通页面优先 image
- 结构总览页才考虑 mindmap
- 默认不要在同一页同时使用 image 和 mindmap

---

## 四、版式选择规则

必须根据页面内容选择 layout，避免整套 PPT 版式重复。

### 1. `cover`
仅用于第 1 页或明确封面页。  
适合：
- 课程导入
- 主题开场
- 大章节开场

### 2. `section-divider`
仅用于章节分隔或阶段过渡。  
内容应非常简洁。

### 3. `title-content`
适合：
- 纯概念解释
- 简短定义
- 小结页
- 不需要图片的说明页

页面结构建议：
- 标题
- 1 个核心解释块
- 2~3 个短要点
- 底部 takeaway

### 4. `title-content-visual`
适合：
- 左侧文字、右侧图片
- 上方标题、中部图文组合
- 需要图片辅助理解的普通教学页

页面结构建议：
- 标题
- 1 个核心解释块
- 2 个短要点
- 1 张图片
- 1 句 takeaway

### 5. `visual-left-content-right`
适合：
- 案例页
- 历史事件页
- 产品 / 系统 / 人物 / 实验页
- 图片是页面主要信息入口的页面

页面结构建议：
- 左侧图片
- 右侧 2~3 个短文本块
- 底部 takeaway

### 6. `summary-cards`
适合：
- 3 个并列概念
- 3 个特征
- 3 个阶段
- 3 个结论
- 简单对比

页面结构建议：
- 3 张卡片，每张卡片只包含一个标题和 1~2 条短句
- 不要在卡片中写长段落
- 可以不使用图片

---

## 五、元素生成规则

`elements` 中必须包含：
- 一个标题文本元素：`metadata.role = "title"`
- 至少一个主体文本元素：`metadata.role = "body"`

可以根据需要加入以下文本元素：

- `metadata.role = "bullet-list"`：用于 2~4 个短要点
- `metadata.role = "example"`：用于具体例子
- `metadata.role = "comparison"`：用于对比说明
- `metadata.role = "callout"`：用于强调重点
- `metadata.role = "caption"`：用于图片说明
- `metadata.role = "takeaway"`：用于底部结论
- `metadata.role = "note"`：用于补充说明

### 文本长度限制

为了避免前端渲染截断，必须严格控制文字长度：

- title：不超过 22 个中文字符，必要时使用副标题放入其他元素
- core_message：不超过 45 个中文字符
- body：不超过 80 个中文字符
- bullet-list：最多 4 条，每条不超过 35 个中文字符
- example：不超过 70 个中文字符
- callout：不超过 50 个中文字符
- takeaway：不超过 55 个中文字符
- caption：不超过 35 个中文字符

如果内容复杂，把详细解释写入 `speaker_notes`，不要塞进页面元素。

---

## 六、视觉元素声明规则

如果需要图片：
- 在 `elements` 中加入一个 `element_ref`
- `metadata.role = "visual"`
- `metadata.placement = "primary"`
- 在 `required_elements` 中声明对应 image

图片 required element 要求：
- `type = "image"`
- `purpose` 说明图片服务于哪一个教学目标
- `instruction` 必须描述局部视觉资产
- `aspect_ratio` 建议为 `4:3` 或 `16:9`
- `style` 建议使用清爽教学插画、简洁概念图、真实案例图风格等

如果需要 mindmap：
- 在 `elements` 中加入一个 `element_ref`
- `metadata.role = "mindmap"`
- `metadata.placement = "supporting"`
- `metadata.downgrade = "text"`
- 在 `required_elements` 中声明对应 mindmap

---

## 七、layout_hints 要求

`layout_hints` 必须包含：

```json
{
  "density": "light" | "balanced" | "rich",
  "supported_renderer": "scenekit.slide/v1"
}
````

可额外包含：

```json
{
  "content_pattern": "concept" | "case" | "comparison" | "process" | "summary" | "visual_explanation",
  "body_structure": "single-explanation" | "two-column" | "three-cards" | "image-with-points" | "case-brief",
  "primary_visual": "image element id when image is declared",
  "secondary_visual": "mindmap element id when mindmap is declared"
}
```

`density` 选择规则：

* `light`：封面、章节页、简短定义页
* `balanced`：普通教学页
* `rich`：案例页、机制页、综合说明页

---

## 八、speaker_notes 要求

`speaker_notes` 应提供比页面更完整的讲解。
它可以包含：

* 页面核心观点的展开解释
* 课堂讲解顺序
* 示例补充
* 与前后页的衔接
* 可口头讲解但不适合放在页面上的细节

不要把 speaker_notes 写得过短。
建议 100~200 个中文字符。

---

## 九、质量检查

生成前请检查：

1. 页面是否只讲一个核心信息？
2. 页面是否不是固定三卡片模板？
3. 如果 include_images=true，这页是否适合放一张图片？
4. 如果没有图片，是否有充分理由？
5. 是否误用了 mindmap？
6. 每个文本块是否足够短，避免渲染截断？
7. 页面正文是否不是长段讲义？
8. speaker_notes 是否承接了详细解释？
9. required_elements 与 element_ref 是否一一对应？
10. layout_hints.supported_renderer 是否等于 `"scenekit.slide/v1"`？

---

## 十、输入

* unit_spec_id: {unit_spec_id}
* outline_unit: {outline_unit}
* retrieval_results: {retrieval_results}
* generation_options: {generation_options}

````

---

# 二、同时建议修改 renderer 的几个关键点

你说“不用给补丁，给详细修改意见”，那我按你当前渲染问题逐条给。

---

## 1）不要把 `summary-cards` 当成默认安全布局

你现在几乎每页都像 `summary-cards`。  
原因通常有两个：

- prompt 倾向于生成多个文本元素
- renderer 对多个文本块的默认处理方式就是卡片化

建议改成：

```python
def _choose_render_pattern(slide):
    layout = slide.layout
    pattern = slide.layout_hints.get("content_pattern")

    if layout == "summary-cards":
        return "cards"

    if layout in {"title-content-visual", "visual-left-content-right"}:
        return "visual"

    if pattern in {"case", "visual_explanation", "process"}:
        return "visual"

    if pattern == "comparison":
        return "comparison"

    return "content"
````

核心思想：
**只有 layout 明确是 `summary-cards` 时，才渲染成三卡片。**

普通 `title-content` 不要渲染成卡片墙，而是渲染成：

* 一个主说明块
* 一个短列表
* 一个底部结论条

---

## 2）视觉页要优先给图片留大空间

现在第 4 张图的图片太小，而且外面灰框很大，视觉上像“缩在盒子里”。

建议：

### `title-content-visual`

采用左文右图：

```text
标题
分隔线

左侧：核心解释 + 2~3 个要点
右侧：图片，占页面 35%~40%

底部：takeaway
```

建议坐标：

```python
TEXT_LEFT = 64
TEXT_TOP = 170
TEXT_WIDTH = 500

IMAGE_LEFT = 620
IMAGE_TOP = 165
IMAGE_WIDTH = 280
IMAGE_HEIGHT = 210

TAKEAWAY_LEFT = 88
TAKEAWAY_TOP = 455
TAKEAWAY_WIDTH = 780
TAKEAWAY_HEIGHT = 52
```

不要把图片放进太厚的灰色容器。
可以只给图片本身加圆角和阴影。

---

## 3）`visual-left-content-right` 应该让图片更大

如果是案例页或图解页，图片应该成为主视觉。
建议：

```python
IMAGE_LEFT = 60
IMAGE_TOP = 160
IMAGE_WIDTH = 390
IMAGE_HEIGHT = 245

TEXT_LEFT = 500
TEXT_TOP = 155
TEXT_WIDTH = 380
```

也就是说，图片不要只有 300×168，至少应接近 390×245。
这会更像你给的 AlphaGo 示例页。

---

## 4）减少文本框固定高度导致的截断

现在截断明显是因为：

* 卡片高度固定
* 字体偏大
* 行高偏大
* 文本没有按长度动态分配高度

建议增加一个简单的文本高度估算函数：

```python
def _estimate_text_height(text: str, font_size: int, width: int, line_height: float = 1.25) -> int:
    # 粗略估算：中文每个字约占 font_size 宽度，英文略窄
    chars_per_line = max(8, int(width / (font_size * 0.95)))
    line_count = max(1, math.ceil(len(_plain_text(text)) / chars_per_line))
    return int(line_count * font_size * line_height + 16)
```

然后卡片高度不要写死，而是：

```python
height = min(max(_estimate_text_height(content, 18, card_width), 72), 140)
```

如果内容超过最大高度，要在 renderer 层做截断：

```python
def _truncate_text(text: str, max_chars: int) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 1].rstrip() + "…"
```

建议按 role 控制：

```python
ROLE_LIMITS = {
    "body": 90,
    "bullet-list": 120,
    "example": 80,
    "comparison": 90,
    "callout": 70,
    "takeaway": 60,
    "caption": 40,
}
```

这样即使 LLM 偶尔生成过长内容，也不会前端直接裁掉。

---

## 5）卡片数量不要超过 3，且每张卡片文字要短

现在前三页都是三张卡片，但每张卡片放了长文本，所以必然截断。

建议 renderer 中：

```python
cards = content_blocks[:3]
```

每个卡片渲染时：

```python
title = block.title or role_name
content = _truncate_text(block.content, 55)
```

卡片内只显示：

* 一个小标题
* 一到两句短文本

详细内容给 speaker_notes，不要在卡片里展示。

---

## 6）新增几种版式，避免页面太死板

你现在基本只有一种“卡片 + takeaway”。建议 renderer 内部不用改 schema，只根据 layout / hints 生成不同模板。

### 模板 A：概念解释页

适合 `title-content`

```text
标题
分隔线

左侧大解释块
右侧 2 个要点小块

底部 takeaway
```

---

### 模板 B：图文说明页

适合 `title-content-visual`

```text
标题
分隔线

左侧：核心解释 + 要点列表
右侧：图片

底部 takeaway
```

---

### 模板 C：案例页

适合 `visual-left-content-right`

```text
标题
分隔线

左侧：大图
右侧：案例背景 / 发生了什么 / 意义

底部结论
```

---

### 模板 D：三卡总结页

适合 `summary-cards`

```text
标题
分隔线

三张卡片
每张卡片：标题 + 1~2 句

底部 takeaway
```

---

### 模板 E：章节过渡页

适合 `section-divider`

```text
大标题
一句核心问题 / 核心判断
小装饰线
```

---

## 7）图片渲染应使用 contain，不要裁掉主体

你上传的前端格式如果 image 元素没有 `objectFit` 字段，就只能通过宽高控制。

建议：

* 图片生成 instruction 统一要求“主体居中，四周留白，避免贴边”
* renderer 给图片容器用 4:3 或 16:9 固定比例
* 不要把图片框做得太扁

推荐：

* `title-content-visual`：`280 x 210`，比例 4:3
* `visual-left-content-right`：`390 x 245`，比例接近 16:10
* 避免 `270 x 152` 这种太小的图片框

---

## 8）去掉过重灰色背景

现在所有内容块都是灰底，导致页面看起来像表单组件，不像 PPT。

建议：

* 主说明块可以用浅灰或浅蓝
* 普通 bullet 列表不要都加灰底
* takeaway 可用浅蓝条或仅用加粗文字
* 图片外框不要大面积灰底

比如：

```python
BODY_FILL = "#F8FAFC"
CARD_FILL = "#F1F5F9"
TAKEAWAY_FILL = "#E0F2FE"
```

但不要所有区域都同一种灰。

---

## 9）标题区可以保留，但减少顶部空间浪费

你现在标题很大，顶部区域占用偏多，正文只能往下挤。

建议：

* title font size 从 36~40 降到 32~34
* subtitle badge 可以保留，但不要占太多高度
* divider top 控制在 130 左右
* 正文从 160 左右开始

---

# 三、最推荐的 renderer 修改方向

按优先级来：

## 优先级 1：修复截断

必须做：

```python
_truncate_text()
_estimate_text_height()
按 role 限制文本长度
卡片高度动态调整或减少内容
```

这是最影响可用性的。

---

## 优先级 2：提高图片使用空间

必须做：

```python
title-content-visual: 图片右侧大图
visual-left-content-right: 左侧大图
图片框至少 280x210 或 390x245
```

这会立刻改善“图片太少且太小”的视觉问题。

---

## 优先级 3：减少固定三卡模板

必须做：

```python
只有 summary-cards 使用三卡片
title-content 使用解释块 + 要点块
title-content-visual 使用左文右图
visual-left-content-right 使用大图 + 右侧说明
```

这会解决“每页都一个样”的问题。

---

# 四、我建议你下一轮生成效果的目标

比较合理的结果应该是：

* 第 1 页：封面 / 导入页，可以无图或大背景图
* 第 2 页：概念解释页，可以无图，用定义 + 对比 + takeaway
* 第 3 页：图文页，右侧一张多模态概念图
* 第 4 页：架构页，右侧或左侧一张架构图
* 第 5 页：案例页，大图 + 右侧解释
* 第 6 页：总结页，三卡片或简洁总结，不一定有图

也就是说，不是“每页都有图”，而是：

```text
概念页可无图
普通内容页大多有图
案例/机制/架构页必须尽量有图
总结页可无图
mindmap 极少出现
```

---

# 五、最终建议

这次建议你同时做两步：

1. **先替换上面的新版 prompt**
   解决图片比例、文字长度、页面结构问题。

2. **再按我上面的 renderer 修改意见优化布局**
   重点改：

   * 截断保护
   * 图片框大小
   * layout 对应模板
   * 不要默认三卡片

这样改完，生成结果会明显从“组件化卡片页”接近“真实教学 PPT 页”。
