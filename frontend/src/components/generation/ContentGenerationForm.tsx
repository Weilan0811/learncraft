import { FormEvent, useState } from "react";

import { useContentGenerationStore } from "../../stores/contentGenerationStore";
import type {
  ContentGenerationRequest,
  Difficulty,
  GenerationOptions,
  MvpContentType,
  OutputDepth
} from "../../types/content";
import { LineIcon, type IconName } from "./icons";

interface Draft {
  topic: string;
  prompt: string;
  systemPrompt: string;
}

const defaultsByType: Record<MvpContentType, Draft> = {
  lecture: {
    topic: "人工智能基础导论",
    prompt: "生成一份适合本科一年级学生学习的多模态讲义。",
    systemPrompt: "内容准确、结构清晰、适合教学。"
  },
  slide_deck: {
    topic: "人工智能基础导论",
    prompt: "生成一份适合课堂展示的 Slide Deck，重点突出概念、结构和讲解顺序。",
    systemPrompt: "内容准确、结构清晰、适合课堂展示。"
  },
  social_post: {
    topic: "AI Agent 工作流的设计与实践",
    prompt: "围绕给定主题生成一篇适合微信公众号发布的知识技术型推文，要求结构清晰、有问题链、有判断，并适合手机端阅读。",
    systemPrompt: "内容准确、表达自然、结构清晰，适合微信公众号读者阅读。"
  },
  podcast_script: {
    topic: "AI Agent 工作流的设计与实践",
    prompt: "根据给定内容生成一段适合中文 TTS 播放的双人播客对话，要求 Person1/Person2 自然来回交流，保留清晰观点推进，并包含一次温和追问。",
    systemPrompt: "内容准确、表达自然、节奏适合收听。"
  },
  interactive_html: {
    topic: "生成式 AI 如何理解你的问题？",
    prompt: "生成一份面向初学者的互动式 HTML 课程，包含讲解、互动练习和对话式教学引导。",
    systemPrompt: "内容准确、结构清晰、适合互动式学习。"
  }
};

const contentTypeMeta: Array<{ value: MvpContentType; label: string; icon: IconName }> = [
  { value: "lecture", label: "讲义", icon: "book" },
  { value: "slide_deck", label: "幻灯片", icon: "presentation" },
  { value: "social_post", label: "图文推文", icon: "article" },
  { value: "podcast_script", label: "播客文稿", icon: "mic" },
  { value: "interactive_html", label: "互动讲义", icon: "interactive" }
];

const styleByType: Record<MvpContentType, string> = {
  lecture: "educational",
  slide_deck: "classroom_slide",
  social_post: "wechat_technical_article",
  podcast_script: "chinese_podcast_dialogue",
  interactive_html: "interactive_lesson"
};

function createDrafts(): Record<MvpContentType, Draft> {
  return {
    lecture: { ...defaultsByType.lecture },
    slide_deck: { ...defaultsByType.slide_deck },
    social_post: { ...defaultsByType.social_post },
    podcast_script: { ...defaultsByType.podcast_script },
    interactive_html: { ...defaultsByType.interactive_html }
  };
}

