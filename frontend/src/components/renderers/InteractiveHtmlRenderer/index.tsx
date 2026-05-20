import React, { useEffect, useState, useCallback, useRef } from "react";
import type { InteractiveHtmlRenderModel, CreateSessionResponse, SubmitEventRequest } from "../../../types/interactiveHtml";
import { createLearningSession, submitLearningEvent } from "../../../api/learningApi";

import { HeadingBlock, ParagraphBlock, ConceptCardBlock, CalloutBlock, ExampleBlock, SummaryBlock } from "./blocks/ContentBlocks";
import { AnimatedFlowBlock, CaseCompareBlock, ContextInspectorBlock, StepperBlock } from "./blocks/DisplayBlocks";
import { SingleChoiceBlock, MultipleChoiceBlock, ShortAnswerBlock, DragMatchBlock, SequenceBlock, FlashcardBlock } from "./blocks/InteractiveBlocks";
import { SocraticChatBlock, ScenarioBlock } from "./blocks/DialogueBlocks";
import "./styles.css";

interface Props {
  model: InteractiveHtmlRenderModel;
  fullscreen?: boolean;
}

type BlockType = InteractiveHtmlRenderModel["sections"][0]["render_blocks"][0];

const BLOCK_RENDERERS: Record<string, React.FC<{
  block: BlockType;
  lessonId?: string;
  sessionId?: string;
  sectionId?: string;
  onSubmitEvent?: (event: SubmitEventRequest) => void;
  onScore?: (points: number) => void;
}>> = {
  heading: HeadingBlock as any,
  paragraph: ParagraphBlock as any,
  concept_card: ConceptCardBlock as any,
  callout: CalloutBlock as any,
  example: ExampleBlock as any,
  summary: SummaryBlock as any,
  animated_flow: AnimatedFlowBlock as any,
  case_compare: CaseCompareBlock as any,
  context_inspector: ContextInspectorBlock as any,
  stepper: StepperBlock as any,
  single_choice: SingleChoiceBlock as any,
  multiple_choice: MultipleChoiceBlock as any,
  short_answer: ShortAnswerBlock as any,
  drag_match: DragMatchBlock as any,
  sequence: SequenceBlock as any,
  flashcard: FlashcardBlock as any,
  socratic_chat: SocraticChatBlock as any,
  scenario: ScenarioBlock as any,
};

/** Block types that should start a new sub-card (tall/heavy content) */
const SUB_CARD_BREAK = new Set([
  "animated_flow", "case_compare", "context_inspector", "stepper",
  "single_choice", "multiple_choice", "short_answer", "drag_match",
  "sequence", "flashcard", "socratic_chat", "scenario",
  "example", "summary",
]);

/** Check if two strings are effectively the same title */
function isSameTitle(a: string, b: string): boolean {
  const norm = (s: string) => s.trim().toLowerCase().replace(/\s+/g, "");
  const na = norm(a);
  const nb = norm(b);
  if (!na || !nb) return false;
  return na === nb || na.includes(nb) || nb.includes(na);
}

/** Remove consecutive duplicate paragraph blocks */
function dedupBlocks(blocks: BlockType[]): BlockType[] {
  const out: BlockType[] = [];
  for (const b of blocks) {
    if (b.type === "paragraph" && out.length > 0) {
      const prev = out[out.length - 1];
      const prevText = ((prev as any).block_data?.text ?? "") as string;
      const curText = ((b as any).block_data?.text ?? "") as string;
      if (prev.type === "paragraph" && prevText === curText) continue;
    }
    out.push(b);
  }
  return out;
}

/** Infer module eyebrow label from blocks, or use section order as fallback */
const MODULE_DETECT_PATTERNS: Array<{ types: string[]; label: string }> = [
  { types: ["socratic_chat"], label: "启发式多轮问答" },
  { types: ["scenario"], label: "情景教学" },
  { types: ["animated_flow"], label: "流程动画式讲解" },
  { types: ["case_compare"], label: "案例理解" },
  { types: ["flashcard", "drag_match", "sequence", "single_choice", "multiple_choice", "short_answer"], label: "综合练习模块" },
  { types: ["concept_card"], label: "知识点讲解" },
  { types: ["summary"], label: "总结回顾" },
];

function deriveEyebrow(blocks: BlockType[], sectionOrder: number, totalSections: number): string {
  const typeSet = new Set(blocks.map((b) => b.type));
  for (const pattern of MODULE_DETECT_PATTERNS) {
    if (pattern.types.some((t) => typeSet.has(t))) return pattern.label;
  }
  if (sectionOrder === 0) return "课程导入";
  if (sectionOrder === totalSections - 1) return "总结回顾";
  return "";
}

