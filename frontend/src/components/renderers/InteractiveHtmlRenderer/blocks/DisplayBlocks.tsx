import React, { useState, useEffect, useRef, useCallback } from "react";
import type { InteractiveHtmlRenderBlock } from "../../../../types/interactiveHtml";

function getData(block: InteractiveHtmlRenderBlock): Record<string, unknown> {
  return (block.block_data ?? {}) as Record<string, unknown>;
}

// ---- AnimatedFlowBlock (enhanced: track-line, packet, tokens, auto-play, story) ----

export const AnimatedFlowBlock: React.FC<{
  block: InteractiveHtmlRenderBlock;
  onScore?: (points: number) => void;
}> = ({ block, onScore }) => {
  const data = getData(block);
  const steps = (data.steps as Array<Record<string, unknown>>) ?? [];
  const playback = (data.playback as Record<string, unknown>) ?? {};
  const mode = (playback.mode as string) ?? "manual";
  const intervalMs = (playback.default_interval_ms as number) ?? 1200;

  const [currentStep, setCurrentStep] = useState(-1);
  const [isPlaying, setIsPlaying] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  useEffect(() => {
    return clearTimer;
  }, [clearTimer]);

  if (steps.length === 0) return null;

  const goToStep = (index: number) => {
    const clamped = Math.max(-1, Math.min(index, steps.length - 1));
    setCurrentStep(clamped);
    if (clamped >= steps.length - 1) {
      setIsPlaying(false);
      clearTimer();
    }
  };

  const play = () => {
    clearTimer();
    setIsPlaying(true);
    let step = currentStep;
    timerRef.current = setInterval(() => {
      step += 1;
      if (step >= steps.length) {
        clearTimer();
        setIsPlaying(false);
        if (onScore) onScore(5);
        return;
      }
      setCurrentStep(step);
    }, intervalMs);
  };

  const reset = () => {
    clearTimer();
    setIsPlaying(false);
    setCurrentStep(-1);
  };

  const fillPercent = currentStep < 0 ? 0 : (currentStep / (steps.length - 1 || 1)) * 100;
  const nodePositions = steps.map((_, i) => 12 + i * ((100 - 24) / (steps.length - 1 || 1)));

  // Split text into tokens: CJK characters individually, others by whitespace
  function tokenize(text: string): string[] {
    const cjk = /[一-鿿㐀-䶿]/;
    if (cjk.test(text)) return [...text].filter((c) => c.trim() !== "");
    return text.split(/\s+/).filter(Boolean);
  }

  return (
    <div className="ih-animated-flow">
      {/* Controls */}
      <div className="ih-flow-controls">
        <div className="ih-flow-controls__left">
          {mode !== "manual" && (
            <button className="ih-btn ih-btn--primary" onClick={play} disabled={isPlaying}>
              播放动画
            </button>
          )}
          <button className="ih-btn ih-btn--secondary" onClick={() => goToStep(currentStep + 1)} disabled={currentStep >= steps.length - 1}>
            下一步
          </button>
          <button className="ih-btn ih-btn--ghost" onClick={reset}>重置</button>
        </div>
        <span className="ih-flow-status">
          {currentStep < 0 ? "准备就绪" : `步骤 ${currentStep + 1} / ${steps.length}`}
        </span>
      </div>

      {/* Flow board with track-line + packet + nodes */}
      <div className="ih-flow-board">
        <div className="ih-flow-track">
          <div className="ih-flow-track__line">
            <div className="ih-flow-track__fill" style={{ width: `${fillPercent}%` }} />
          </div>
          {currentStep >= 0 && (
            <div className="ih-flow-packet" style={{ left: `${nodePositions[currentStep]}%` }}>&#10022;</div>
          )}
          <div className="ih-flow-nodes">
            {steps.map((step, i) => (
              <div key={step.step_id as string} className={`ih-flow-node ${i === currentStep ? "active" : ""} ${i < currentStep ? "done" : ""}`}>
                <div className="ih-flow-node__dot">{i + 1}</div>
                <article className="ih-flow-node__card">
                  <h4>{step.title as string}</h4>
                  <p>{step.description as string}</p>
                </article>
              </div>
            ))}
          </div>
        </div>

        {/* Token stream */}
        <div className="ih-token-stream">
          {(currentStep >= 1
            ? tokenize(steps[currentStep]?.visual_label as string ?? steps[currentStep]?.title as string ?? "")
            : []
          ).map((token: string, j: number) => (
            <span key={j} className={`ih-token-chip ${currentStep >= 1 ? "show" : ""}`}>
              {token}
            </span>
          ))}
          {currentStep < 1 && <span className="ih-token-chip show">流程开始后，关键词将在此逐步显示…</span>}
        </div>
      </div>

      {/* Story panel */}
      <div className="ih-flow-story">
        {currentStep < 0 ? (
          <><strong>准备就绪：</strong>点击<em>下一步</em>或<em>播放动画</em>浏览完整流程。</>
        ) : (
          <><strong>{steps[currentStep]?.title as string}：</strong> {steps[currentStep]?.tutor_message ?? steps[currentStep]?.description as string}</>
        )}
      </div>
    </div>
  );
};

