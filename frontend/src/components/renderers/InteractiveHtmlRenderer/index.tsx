import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import DOMPurify from "dompurify";
import type {
  CreateSessionResponse,
  InteractiveHtmlRenderModel,
  InteractiveHtmlRenderedUnit,
  LearningEventPayload,
  LearningEventType,
  SubmitEventRequest,
} from "../../../types/interactiveHtml";
import { createLearningSession, submitLearningEvent } from "../../../api/learningApi";
import "./styles.css";

interface Props {
  model: InteractiveHtmlRenderModel;
  fullscreen?: boolean;
}

const ACTION_EVENT_TYPE: Partial<Record<string, LearningEventType>> = {
  "single-choice": "single_choice_answered",
  "multiple-choice": "multiple_choice_answered",
  "short-answer": "short_answer_submitted",
  "sequence-select": "sequence_submitted",
  "match-select": "drag_match_submitted",
};

const SANITIZE_CONFIG = {
  ADD_TAGS: ["section"],
  ADD_ATTR: [
    "aria-label",
    "aria-labelledby",
    "aria-describedby",
    "aria-controls",
    "aria-expanded",
    "aria-selected",
    "role",
    "data-ih-action",
    "data-section-id",
    "data-block-id",
    "data-block-type",
    "data-interaction-id",
    "data-option-id",
    "data-item-id",
    "data-target-id",
    "data-tab-target",
    "data-tab-panel",
    "data-flow-id",
    "data-step",
    "data-correct",
  ],
  FORBID_TAGS: ["script", "iframe", "object", "embed", "link", "meta", "svg"],
  FORBID_ATTR: ["onclick", "onchange", "oninput", "onkeydown", "onkeyup", "onmouseover"],
};

function optionIds(container: Element, selector = ".selected,[aria-pressed='true']"): string[] {
  return Array.from(container.querySelectorAll<HTMLElement>(selector))
    .map((el) => el.dataset.optionId || el.dataset.itemId || "")
    .filter(Boolean);
}

function sectionIdFor(target: HTMLElement): string {
  return target.closest<HTMLElement>("[data-section-id]")?.dataset.sectionId || "";
}

function setPressed(el: HTMLElement, pressed: boolean): void {
  el.classList.toggle("selected", pressed);
  el.classList.toggle("active", pressed);
  el.setAttribute("aria-pressed", pressed ? "true" : "false");
}

function useScopedStyles(sections: InteractiveHtmlRenderedUnit[]) {
  const styleRef = useRef<HTMLStyleElement | null>(null);

  useEffect(() => {
    if (!styleRef.current) {
      styleRef.current = document.createElement("style");
      styleRef.current.setAttribute("data-ih-scoped", "true");
      document.head.appendChild(styleRef.current);
    }

    const css = sections
      .filter((section) => section.css_fragment?.trim())
      .map((section) => `/* scope: ${section.style_scope_id} */\n${section.css_fragment}`)
      .join("\n\n");

    styleRef.current.textContent = css;

    return () => {
      if (styleRef.current && styleRef.current.parentNode) {
        styleRef.current.parentNode.removeChild(styleRef.current);
        styleRef.current = null;
      }
    };
  }, [sections]);
}

