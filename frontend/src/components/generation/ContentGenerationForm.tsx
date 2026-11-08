import { FormEvent, useState } from "react";

import { useContentGenerationStore } from "../../stores/contentGenerationStore";
import type { ContentGenerationRequest, MvpContentType } from "../../types/content";

const defaultsByType: Record<MvpContentType, { topic: string; prompt: string; systemPrompt: string }> = {
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
    prompt: "根据给定内容生成一段适合中文 TTS 播放的双人播客对话，要求 Person1/Person2 自然来回交流，并保留清晰观点推进。",
    systemPrompt: "内容准确、表达自然、节奏适合收听。"
  },
  interactive_html: {
    topic: "生成式 AI 如何理解你的问题？",
    prompt: "生成一份面向初学者的互动式 HTML 课程，包含讲解、互动练习和对话式教学引导。",
    systemPrompt: "内容准确、结构清晰、适合互动式学习。"
  }
};

export function ContentGenerationForm() {
  const submitTask = useContentGenerationStore((state) => state.submitTask);
  const loading = useContentGenerationStore((state) => state.loading);
  const [contentType, setContentType] = useState<MvpContentType>("lecture");
  const [topic, setTopic] = useState(defaultsByType.lecture.topic);
  const [userPrompt, setUserPrompt] = useState(defaultsByType.lecture.prompt);
  const [knowledgeBaseId, setKnowledgeBaseId] = useState("kb_ai_basic");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const request: ContentGenerationRequest = {
      content_type: contentType,
      topic,
      user_prompt: userPrompt,
      system_prompt: defaultsByType[contentType].systemPrompt,
      knowledge_base_ids: knowledgeBaseId.trim() ? [knowledgeBaseId.trim()] : [],
      generation_options: {
        language: "zh-CN",
        difficulty: "introductory",
        style: contentType === "social_post" ? "wechat_technical_article" : contentType === "podcast_script" ? "chinese_podcast_dialogue" : "educational",
        output_depth: "standard",
        citation_policy: "light",
        speaker_notes: contentType === "slide_deck"
      }
    };
    await submitTask(request);
  }

  function handleContentTypeChange(nextType: MvpContentType) {
    setContentType(nextType);
    setTopic(defaultsByType[nextType].topic);
    setUserPrompt(defaultsByType[nextType].prompt);
  }

  return (
    <form className="generation-form" onSubmit={handleSubmit}>
      <label>
        内容类型
        <select value={contentType} onChange={(event) => handleContentTypeChange(event.target.value as MvpContentType)}>
          <option value="lecture">讲义</option>
          <option value="slide_deck">Slide Deck</option>
          <option value="social_post">Social Post</option>
          <option value="podcast_script">Podcast</option>
          <option value="interactive_html">Interactive HTML</option>
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

      <button type="submit" disabled={loading}>
        {loading ? "生成中..." : "创建生成任务"}
      </button>
    </form>
  );
}