/** Split a section's blocks into sub-card groups that each fit ~1 viewport */
function splitIntoSubCards(blocks: BlockType[]): BlockType[][] {
  const pages: BlockType[][] = [];
  let current: BlockType[] = [];
  let lightCount = 0;

  for (const b of blocks) {
    const isHeavy = SUB_CARD_BREAK.has(b.type);

    if (isHeavy && current.length > 0) {
      pages.push(current);
      current = [];
      lightCount = 0;
    } else if (!isHeavy && lightCount >= 4) {
      pages.push(current);
      current = [];
      lightCount = 0;
    }

    current.push(b);
    if (!isHeavy) lightCount++;
  }

  if (current.length > 0) pages.push(current);
  return pages;
}

export const InteractiveHtmlRenderer: React.FC<Props> = ({ model, fullscreen = false }) => {
  const [session, setSession] = useState<CreateSessionResponse | null>(null);
  const [completedSections, setCompletedSections] = useState<Set<string>>(new Set());
  const [score, setScore] = useState(0);
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const sectionRefs = useRef<Map<string, HTMLElement>>(new Map());

  useEffect(() => {
    createLearningSession(model.lesson_id).then(setSession).catch(console.error);
  }, [model.lesson_id]);

  const handleSubmitEvent = useCallback(async (event: SubmitEventRequest) => {
    if (!session) return;
    try {
      await submitLearningEvent(model.lesson_id, session.session_id, event);
    } catch (err) {
      console.error("Failed to submit learning event:", err);
    }
  }, [model.lesson_id, session]);

  const addScore = useCallback((points: number) => {
    setScore((s) => s + points);
  }, []);

  // IntersectionObserver: highlight active section in sidebar
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting && entry.intersectionRatio > 0.3) {
            setActiveSection(entry.target.id);
          }
        }
      },
      { threshold: [0.3] }
    );

    const currentRefs = sectionRefs.current;
    currentRefs.forEach((el) => observer.observe(el));
    return () => {
      currentRefs.forEach((el) => observer.unobserve(el));
    };
  }, [model.sections]);

  const sections = model.sections;

  const scrollToSection = (sectionId: string) => {
    const el = sectionRefs.current.get(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  const markComplete = (sectionId: string) => {
    setCompletedSections((prev) => {
      if (prev.has(sectionId)) return prev;
      const next = new Set(prev);
      next.add(sectionId);
      return next;
    });
    addScore(5);
  };

  const progressPercent = sections.length > 0
    ? Math.round((completedSections.size / sections.length) * 100)
    : 0;

  /** Render a group of blocks with concept-card grid detection */
  const renderBlocks = (blocks: BlockType[], sectionId: string, sectionTitle?: string) => {
    const elements: React.ReactNode[] = [];
    let i = 0;

    while (i < blocks.length) {
      // Skip leading heading if it duplicates the section title
      if (i === 0 && blocks[i].type === "heading" && sectionTitle) {
        const headingText = ((blocks[i] as any).block_data?.text ?? "") as string;
        if (isSameTitle(headingText, sectionTitle)) {
          i++;
          continue;
        }
      }

      if (blocks[i].type === "concept_card") {
        const grid: BlockType[] = [];
        while (i < blocks.length && blocks[i].type === "concept_card") {
          grid.push(blocks[i]);
          i++;
        }
        const cols = grid.length === 2 ? "cols-2" : "";
        elements.push(
          <div key={`grid-${grid[0].block_id}`} className={`ih-concept-grid ${cols}`}>
            {grid.map((b) => {
              const R = BLOCK_RENDERERS[b.type];
              return R ? (
                <div key={b.block_id} className="ih-block">
                  {b.tutor_message && <div className="ih-tutor-message">{b.tutor_message}</div>}
                  <R block={b} />
                </div>
              ) : <div key={b.block_id} className="ih-unknown-block"><p>Unknown: {b.type}</p></div>;
            })}
          </div>
        );
        continue;
      }

      const b = blocks[i];
      const R = BLOCK_RENDERERS[b.type];
      if (!R) {
        elements.push(<div key={b.block_id} className="ih-unknown-block"><p>Unknown: {b.type}</p></div>);
      } else {
        elements.push(
          <div key={b.block_id} className="ih-block">
            {b.tutor_message && <div className="ih-tutor-message">{b.tutor_message}</div>}
            <R
              block={b}
              lessonId={model.lesson_id}
              sessionId={session?.session_id ?? ""}
              sectionId={sectionId}
              onSubmitEvent={handleSubmitEvent}
              onScore={addScore}
            />
          </div>
        );
      }
      i++;
    }
    return elements;
  };

  /** Render a section's blocks split into viewport-sized sub-cards */
  const renderSectionBlocks = (blocks: BlockType[], sectionId: string, sectionTitle: string) => {
    const deduped = dedupBlocks(blocks);
    const subCards = splitIntoSubCards(deduped);
    return subCards.map((subBlocks, idx) => (
      <div key={`subcard-${sectionId}-${idx}`} className="ih-sub-card">
        {renderBlocks(subBlocks, sectionId, idx === 0 ? sectionTitle : undefined)}
      </div>
    ));
  };

  // ---- Sidebar ----
  const sidebar = (
    <aside className="ih-sidebar">
      <div className="ih-brand">
        <div className="ih-logo">AI</div>
        <div>
          <h1 className="ih-brand__title">{model.title}</h1>
          <p className="ih-brand__subtitle">互动式课程</p>
        </div>
      </div>
      <div className="ih-nav-title">课程目录</div>
      <nav className="ih-nav">
        {sections.map((section, i) => {
          const navEyebrow = i === 0 ? "课程封面" : deriveEyebrow(section.render_blocks, i, sections.length);
          return (
          <button
            key={section.section_id}
            className={`ih-nav__link ${section.section_id === activeSection ? "active" : ""} ${completedSections.has(section.section_id) ? "done" : ""}`}
            onClick={() => scrollToSection(section.section_id)}
          >
            <span className="ih-nav__dot" />
            <span className="ih-nav__label">{navEyebrow || section.title}</span>
            {completedSections.has(section.section_id) && <span className="ih-nav__check">&#10003;</span>}
          </button>
          );
        })}
      </nav>
      <div className="ih-progress-card">
        <strong>学习进度</strong>
        <div className="ih-progress-bar"><span style={{ width: `${progressPercent}%` }} /></div>
        <p className="ih-progress-text">已完成 {progressPercent}%</p>
        <div className="ih-score-pill">互动积分 {score}</div>
      </div>
    </aside>
  );

  // ---- Main ----
  return (
    <div className={`ih-app${fullscreen ? " ih-app--fullscreen" : ""}`}>
      {sidebar}

      <main className="ih-main">
        {/* Hero card */}
        <section
          id={sections[0]?.section_id}
          ref={(el) => { if (el && sections[0]) sectionRefs.current.set(sections[0].section_id, el); }}
          className="ih-module-card ih-module-card--hero"
        >
          <div className="ih-hero-inner">
            <div className="ih-hero-text">
              <div className="ih-eyebrow">课程封面 &middot; 共 {sections.length} 个模块</div>
              <h2 className="ih-hero-title">{model.title}</h2>
              {model.subtitle && <p className="ih-hero-subtitle">{model.subtitle}</p>}
            </div>
            <div className="ih-hero-icon" aria-hidden="true">
              <div className="ih-hero-icon__shape" />
            </div>
          </div>
          {sections[0] && renderSectionBlocks(sections[0].render_blocks, sections[0].section_id, sections[0].title)}
          <div className="ih-module-card__footer">
            <button
              className={`ih-btn ih-btn--secondary ${completedSections.has(sections[0].section_id) ? "done" : ""}`}
              onClick={() => markComplete(sections[0].section_id)}
            >
              {completedSections.has(sections[0].section_id) ? "已完成" : "标记完成"}
            </button>
          </div>
        </section>

        {/* Remaining module cards */}
        {sections.slice(1).map((section, idx) => {
          const eyebrow = deriveEyebrow(section.render_blocks, idx + 1, sections.length);
          return (
          <section
            key={section.section_id}
            id={section.section_id}
            ref={(el) => { if (el) sectionRefs.current.set(section.section_id, el); }}
            className="ih-module-card"
          >
            <div className="ih-module-card__header">
              {eyebrow && <div className="ih-eyebrow">模块 {idx + 2} &middot; {eyebrow}</div>}
              <h2 className="ih-module-card__title">{section.title}</h2>
              <p className="ih-module-card__goal">{section.learning_goal}</p>
            </div>
            <div className="ih-module-card__blocks">
              {renderSectionBlocks(section.render_blocks, section.section_id, section.title)}
            </div>
            <div className="ih-module-card__footer">
              <button
                className={`ih-btn ih-btn--secondary ${completedSections.has(section.section_id) ? "done" : ""}`}
                onClick={() => markComplete(section.section_id)}
              >
                {completedSections.has(section.section_id) ? "已完成" : "标记完成"}
              </button>
            </div>
          </section>
          );
        })}

        {/* Citations */}
        {model.citations.length > 0 && (
          <footer className="ih-citations">
            <h3>参考资料</h3>
            <ul>
              {model.citations.map((citation, i) => (
                <li key={i}>{(citation as any).source_id ?? `资料 ${i + 1}`}</li>
              ))}
            </ul>
          </footer>
        )}
      </main>
    </div>
  );
};

export default InteractiveHtmlRenderer;
