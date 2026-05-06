import { FormEvent, useState } from "react";

import { useContentGenerationStore } from "../../stores/contentGenerationStore";
import type { ContentGenerationRequest, ExportType, MvpContentType } from "../../types/content";

const defaultPrompt = "生成一份适合本科一年级学生学习的多模态讲义。";

export function ContentGenerationForm() {
  // TODO(MVP-form): Expand generation controls for audience, difficulty,
  // slide count/duration, image style, PDF options, and slide theme options.
  const submitTask = useContentGenerationStore((state) => state.submitTask);
  const loading = useContentGenerationStore((state) => state.loading);
  const [contentType, setContentType] = useState<MvpContentType>("lecture");
  const [topic, setTopic] = useState("人工智能基础导论");
  const [userPrompt, setUserPrompt] = useState(defaultPrompt);
  const [knowledgeBaseId, setKnowledgeBaseId] = useState("kb_ai_basic");
  const [includeImages, setIncludeImages] = useState(true);
  const [includeCharts, setIncludeCharts] = useState(true);
  const [includeMindmap, setIncludeMindmap] = useState(true);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const outputFormats: ExportType[] = contentType === "slide_deck" ? ["preview", "slide_json"] : ["preview", "pdf"];
    const request: ContentGenerationRequest = {
      content_type: contentType,
      topic,
      user_prompt: userPrompt,
      system_prompt: "内容准确、结构清晰、适合教学。",
      knowledge_base_ids: knowledgeBaseId.trim() ? [knowledgeBaseId.trim()] : [],
      output_formats: outputFormats,
      generation_options: {
        language: "zh-CN",
        difficulty: "introductory",
        style: "educational",
        include_images: includeImages,
        include_charts: includeCharts,
        include_mindmap: includeMindmap
      }
    };
    await submitTask(request);
  }

  return (
    <form className="generation-form" onSubmit={handleSubmit}>
      <label>
        内容类型
        <select value={contentType} onChange={(event) => setContentType(event.target.value as MvpContentType)}>
          <option value="lecture">讲义</option>
          <option value="slide_deck">Slide Deck</option>
        </select>
      </label>

      <label>
        主题
        <input value={topic} onChange={(event) => setTopic(event.target.value)} />
      </label>

      <label>
        用户 Prompt
        <textarea rows={5} value={userPrompt} onChange={(event) => setUserPrompt(event.target.value)} />
      </label>

      <label>
        知识库 ID
        <input value={knowledgeBaseId} onChange={(event) => setKnowledgeBaseId(event.target.value)} />
      </label>

      <fieldset>
        <legend>生成配置</legend>
        <label className="checkbox-row">
          <input type="checkbox" checked={includeImages} onChange={(event) => setIncludeImages(event.target.checked)} />
          图片
        </label>
        <label className="checkbox-row">
          <input type="checkbox" checked={includeCharts} onChange={(event) => setIncludeCharts(event.target.checked)} />
          图表
        </label>
        <label className="checkbox-row">
          <input type="checkbox" checked={includeMindmap} onChange={(event) => setIncludeMindmap(event.target.checked)} />
          思维导图
        </label>
      </fieldset>

      <button type="submit" disabled={loading}>
        {loading ? "生成中" : "创建生成任务"}
      </button>
    </form>
  );
}
