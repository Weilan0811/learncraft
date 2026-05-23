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
import { createLearningSession, getSessionState, submitLearningEvent } from "../../../api/learningApi";
import { useContentGenerationStore } from "../../../stores/contentGenerationStore";
import "./styles.css";

interface Props {
  model: InteractiveHtmlRenderModel;
  fullscreen?: boolean;
}

const ACTION_EVENT_TYPE: Partial<Record<string, LearningEventType>> = {
  "single-choice": "single_choice_answered",
  "multiple-choice-submit": "multiple_choice_answered",
  "short-answer-submit": "short_answer_submitted",
  "scenario-discussion-submit": "scenario_discussion_submitted",
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
    "data-feedback",
    "data-option-label",
    "data-ih-input-for",
    "data-ih-feedback-for",
    "data-min-length",
  ],
  FORBID_TAGS: ["script", "iframe", "object", "embed", "link", "meta", "svg"],
  FORBID_ATTR: ["onclick", "onchange", "oninput", "onkeydown", "onkeyup", "onmouseover"],
};

function sessionStorageKey(lessonId: string): string {
  return `interactive-html-session:${lessonId}`;
}

function readStoredSession(lessonId: string): CreateSessionResponse | null {
  try {
    const raw = window.localStorage.getItem(sessionStorageKey(lessonId));
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<CreateSessionResponse>;
    if (parsed.session_id && parsed.lesson_id === lessonId) {
      return { session_id: parsed.session_id, lesson_id: parsed.lesson_id, state: parsed.state ?? {} };
    }
  } catch {
    window.localStorage.removeItem(sessionStorageKey(lessonId));
  }
  return null;
}

function storeSession(session: CreateSessionResponse): void {
  window.localStorage.setItem(sessionStorageKey(session.lesson_id), JSON.stringify(session));
}

function clearStoredSession(lessonId: string): void {
  window.localStorage.removeItem(sessionStorageKey(lessonId));
}

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
  el.classList.toggle("is-selected", pressed);
  el.setAttribute("aria-pressed", pressed ? "true" : "false");
}

function findFeedbackBox(root: ParentNode, interactionId: string): HTMLElement | null {
  return Array.from(root.querySelectorAll<HTMLElement>("[data-ih-feedback-for]"))
    .find((el) => el.dataset.ihFeedbackFor === interactionId) ?? null;
}

function findInteractionInput(root: ParentNode, interactionId: string): HTMLTextAreaElement | HTMLInputElement | null {
  return Array.from(root.querySelectorAll<HTMLTextAreaElement | HTMLInputElement>("[data-ih-input-for]"))
    .find((el) => el.dataset.ihInputFor === interactionId) ?? null;
}

