import React, { useState, useRef, useCallback, useEffect } from "react";
import type { InteractiveHtmlRenderBlock } from "../../../../types/interactiveHtml";
import type { SubmitEventRequest } from "../../../../types/interactiveHtml";

function getData(block: InteractiveHtmlRenderBlock): Record<string, unknown> {
  return (block.block_data ?? {}) as Record<string, unknown>;
}

interface InteractiveBlockProps {
  block: InteractiveHtmlRenderBlock;
  lessonId: string;
  sessionId: string;
  sectionId: string;
  onSubmitEvent: (event: SubmitEventRequest) => void;
  onScore?: (points: number) => void;
}

// ---- SingleChoiceBlock ----

export const SingleChoiceBlock: React.FC<InteractiveBlockProps> = ({
  block, lessonId, sessionId, sectionId, onSubmitEvent, onScore,
}) => {
  const data = getData(block);
  const question = (data.question as string) ?? "";
  const options = (data.options as Array<Record<string, unknown>>) ?? [];
  const explanation = (data.explanation as string) ?? "";
  const interactionId = block.block_data?.interaction_id as string | undefined;
  const [selected, setSelected] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (optionId: string) => {
    if (submitted) return;
    setSelected(optionId);
    setSubmitted(true);
    const opt = options.find((o) => o.option_id === optionId);
    if (opt?.is_correct && onScore) onScore(10);
    onSubmitEvent({
      section_id: sectionId,
      block_id: block.block_id,
      interaction_id: interactionId ?? null,
      event_type: "single_choice_answered",
      payload: { selected_option_ids: [optionId] },
    });
  };

  return (
    <div className="ih-interactive ih-single-choice">
      <h4 className="ih-question">{question}</h4>
      <div className="ih-options">
        {options.map((opt) => {
          const isSelected = selected === (opt.option_id as string);
          const isCorrect = opt.is_correct as boolean;
          return (
            <button
              key={opt.option_id as string}
              className={`ih-option ${submitted ? (isCorrect ? "correct" : isSelected ? "wrong" : "") : ""}`}
              disabled={submitted}
              onClick={() => handleSubmit(opt.option_id as string)}
            >
              {opt.text as string}
            </button>
          );
        })}
      </div>
      {submitted && <div className="ih-explanation">{explanation}</div>}
    </div>
  );
};

// ---- MultipleChoiceBlock (button toggle style) ----