export function ContentGenerationForm() {
  const submitTask = useContentGenerationStore((state) => state.submitTask);
  const loading = useContentGenerationStore((state) => state.loading);
  const [contentType, setContentType] = useState<MvpContentType>("lecture");
  const [drafts, setDrafts] = useState<Record<MvpContentType, Draft>>(createDrafts);
  const [language, setLanguage] = useState("zh-CN");
  const [difficulty, setDifficulty] = useState<Difficulty>("introductory");
  const [outputDepth, setOutputDepth] = useState<OutputDepth>("standard");
  const [sectionCount, setSectionCount] = useState(4);
  const [slideCount, setSlideCount] = useState(8);

  const draft = drafts[contentType];
  const canSubmit = Boolean(draft.topic.trim() && draft.prompt.trim()) && !loading;

  function updateDraft(patch: Partial<Draft>) {
    setDrafts((previous) => ({
      ...previous,
      [contentType]: { ...previous[contentType], ...patch }
    }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) {
      return;
    }
    const generationOptions: GenerationOptions = {
      language,
      difficulty,
      style: styleByType[contentType],
      output_depth: outputDepth,
      citation_policy: "none",
      speaker_notes: contentType === "slide_deck",
      ...(contentType === "lecture"
        ? { section_count: sectionCount, max_section_count: sectionCount }
        : {}),
      ...(contentType === "slide_deck" ? { slide_count: slideCount, max_slide_count: slideCount } : {})
    };
    const request: ContentGenerationRequest = {
      content_type: contentType,
      topic: draft.topic.trim(),
      user_prompt: draft.prompt.trim(),
      system_prompt: draft.systemPrompt,
      generation_options: generationOptions
    };
    await submitTask(request);
  }

  return (
    <form className="generation-form" onSubmit={handleSubmit}>
      <section className="config-section">
        <div className="section-heading">
          <LineIcon name="layers" size={16} />
          <div>
            <h2>内容类型</h2>
            <p>选择要生成的内容形式。</p>
          </div>
        </div>
        <div className="content-type-grid" role="radiogroup" aria-label="内容类型">
          {contentTypeMeta.map((item) => (
            <button
              type="button"
              role="radio"
              aria-checked={contentType === item.value}
              className={`content-type-card${contentType === item.value ? " is-active" : ""}`}
              onClick={() => setContentType(item.value)}
              key={item.value}
            >
              <LineIcon name={item.icon} size={15} />
              <span>{item.label}</span>
            </button>
          ))}
        </div>
      </section>

      <section className="config-section">
        <div className="section-heading">
          <LineIcon name="pencil" size={16} />
          <div>
            <h2>主题</h2>
            <p>填写内容的核心主题。</p>
          </div>
        </div>
        <input
          className="text-input"
          aria-label="主题"
          value={draft.topic}
          placeholder={`例如：${defaultsByType[contentType].topic}`}
          onChange={(event) => updateDraft({ topic: event.target.value })}
        />
      </section>

      <section className="config-section">
        <div className="section-heading">
          <LineIcon name="fileText" size={16} />
          <div>
            <h2>生成要求</h2>
            <p>说明具体内容、受众、重点与结构。</p>
          </div>
        </div>
        <textarea
          className="text-area"
          aria-label="生成要求"
          rows={7}
          value={draft.prompt}
          placeholder="描述目标读者、内容重点和希望采用的结构。"
          onChange={(event) => updateDraft({ prompt: event.target.value })}
        />
      </section>

      <details className="advanced-settings">
        <summary>
          <span className="summary-label">
            <LineIcon name="sliders" size={16} />
            <span>
              <strong>高级设置</strong>
              <small>语言、难度与篇幅</small>
            </span>
          </span>
          <LineIcon name="chevronDown" size={16} className="summary-chevron" />
        </summary>
        <div className="settings-grid">
          <label className="compact-field">
            <span>语言</span>
            <select value={language} onChange={(event) => setLanguage(event.target.value)}>
              <option value="zh-CN">中文</option>
              <option value="en-US">English</option>
            </select>
          </label>
          <label className="compact-field">
            <span>难度</span>
            <select
              value={difficulty}
              onChange={(event) => setDifficulty(event.target.value as Difficulty)}
            >
              <option value="introductory">入门</option>
              <option value="intermediate">进阶</option>
              <option value="advanced">高级</option>
            </select>
          </label>
          <label className="compact-field">
            <span>篇幅</span>
            <select
              value={outputDepth}
              onChange={(event) => setOutputDepth(event.target.value as OutputDepth)}
            >
              <option value="brief">简要</option>
              <option value="standard">标准</option>
              <option value="detailed">详细</option>
            </select>
          </label>
          {contentType === "lecture" ? (
            <label className="compact-field">
              <span>章节</span>
              <select
                value={sectionCount}
                onChange={(event) => setSectionCount(Number(event.target.value))}
              >
                {[2, 3, 4, 5, 6, 7, 8].map((count) => (
                  <option value={count} key={count}>
                    {count} 节
                  </option>
                ))}
              </select>
            </label>
          ) : null}
          {contentType === "slide_deck" ? (
            <label className="compact-field">
              <span>页数</span>
              <select
                value={slideCount}
                onChange={(event) => setSlideCount(Number(event.target.value))}
              >
                {[4, 6, 8, 10, 12].map((count) => (
                  <option value={count} key={count}>
                    {count} 页
                  </option>
                ))}
              </select>
            </label>
          ) : null}
        </div>
        {contentType === "slide_deck" ? (
          <p className="settings-hint">幻灯片会同时生成演讲者备注。</p>
        ) : null}
      </details>

      <p className="knowledge-note">
        <LineIcon name="info" size={14} />
        <span>当前未接入知识库，生成内容不会引用外部资料。</span>
      </p>

      <button type="submit" className="primary-action" disabled={!canSubmit}>
        <LineIcon name={loading ? "clock" : "play"} size={16} />
        {loading ? "正在创建任务…" : "开始生成"}
      </button>
    </form>
  );
}