// ---- CaseCompareBlock (with internal tabs) ----

export const CaseCompareBlock: React.FC<{ block: InteractiveHtmlRenderBlock }> = ({ block }) => {
  const data = getData(block);
  const cases = (data.cases as Array<Record<string, unknown>>) ?? [];
  const takeaway = data.takeaway as string | undefined;
  const [activeTab, setActiveTab] = useState(0);

  if (cases.length === 0) return null;

  // Group cases into pairs for comparison tabs
  const comparisons: Array<Array<Record<string, unknown>>> = [];
  for (let i = 0; i < cases.length; i += 2) {
    comparisons.push(cases.slice(i, i + 2));
  }

  return (
    <div className="ih-case-compare">
      {comparisons.length > 1 && (
        <div className="ih-case-tabs">
          {comparisons.map((pair, i) => (
            <button
              key={i}
              className={`ih-case-tab ${i === activeTab ? "active" : ""}`}
              onClick={() => setActiveTab(i)}
            >
              {i + 1}. {pair[0]?.title as string ?? `Case ${i * 2 + 1}`} vs {pair[1]?.title as string ?? `Case ${i * 2 + 2}`}
            </button>
          ))}
        </div>
      )}

      <div className="ih-case-compare__grid">
        {(comparisons[activeTab] ?? []).map((c) => (
          <div key={c.case_id as string} className={`ih-case-compare__case ih-case-compare__case--${c.variant ?? "default"}`}>
            <h4>{c.title as string}</h4>
            <p>{c.content as string}</p>
            {Array.isArray(c.tags) && (c.tags as string[]).length > 0 && (
              <div className="ih-case-compare__tags">
                {(c.tags as string[]).map((t, ti) => {
                  const isGood = /good|success|正确|合理|推荐/i.test(t);
                  const isWarn = /weak|bad|error|错误|不足|风险/i.test(t);
                  return <span key={ti} className={`ih-tag ${isGood ? "green" : ""} ${isWarn ? "orange" : ""}`}>{t}</span>;
                })}
              </div>
            )}
          </div>
        ))}
      </div>

      {takeaway && <p className="ih-case-compare__takeaway"><strong>要点总结：</strong> {takeaway}</p>}
    </div>
  );
};

// ---- ContextInspectorBlock ----

export const ContextInspectorBlock: React.FC<{ block: InteractiveHtmlRenderBlock; onScore?: (points: number) => void }> = ({ block, onScore }) => {
  const data = getData(block);
  const items = (data.items as Array<Record<string, unknown>>) ?? [];
  const resultDescription = data.result_description as string | undefined;
  const [selected, setSelected] = useState<Set<string>>(
    new Set(items.filter((it) => it.selected_by_default).map((it) => it.item_id as string))
  );

  const toggle = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      if (next.size === items.length && onScore) onScore(5);
      return next;
    });
  };

  const checkedPercent = Math.round((selected.size / (items.length || 1)) * 100);

  return (
    <div className="ih-context-inspector">
      {items.map((it) => {
        const isSelected = selected.has(it.item_id as string);
        return (
          <label key={it.item_id as string} className="ih-context-inspector__item">
            <input type="checkbox" checked={isSelected} onChange={() => toggle(it.item_id as string)} />
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <strong>{it.label as string}</strong>
                {isSelected && (it.effect_explanation as string) && (
                  <span style={{ color: "var(--ih-primary)", fontSize: 12, fontWeight: 700 }}>
                    {(it.effect_explanation as string)}
                  </span>
                )}
              </div>
              <span>{it.description as string}</span>
            </div>
          </label>
        );
      })}
      <div className="ih-context-meter"><span style={{ width: `${checkedPercent}%` }} /></div>
      {resultDescription && <p className="ih-context-inspector__result">{resultDescription}</p>}
    </div>
  );
};

// ---- StepperBlock ----

export const StepperBlock: React.FC<{ block: InteractiveHtmlRenderBlock }> = ({ block }) => {
  const data = getData(block);
  const steps = (data.steps as Array<Record<string, unknown>>) ?? [];
  const [active, setActive] = useState(0);

  if (steps.length === 0) return null;

  return (
    <div className="ih-stepper">
      <div className="ih-stepper__tabs">
        {steps.map((step, i) => (
          <button key={i} className={`ih-stepper__tab ${i === active ? "active" : ""}`} onClick={() => setActive(i)}>
            {step.title as string}
          </button>
        ))}
      </div>
      {steps[active] && (
        <div className="ih-stepper__content">
          <p>{steps[active].description as string}</p>
        </div>
      )}
    </div>
  );
};