export const MultipleChoiceBlock: React.FC<InteractiveBlockProps> = ({
  block, lessonId, sessionId, sectionId, onSubmitEvent, onScore,
}) => {
  const data = getData(block);
  const question = (data.question as string) ?? "";
  const options = (data.options as Array<Record<string, unknown>>) ?? [];
  const explanation = (data.explanation as string) ?? "";
  const interactionId = block.block_data?.interaction_id as string | undefined;
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [submitted, setSubmitted] = useState(false);

  const toggle = (id: string) => {
    if (submitted) return;
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleSubmit = () => {
    if (submitted || selected.size === 0) return;
    setSubmitted(true);
    const allCorrect = options.every((o) => {
      const should = o.is_correct as boolean;
      const isSelected = selected.has(o.option_id as string);
      return should === isSelected;
    });
    if (allCorrect && onScore) onScore(12);
    onSubmitEvent({
      section_id: sectionId,
      block_id: block.block_id,
      interaction_id: interactionId ?? null,
      event_type: "multiple_choice_answered",
      payload: { selected_option_ids: Array.from(selected) },
    });
  };

  return (
    <div className="ih-interactive ih-multiple-choice">
      <h4 className="ih-question">{question}</h4>
      <div className="ih-options">
        {options.map((opt) => {
          const isSelected = selected.has(opt.option_id as string);
          const isCorrect = opt.is_correct as boolean;
          let cls = "ih-option";
          if (submitted) {
            if (isCorrect) cls += " correct";
            else if (isSelected) cls += " wrong";
          } else if (isSelected) {
            cls += " active";
          }
          return (
            <button
              key={opt.option_id as string}
              className={cls}
              disabled={submitted}
              onClick={() => toggle(opt.option_id as string)}
            >
              {opt.text as string}
            </button>
          );
        })}
      </div>
      {!submitted && (
        <button className="ih-submit-btn" onClick={handleSubmit} disabled={selected.size === 0}>提交多选</button>
      )}
      {submitted && (
        <div className="ih-explanation">{explanation}</div>
      )}
    </div>
  );
};

// ---- ShortAnswerBlock (toggleable rubric + draft save) ----

export const ShortAnswerBlock: React.FC<InteractiveBlockProps> = ({
  block, lessonId, sessionId, sectionId, onSubmitEvent, onScore,
}) => {
  const data = getData(block);
  const question = (data.question as string) ?? "";
  const placeholder = (data.placeholder as string) ?? "输入你的回答…";
  const referencePoints = (data.reference_points as string[]) ?? [];
  const discussionMode = (data.discussion_mode as boolean) ?? false;
  const interactionId = block.block_data?.interaction_id as string | undefined;
  const [answer, setAnswer] = useState("");
  const [showRubric, setShowRubric] = useState(false);
  const [saved, setSaved] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const saveKey = `ih-sa-${block.block_id}`;

  // Restore saved draft on mount
  useEffect(() => {
    try {
      const draft = localStorage.getItem(saveKey);
      if (draft) setAnswer(draft);
    } catch { /* localStorage unavailable */ }
  }, [saveKey]);

  const handleSubmit = () => {
    if (submitted || !answer.trim()) return;
    setSubmitted(true);
    if (onScore) onScore(6);
    onSubmitEvent({
      section_id: sectionId,
      block_id: block.block_id,
      interaction_id: interactionId ?? null,
      event_type: "short_answer_submitted",
      payload: { answer_text: answer },
    });
  };

  const handleSaveDraft = () => {
    if (!answer.trim()) return;
    try {
      localStorage.setItem(saveKey, answer);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch { /* localStorage unavailable */ }
  };

  return (
    <div className="ih-interactive ih-short-answer">
      <h4 className="ih-question">{question}</h4>
      {discussionMode && (
        <p className="ih-short-answer__mode">讨论模式 — 没有标准答案，自由表达你的想法。</p>
      )}
      <textarea
        placeholder={placeholder}
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        disabled={submitted}
        rows={5}
      />
      <div className="ih-short-answer__actions">
        {!submitted && (
          <button className="ih-submit-btn" onClick={handleSubmit} disabled={!answer.trim()}>提交回答</button>
        )}
        <button className="ih-btn ih-btn--secondary" onClick={() => setShowRubric((v) => !v)}>
          {showRubric ? "隐藏参考评分点" : "查看参考评分点"}
        </button>
        <button className="ih-btn ih-btn--ghost" onClick={handleSaveDraft} disabled={!answer.trim()}>
          {saved ? "已保存" : "保存我的回答"}
        </button>
      </div>
      {submitted && (
        <p className="ih-feedback" style={{ color: "var(--ih-green)" }}>你的回答已提交。</p>
      )}
      {showRubric && referencePoints.length > 0 && (
        <div className="ih-rubric">
          <strong>参考评分点：</strong>
          <ul>
            {referencePoints.map((pt, i) => <li key={i}>{pt}</li>)}
          </ul>
        </div>
      )}
      {saved && (
        <p className="ih-short-answer__saved-hint">已保存到本地浏览器，刷新页面后仍可恢复。</p>
      )}
    </div>
  );
};

// ---- DragMatchBlock (drag-drop + click fallback, items move into zones) ----

export const DragMatchBlock: React.FC<InteractiveBlockProps> = ({
  block, lessonId, sessionId, sectionId, onSubmitEvent, onScore,
}) => {
  const data = getData(block);
  const instruction = (data.instruction as string) ?? "";
  const items = (data.items as Array<Record<string, unknown>>) ?? [];
  const targets = (data.targets as Array<Record<string, unknown>>) ?? [];
  const explanation = (data.explanation as string) ?? "";
  const interactionId = block.block_data?.interaction_id as string | undefined;
  const [matches, setMatches] = useState<Record<string, string>>({});
  const [selectedItem, setSelectedItem] = useState<string | null>(null);
  const [draggedItem, setDraggedItem] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [matchResults, setMatchResults] = useState<Record<string, { correct: boolean }>>({});

  const matchedItemIds = new Set(Object.keys(matches));
  const unmatchedItems = items.filter((it) => !matchedItemIds.has(it.item_id as string));

  const getItemById = (id: string) => items.find((it) => it.item_id === id);

  const placeItem = (itemId: string, targetId: string) => {
    if (submitted) return;
    setMatches((prev) => {
      const next = { ...prev };
      delete next[itemId];
      Object.keys(next).forEach((k) => { if (next[k] === targetId) delete next[k]; });
      next[itemId] = targetId;
      return next;
    });
    setSelectedItem(null);
    setDraggedItem(null);
  };

  const unmatchItem = (itemId: string) => {
    if (submitted) return;
    setMatches((prev) => {
      const next = { ...prev };
      delete next[itemId];
      return next;
    });
  };

  const handleItemClick = (itemId: string) => {
    if (submitted) return;
    setSelectedItem((prev) => (prev === itemId ? null : itemId));
  };

  const handleTargetClick = (targetId: string) => {
    if (submitted || !selectedItem) return;
    placeItem(selectedItem, targetId);
  };

  const handleDragStart = (e: React.DragEvent, itemId: string) => {
    if (submitted) return;
    setDraggedItem(itemId);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", itemId);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
  };

  const handleDrop = (e: React.DragEvent, targetId: string) => {
    e.preventDefault();
    const itemId = e.dataTransfer.getData("text/plain") || draggedItem;
    if (itemId) placeItem(itemId, targetId);
  };

  const handleSubmit = () => {
    if (submitted) return;
    setSubmitted(true);
    const results: Record<string, { correct: boolean }> = {};
    let allCorrect = true;
    items.forEach((it) => {
      const expected = it.correct_target_id as string;
      const actual = matches[it.item_id as string];
      const isCorrect = expected ? actual === expected : false;
      results[it.item_id as string] = { correct: isCorrect };
      if (!isCorrect) allCorrect = false;
    });
    setMatchResults(results);
    if (allCorrect && onScore) onScore(12);
    onSubmitEvent({
      section_id: sectionId,
      block_id: block.block_id,
      interaction_id: interactionId ?? null,
      event_type: "drag_match_submitted",
      payload: { match_pairs: matches },
    });
  };

  return (
    <div className="ih-interactive ih-drag-match">
      <h4 className="ih-question">{instruction}</h4>
      <p className="ih-drag-match__hint">可以直接拖拽；也可以先点击左侧模块，再点击右侧目标完成匹配。</p>
      <div className="ih-match-board">
        {/* Left: unmatched items bank */}
        <div className="ih-match-board__bank">
          <p className="ih-match-board__label">选项</p>
          {unmatchedItems.map((it) => (
            <div
              key={it.item_id as string}
              className={`ih-match-item ${selectedItem === it.item_id ? "selected" : ""} ${draggedItem === it.item_id ? "dragging" : ""}`}
              draggable={!submitted}
              onDragStart={(e) => handleDragStart(e, it.item_id as string)}
              onDragEnd={() => setDraggedItem(null)}
              onClick={() => handleItemClick(it.item_id as string)}
            >
              <span>{it.text as string}</span>
              <span className="ih-match-item__handle">拖动 →</span>
            </div>
          ))}
          {unmatchedItems.length === 0 && !submitted && (
            <p className="ih-match-board__empty">所有选项已匹配。可以点击已放置的选项移回此处。</p>
          )}
        </div>
        {/* Right: target drop zones */}
        <div className="ih-match-board__zones">
          <p className="ih-match-board__label">目标</p>
          {targets.map((tgt) => {
            const matchedItemId = Object.keys(matches).find((k) => matches[k] === tgt.target_id);
            const matchedItem = matchedItemId ? getItemById(matchedItemId) : null;
            const result = matchedItemId ? matchResults[matchedItemId] : null;
            const isCorrect = result?.correct;
            const isWrong = result && !result.correct;
            // Find the correct item for this target (to show on wrong match)
            const correctItemForZone = submitted && isWrong
              ? items.find((it) => it.correct_target_id === tgt.target_id)
              : null;
            return (
              <div
                key={tgt.target_id as string}
                className={`ih-drop-zone ${selectedItem && !submitted ? "selected-target" : ""} ${submitted && isCorrect ? "correct" : ""} ${isWrong ? "wrong" : ""}`}
                onDragOver={handleDragOver}
                onDrop={(e) => handleDrop(e, tgt.target_id as string)}
                onClick={() => handleTargetClick(tgt.target_id as string)}
              >
                <span className="ih-drop-zone__label">{tgt.label as string}</span>
                {matchedItem ? (
                  <div
                    className={`ih-match-item ih-match-item--in-zone ${submitted && isCorrect ? "correct" : ""} ${isWrong ? "wrong" : ""}`}
                    draggable={!submitted}
                    onDragStart={(e) => handleDragStart(e, matchedItem.item_id as string)}
                    onClick={(e) => { e.stopPropagation(); if (!submitted) unmatchItem(matchedItem.item_id as string); }}
                  >
                    <span>{matchedItem.text as string}</span>
                    {isWrong && <span className="ih-match-item__result">✗</span>}
                    {isCorrect && <span className="ih-match-item__result correct">✓</span>}
                  </div>
                ) : null}
                {correctItemForZone && (
                  <div className="ih-match-item ih-match-item--in-zone ih-match-item--correct-answer">
                    <span>{correctItemForZone.text as string}</span>
                    <span className="ih-match-item__result correct">✓ 正确答案</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
      <div className="ih-match-board__actions">
        {!submitted && (
          <button className="ih-submit-btn" onClick={handleSubmit}>检查匹配</button>
        )}
        {!submitted && (
          <button className="ih-btn ih-btn--secondary" onClick={() => { setMatches({}); setSelectedItem(null); }}>重置匹配</button>
        )}
      </div>
      {submitted && <div className="ih-explanation">{explanation}</div>}
    </div>
  );
};

// ---- SequenceBlock (drag sort + move buttons + shuffle) ----

export const SequenceBlock: React.FC<InteractiveBlockProps> = ({
  block, lessonId, sessionId, sectionId, onSubmitEvent, onScore,
}) => {
  const data = getData(block);
  const instruction = (data.instruction as string) ?? "";
  const items = (data.items as Array<Record<string, unknown>>) ?? [];
  const explanation = (data.explanation as string) ?? "";
  const interactionId = block.block_data?.interaction_id as string | undefined;
  const [order, setOrder] = useState<string[]>(items.map((it) => it.item_id as string));
  const [selectedSeq, setSelectedSeq] = useState<string | null>(null);
  const [dragId, setDragId] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const dragOverRef = useRef<number | null>(null);

  const getItem = (id: string) => items.find((it) => it.item_id === id);

  const moveUp = (index: number) => {
    if (submitted || index === 0) return;
    setOrder((prev) => {
      const next = [...prev];
      [next[index - 1], next[index]] = [next[index], next[index - 1]];
      return next;
    });
  };

  const moveDown = (index: number) => {
    if (submitted || index === order.length - 1) return;
    setOrder((prev) => {
      const next = [...prev];
      [next[index], next[index + 1]] = [next[index + 1], next[index]];
      return next;
    });
  };

  const shuffle = () => {
    if (submitted) return;
    setOrder((prev) => {
      const arr = [...prev];
      for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
      }
      return arr;
    });
    setSelectedSeq(null);
  };

  const handleDragStart = (e: React.DragEvent, id: string) => {
    if (submitted) return;
    setDragId(id);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", id);
  };

  const handleDragOver = (e: React.DragEvent, _id: string, index: number) => {
    e.preventDefault();
    dragOverRef.current = index;
  };

  const handleDragLeave = () => {
    dragOverRef.current = null;
  };

  const handleDrop = (e: React.DragEvent, targetId: string) => {
    e.preventDefault();
    const sourceId = e.dataTransfer.getData("text/plain") || dragId;
    if (!sourceId || sourceId === targetId) return;
    setOrder((prev) => {
      const next = [...prev];
      const srcIdx = next.indexOf(sourceId);
      const tgtIdx = next.indexOf(targetId);
      if (srcIdx === -1 || tgtIdx === -1) return prev;
      next.splice(srcIdx, 1);
      next.splice(tgtIdx, 0, sourceId);
      return next;
    });
    setDragId(null);
    dragOverRef.current = null;
  };

  const handleDragEnd = () => {
    setDragId(null);
    dragOverRef.current = null;
  };

  const selectItem = (id: string) => {
    if (submitted) return;
    setSelectedSeq((prev) => (prev === id ? null : id));
  };

  const handleSubmit = () => {
    if (submitted) return;
    setSubmitted(true);
    // Local validation using correct_order
    let allCorrect = true;
    items.forEach((it) => {
      const expectedOrder = it.correct_order as number;
      const actualIndex = order.indexOf(it.item_id as string);
      // correct_order is 1-indexed? Let's handle both: if values start from 0 or 1
      if (expectedOrder !== actualIndex && expectedOrder !== actualIndex + 1) allCorrect = false;
    });
    if (allCorrect && onScore) onScore(12);
    onSubmitEvent({
      section_id: sectionId,
      block_id: block.block_id,
      interaction_id: interactionId ?? null,
      event_type: "sequence_submitted",
      payload: { ordered_item_ids: order },
    });
  };

  return (
    <div className="ih-interactive ih-sequence">
      <h4 className="ih-question">{instruction}</h4>
      <p className="ih-sequence__hint">拖动卡片调整顺序，也可以点击选中后使用上移/下移按钮。</p>
      <div className="ih-sequence__list">
        {order.map((id, i) => (
          <div
            key={id}
            className={`ih-sequence__item ${dragId === id ? "dragging" : ""} ${selectedSeq === id ? "selected" : ""}`}
            draggable={!submitted}
            onDragStart={(e) => handleDragStart(e, id)}
            onDragOver={(e) => handleDragOver(e, id, i)}
            onDragLeave={handleDragLeave}
            onDrop={(e) => handleDrop(e, id)}
            onDragEnd={handleDragEnd}
            onClick={() => selectItem(id)}
          >
            <span>{getItem(id)?.text as string}</span>
            <span className="ih-sequence__handle">⋮⋮</span>
          </div>
        ))}
      </div>
      {!submitted && (
        <div className="ih-sequence__controls">
          <button className="ih-submit-btn" onClick={handleSubmit}>检查顺序</button>
          <button className="ih-btn ih-btn--secondary" onClick={() => { const sel = order.findIndex(x => x === selectedSeq); if (sel >= 0) moveUp(sel); }} disabled={selectedSeq === null}>上移</button>
          <button className="ih-btn ih-btn--secondary" onClick={() => { const sel = order.findIndex(x => x === selectedSeq); if (sel >= 0) moveDown(sel); }} disabled={selectedSeq === null}>下移</button>
          <button className="ih-btn ih-btn--secondary" onClick={shuffle}>随机打乱</button>
        </div>
      )}
      {submitted && <div className="ih-explanation">{explanation}</div>}
    </div>
  );
};

// ---- FlashcardBlock (grid layout) ----

export const FlashcardBlock: React.FC<{ block: InteractiveHtmlRenderBlock }> = ({ block }) => {
  const data = getData(block);
  const cards = (data.cards as Array<Record<string, unknown>>) ?? [];
  const [flipped, setFlipped] = useState<Set<string>>(new Set());

  if (cards.length === 0) return null;

  const toggleFlip = (cardId: string) => {
    setFlipped((prev) => {
      const next = new Set(prev);
      if (next.has(cardId)) next.delete(cardId);
      else next.add(cardId);
      return next;
    });
  };

  return (
    <div className="ih-interactive ih-flashcard">
      <div className="ih-flashcard__grid">
        {cards.map((card) => {
          const isFlipped = flipped.has(card.card_id as string);
          return (
            <div
              key={card.card_id as string}
              className={`ih-flashcard__card ${isFlipped ? "flipped" : ""}`}
              onClick={() => toggleFlip(card.card_id as string)}
            >
              <div className="ih-flashcard__card-inner">
                <div className="ih-flashcard__front">{card.front as string}</div>
                <div className="ih-flashcard__back">{card.back as string}</div>
              </div>
            </div>
          );
        })}
      </div>
      <p style={{ textAlign: "center", color: "var(--ih-muted)", fontSize: 13, marginTop: 8 }}>
        点击卡片翻转查看答案
      </p>
    </div>
  );
};