export const InteractiveHtmlRenderer: React.FC<Props> = ({ model, fullscreen = false }) => {
  const [session, setSession] = useState<CreateSessionResponse | null>(null);
  const [completedSections, setCompletedSections] = useState<Set<string>>(new Set());
  const [score, setScore] = useState(0);
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const sectionRefs = useRef<Map<string, HTMLElement>>(new Map());

  useScopedStyles(model.sections);

  useEffect(() => {
    createLearningSession(model.lesson_id).then(setSession).catch(console.error);
  }, [model.lesson_id]);

  const sanitizedSections = useMemo(
    () =>
      model.sections.map((section) => ({
        ...section,
        html_fragment: DOMPurify.sanitize(section.html_fragment, SANITIZE_CONFIG),
      })),
    [model.sections]
  );

  const handleSubmitEvent = useCallback(async (event: SubmitEventRequest) => {
    if (!session) return;
    try {
      await submitLearningEvent(model.lesson_id, session.session_id, event);
    } catch (err) {
      console.error("Failed to submit learning event:", err);
    }
  }, [model.lesson_id, session]);

  const markComplete = useCallback((sectionId: string) => {
    if (!sectionId) return;
    setCompletedSections((prev) => {
      if (prev.has(sectionId)) return prev;
      const next = new Set(prev);
      next.add(sectionId);
      return next;
    });
    setScore((s) => s + 5);
  }, []);

  const submitInteraction = useCallback((params: {
    sectionId: string;
    interactionId?: string;
    eventType?: LearningEventType;
    payload?: LearningEventPayload;
  }) => {
    if (!params.sectionId || !params.eventType) return;
    void handleSubmitEvent({
      section_id: params.sectionId,
      interaction_id: params.interactionId || null,
      event_type: params.eventType,
      payload: params.payload ?? {},
    });
  }, [handleSubmitEvent]);

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
  }, [sanitizedSections]);

  const scrollToSection = (sectionId: string) => {
    sectionRefs.current.get(sectionId)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const handleRuntimeClick = useCallback((event: React.MouseEvent<HTMLElement>) => {
    const target = (event.target as HTMLElement).closest<HTMLElement>("[data-ih-action]");
    if (!target) return;

    const action = target.dataset.ihAction || "";
    const sectionId = sectionIdFor(target);
    const interactionId = target.dataset.interactionId;
    const eventType = ACTION_EVENT_TYPE[action];
    const interactionBox = target.closest<HTMLElement>("[data-interaction-id]") || target;

    if (action === "complete-section") {
      markComplete(sectionId);
      return;
    }

    if (action === "tab-select") {
      const tabTarget = target.dataset.tabTarget;
      const tabsRoot = target.closest<HTMLElement>(".ih-tabs") || target.parentElement;
      if (tabsRoot && tabTarget) {
        tabsRoot.querySelectorAll<HTMLElement>("[data-ih-action='tab-select']").forEach((tab) => setPressed(tab, tab === target));
        tabsRoot.querySelectorAll<HTMLElement>("[data-ih-tab-panel], .ih-tab-panel").forEach((panel) => {
          const isActive = panel.id === tabTarget || panel.getAttribute("data-tab-panel") === tabTarget;
          panel.classList.toggle("active", isActive);
          panel.toggleAttribute("hidden", !isActive);
        });
      }
      return;
    }

    if (action === "flow-next" || action === "flow-prev" || action === "flow-reset") {
      const flow = target.closest<HTMLElement>(".ih-flow-board,[data-flow-id]");
      if (!flow) return;
      const steps = Array.from(flow.querySelectorAll<HTMLElement>("[data-step]"));
      const max = Math.max(steps.length - 1, 0);
      const current = Number(flow.dataset.currentStep || "0");
      const next = action === "flow-reset" ? 0 : action === "flow-next" ? Math.min(current + 1, max) : Math.max(current - 1, 0);
      flow.dataset.currentStep = String(next);
      steps.forEach((step, index) => {
        step.classList.toggle("active", index === next);
        step.classList.toggle("done", index < next);
      });
      return;
    }

    if (action === "single-choice") {
      const optionId = target.dataset.optionId;
      interactionBox.querySelectorAll<HTMLElement>("[data-option-id]").forEach((option) => setPressed(option, option === target));
      target.classList.add("answered");
      setScore((s) => s + 1);
      submitInteraction({
        sectionId,
        interactionId,
        eventType,
        payload: { selected_option_ids: optionId ? [optionId] : [] },
      });
      return;
    }

    if (action === "multiple-choice") {
      setPressed(target, !target.classList.contains("selected"));
      submitInteraction({
        sectionId,
        interactionId,
        eventType,
        payload: { selected_option_ids: optionIds(interactionBox, "[data-option-id].selected") },
      });
      return;
    }

    if (action === "short-answer") {
      const answer = interactionBox.querySelector<HTMLTextAreaElement | HTMLInputElement>("textarea,input[type='text']")?.value ?? "";
      target.classList.toggle("answered", answer.trim().length > 0);
      submitInteraction({
        sectionId,
        interactionId,
        eventType,
        payload: { answer_text: answer },
      });
      return;
    }

    if (action === "sequence-select") {
      setPressed(target, !target.classList.contains("selected"));
      submitInteraction({
        sectionId,
        interactionId,
        eventType,
        payload: { ordered_item_ids: optionIds(interactionBox, "[data-item-id].selected") },
      });
      return;
    }

    if (action === "match-select") {
      const selectedSource = interactionBox.querySelector<HTMLElement>("[data-item-id].selected");
      if (target.dataset.itemId) {
        interactionBox.querySelectorAll<HTMLElement>("[data-item-id]").forEach((item) => setPressed(item, item === target));
        return;
      }
      if (selectedSource && target.dataset.targetId) {
        const pair = { [selectedSource.dataset.itemId || ""]: target.dataset.targetId };
        selectedSource.classList.remove("selected", "active");
        target.classList.add("selected-target");
        submitInteraction({
          sectionId,
          interactionId,
          eventType,
          payload: { match_pairs: pair },
        });
      }
    }
  }, [markComplete, submitInteraction]);

  const navigation = model.navigation.length > 0
    ? model.navigation
    : sanitizedSections.map((section) => ({
        section_id: section.section_id,
        title: section.title,
        anchor: `#${section.section_id}`,
      }));

  const progressPercent = sanitizedSections.length > 0
    ? Math.round((completedSections.size / sanitizedSections.length) * 100)
    : 0;

  return (
    <div className={`ih-app${fullscreen ? " ih-app--fullscreen" : ""}`}>
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
          {navigation.map((item, i) => (
            <button
              key={item.section_id}
              className={`ih-nav__link ${item.section_id === activeSection ? "active" : ""} ${completedSections.has(item.section_id) ? "done" : ""}`}
              onClick={() => scrollToSection(item.section_id)}
            >
              <span className="ih-nav__dot" />
              <span className="ih-nav__label">{i === 0 ? "课程封面" : item.title}</span>
              {completedSections.has(item.section_id) && <span className="ih-nav__check">&#10003;</span>}
            </button>
          ))}
        </nav>
        <div className="ih-progress-card">
          <strong>学习进度</strong>
          <div className="ih-progress-bar"><span style={{ width: `${progressPercent}%` }} /></div>
          <p className="ih-progress-text">已完成 {progressPercent}%</p>
          <div className="ih-score-pill">互动积分 {score}</div>
        </div>
      </aside>

      <main className="ih-main" onClick={handleRuntimeClick}>
        <section className="ih-module-card ih-module-card--hero">
          <div className="ih-hero-inner">
            <div className="ih-hero-text">
              <div className="ih-eyebrow">课程封面 &middot; 共 {sanitizedSections.length} 个单元</div>
              <h2 className="ih-hero-title">{model.title}</h2>
              {model.subtitle && <p className="ih-hero-subtitle">{model.subtitle}</p>}
            </div>
            <div className="ih-hero-icon" aria-hidden="true">
              <div className="ih-hero-icon__shape" />
            </div>
          </div>
        </section>

        {sanitizedSections.map((section, index) => (
          <article
            key={section.section_id}
            id={section.section_id}
            ref={(el) => {
              if (el) sectionRefs.current.set(section.section_id, el);
            }}
            className={`ih-module-card ${section.style_scope_id}`}
            data-section-id={section.section_id}
          >
            <div className="ih-module-card__header">
              <div className="ih-eyebrow">单元 {index + 1}</div>
              <h2 className="ih-module-card__title">{section.title}</h2>
              <p className="ih-module-card__goal">{section.learning_goal}</p>
            </div>
            <div
              className="ih-fragment"
              dangerouslySetInnerHTML={{ __html: section.html_fragment }}
            />
            <div className="ih-module-card__footer">
              <button
                className={`ih-btn ih-btn--secondary ${completedSections.has(section.section_id) ? "done" : ""}`}
                data-ih-action="complete-section"
                data-section-id={section.section_id}
              >
                {completedSections.has(section.section_id) ? "已完成" : "标记完成"}
              </button>
            </div>
          </article>
        ))}

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