function showFeedback(root: ParentNode, interactionId: string, title: string, message: string, variant: "success" | "warn"): void {
  const box = findFeedbackBox(root, interactionId);
  if (!box) return;
  box.classList.remove("success", "warn");
  box.classList.add("is-visible", variant);
  box.textContent = "";
  const strong = document.createElement("strong");
  strong.textContent = title;
  const body = document.createElement("div");
  body.textContent = message;
  box.append(strong, body);
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
  const setInteractiveSessionId = useContentGenerationStore((state) => state.setInteractiveSessionId);
  const [completedSections, setCompletedSections] = useState<Set<string>>(new Set());
  const [activeSectionId, setActiveSectionId] = useState<string | null>(model.sections[0]?.section_id ?? null);
  const selectedOptionsRef = useRef<Map<string, Set<string>>>(new Map());

  useScopedStyles(model.sections);

  useEffect(() => {
    let cancelled = false;

    const useSession = (nextSession: CreateSessionResponse) => {
      if (cancelled) return;
      setSession(nextSession);
      setInteractiveSessionId(nextSession.session_id);
      storeSession(nextSession);
    };

    const createAndUseSession = async () => {
      const createdSession = await createLearningSession(model.lesson_id);
      useSession(createdSession);
    };

    const storedSession = readStoredSession(model.lesson_id);
    if (storedSession) {
      getSessionState(model.lesson_id, storedSession.session_id)
        .then(() => useSession(storedSession))
        .catch(() => {
          clearStoredSession(model.lesson_id);
          void createAndUseSession();
        });
    } else {
      void createAndUseSession();
    }

    return () => {
      cancelled = true;
    };
  }, [model.lesson_id, setInteractiveSessionId]);

  useEffect(() => {
    return () => setInteractiveSessionId(undefined);
  }, [setInteractiveSessionId]);

  useEffect(() => {
    setActiveSectionId(model.sections[0]?.section_id ?? null);
  }, [model.lesson_id, model.sections]);

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
  }, []);

  const submitInteraction = useCallback((params: {
    sectionId: string;
    interactionId?: string;
    blockId?: string | null;
    eventType?: LearningEventType;
    payload?: LearningEventPayload;
  }) => {
    if (!params.sectionId || !params.eventType) return;
    void handleSubmitEvent({
      section_id: params.sectionId,
      block_id: params.blockId || null,
      interaction_id: params.interactionId || null,
      event_type: params.eventType,
      payload: params.payload ?? {},
    });
  }, [handleSubmitEvent]);

  const handleRuntimeClick = useCallback((event: React.MouseEvent<HTMLElement>) => {
    const target = (event.target as HTMLElement).closest<HTMLElement>("[data-ih-action]");
    if (!target) return;

    const action = target.dataset.ihAction || "";
    const sectionId = sectionIdFor(target);
    const interactionId = target.dataset.interactionId;
    const eventType = ACTION_EVENT_TYPE[action];
    const block = target.closest<HTMLElement>("[data-block-id]");
    const blockId = block?.dataset.blockId || null;
    const interactionBox = block || target.closest<HTMLElement>("[data-interaction-id]") || target;

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
      const isCorrect = target.dataset.correct === "true";
      interactionBox.querySelectorAll<HTMLElement>(`[data-interaction-id="${interactionId}"][data-option-id]`).forEach((option) => {
        setPressed(option, option === target);
        option.classList.remove("is-correct", "is-wrong", "answered");
      });
      target.classList.add("answered", isCorrect ? "is-correct" : "is-wrong");
      if (interactionId) {
        showFeedback(
          interactionBox,
          interactionId,
          isCorrect ? "回答正确" : "再想一想",
          target.dataset.feedback || "已记录你的选择。",
          isCorrect ? "success" : "warn"
        );
      }
      // setScore((s) => s + 1);
      submitInteraction({
        sectionId,
        interactionId,
        blockId,
        eventType,
        payload: {
          selected_option_ids: optionId ? [optionId] : [],
          is_correct: isCorrect,
          client_timestamp: new Date().toISOString(),
        },
      });
      return;
    }

    if (action === "multiple-choice-toggle") {
      if (!interactionId) return;
      if (!selectedOptionsRef.current.has(interactionId)) {
        selectedOptionsRef.current.set(interactionId, new Set());
      }
      const selected = selectedOptionsRef.current.get(interactionId)!;
      const optionId = target.dataset.optionId || "";
      if (selected.has(optionId)) {
        selected.delete(optionId);
        setPressed(target, false);
      } else {
        selected.add(optionId);
        setPressed(target, true);
      }
      return;
    }

    if (action === "multiple-choice-submit") {
      if (!interactionId) return;
      const selected = selectedOptionsRef.current.get(interactionId) || new Set<string>();
      const options = Array.from(interactionBox.querySelectorAll<HTMLElement>(`[data-interaction-id="${interactionId}"][data-option-id]`));
      const selectedIds = Array.from(selected);
      const correctIds = options.filter((option) => option.dataset.correct === "true").map((option) => option.dataset.optionId || "");
      options.forEach((option) => {
        option.classList.remove("is-correct", "is-wrong");
        if (option.dataset.correct === "true") option.classList.add("is-correct");
        else if (selected.has(option.dataset.optionId || "")) option.classList.add("is-wrong");
      });
      const isCorrect = selectedIds.length === correctIds.length && correctIds.every((id) => selected.has(id));
      showFeedback(
        interactionBox,
        interactionId,
        isCorrect ? "选择完整" : "已提交，看看高亮提示",
        isCorrect ? "你选中了所有关键项。" : "绿色为应选择项，红色为不建议项。",
        isCorrect ? "success" : "warn"
      );
      submitInteraction({
        sectionId,
        interactionId,
        eventType,
        blockId,
        payload: {
          selected_option_ids: selectedIds,
          correct_option_ids: correctIds,
          is_correct: isCorrect,
          client_timestamp: new Date().toISOString(),
        },
      });
      return;
    }

    if (action === "short-answer-submit" || action === "scenario-discussion-submit") {
      if (!interactionId) return;
      const input = findInteractionInput(interactionBox, interactionId);
      const answer = input?.value?.trim() ?? "";
      const minLength = Number(target.dataset.minLength || 0);
      if (answer.length < minLength) {
        showFeedback(interactionBox, interactionId, "还可以再展开一点", `这类问题建议至少写 ${minLength} 个字。`, "warn");
        return;
      }
      showFeedback(
        interactionBox,
        interactionId,
        "已记录你的回答",
        "你的回答已记录，可以继续学习下一部分。",
        "success"
      );
      target.classList.toggle("answered", answer.length > 0);
      submitInteraction({
        sectionId,
        interactionId,
        eventType,
        blockId,
        payload: {
          answer_text: answer,
          client_timestamp: new Date().toISOString(),
        },
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

  const activeSection = sanitizedSections.find((section) => section.section_id === activeSectionId) ?? sanitizedSections[0];
  const activeSectionIndex = activeSection
    ? sanitizedSections.findIndex((section) => section.section_id === activeSection.section_id)
    : -1;

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
              className={`ih-nav__link ${item.section_id === activeSection?.section_id ? "active" : ""} ${completedSections.has(item.section_id) ? "done" : ""}`}
              onClick={() => setActiveSectionId(item.section_id)}
            >
              <span className="ih-nav__dot" />
              <span className="ih-nav__label">{item.title || `单元 ${i + 1}`}</span>
              {completedSections.has(item.section_id) && <span className="ih-nav__check">&#10003;</span>}
            </button>
          ))}
        </nav>
        <div className="ih-progress-card">
          <strong>学习进度</strong>
          <div className="ih-progress-bar"><span style={{ width: `${progressPercent}%` }} /></div>
          <p className="ih-progress-text">已完成 {progressPercent}%</p>
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

        {activeSection && (
          <article
            key={activeSection.section_id}
            id={activeSection.section_id}
            className={`ih-module-card ${activeSection.style_scope_id}`}
            data-section-id={activeSection.section_id}
          >
            <div className="ih-module-card__header">
              <div className="ih-eyebrow">单元 {activeSectionIndex + 1}</div>
              <h2 className="ih-module-card__title">{activeSection.title}</h2>
              <p className="ih-module-card__goal">{activeSection.learning_goal}</p>
            </div>
            <div
              className="ih-fragment"
              dangerouslySetInnerHTML={{ __html: activeSection.html_fragment }}
            />
            <div className="ih-module-card__footer">
              <button
                className={`ih-btn ih-btn--secondary ${completedSections.has(activeSection.section_id) ? "done" : ""}`}
                data-ih-action="complete-section"
                data-section-id={activeSection.section_id}
              >
                {completedSections.has(activeSection.section_id) ? "已完成" : "标记完成"}
              </button>
            </div>
          </article>
        )}

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
