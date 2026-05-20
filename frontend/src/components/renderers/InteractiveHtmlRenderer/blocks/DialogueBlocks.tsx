import React, { useState, useRef, useEffect } from "react";
import type { InteractiveHtmlRenderBlock } from "../../../../types/interactiveHtml";
import type { SubmitEventRequest } from "../../../../types/interactiveHtml";

function getData(block: InteractiveHtmlRenderBlock): Record<string, unknown> {
  return (block.block_data ?? {}) as Record<string, unknown>;
}

interface DialogueBlockProps {
  block: InteractiveHtmlRenderBlock;
  lessonId: string;
  sessionId: string;
  sectionId: string;
  onSubmitEvent: (event: SubmitEventRequest) => void;
  onScore?: (points: number) => void;
}

type ChatMessage = { role: "ai" | "user" | "system"; text: string };

// ---- SocraticChatBlock (bubble-based with typing indicator) ----

export const SocraticChatBlock: React.FC<DialogueBlockProps> = ({
  block, lessonId, sessionId, sectionId, onSubmitEvent, onScore,
}) => {
  const data = getData(block);
  const goal = (data.goal as string) ?? "";
  const rounds = (data.rounds as Array<Record<string, unknown>>) ?? [];
  const interactionId = block.block_data?.interaction_id as string | undefined;
  const [currentRound, setCurrentRound] = useState(0);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [done, setDone] = useState(false);
  const [customInput, setCustomInput] = useState("");
  const chatRef = useRef<HTMLDivElement>(null);

  const scrollChat = () => {
    setTimeout(() => {
      if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }, 50);
  };

  const addMessage = (role: ChatMessage["role"], text: string) => {
    setMessages((prev) => [...prev, { role, text }]);
    scrollChat();
  };

  // Initialize chat
  useEffect(() => {
    if (rounds.length > 0 && messages.length === 0) {
      addMessage("system", "对话导师已就绪。选择一个回答，或输入你的想法。");
      const firstRound = rounds[0];
      addMessage("ai", firstRound.question as string);
    }
  }, []);

  const round = rounds[currentRound];
  const roundOptions = (round?.options as Array<Record<string, unknown>>) ?? [];
  const roundId = round?.round_id as string;

  const handleSelect = (optionId: string) => {
    if (isTyping || done) return;
    const option = roundOptions.find((o) => o.option_id === optionId);
    if (!option) return;

    addMessage("user", option.text as string);
    setIsTyping(true);

    setTimeout(() => {
      setIsTyping(false);
      addMessage("ai", option.feedback as string);
      if ((option.is_preferred as boolean) && onScore) onScore(5);

      onSubmitEvent({
        section_id: sectionId,
        block_id: block.block_id,
        interaction_id: interactionId ?? null,
        event_type: "socratic_round_answered",
        payload: { selected_option_ids: [optionId] },
      });

      if (currentRound < rounds.length - 1) {
        setCurrentRound((r) => r + 1);
        const nextRound = rounds[currentRound + 1];
        setTimeout(() => addMessage("ai", nextRound.question as string), 300);
      } else {
        setTimeout(() => {
          addMessage("system", "对话导师环节完成！你已经探索了所有关键概念。");
          setDone(true);
          if (onScore) onScore(5);
        }, 400);
      }
    }, 500 + Math.random() * 400);
  };

  const handleCustomSend = () => {
    const value = customInput.trim();
    if (!value || isTyping || done) return;
    addMessage("user", value);
    setCustomInput("");
    setIsTyping(true);

    setTimeout(() => {
      setIsTyping(false);
      addMessage("ai", "有道理。可以继续思考：对象、目标、资料和格式这些上下文信息，如何影响回答的质量。");
      if (onScore) onScore(3);
      onSubmitEvent({
        section_id: sectionId,
        block_id: block.block_id,
        interaction_id: interactionId ?? null,
        event_type: "socratic_round_answered",
        payload: { answer_text: value },
      });
    }, 500 + Math.random() * 400);
  };

  const reset = () => {
    setMessages([]);
    setCurrentRound(0);
    setDone(false);
    setIsTyping(false);
    setCustomInput("");
    const firstRound = rounds[0];
    setTimeout(() => {
      addMessage("system", "对话已重新开始。");
      if (firstRound) addMessage("ai", firstRound.question as string);
    }, 100);
  };

  return (
    <div className="ih-interactive ih-socratic-chat">
      <div className="ih-socratic-layout">
        {/* Chat box with bubbles */}
        <div className="ih-chat-box" ref={chatRef}>
          {messages.map((msg, i) => (
            <div key={i} className={`ih-bubble ih-bubble--${msg.role}`}>{msg.text}</div>
          ))}
          {isTyping && (
            <div className="ih-typing"><i /><i /><i /></div>
          )}
        </div>

        {/* Control panel */}
        <div className="ih-socratic-panel">
          {!done ? (
            <>
              <h4 className="ih-socratic-panel__title">
                第 {currentRound + 1} 轮，共 {rounds.length} 轮
              </h4>
              <p className="ih-socratic-panel__guide">选择一个回答，或输入你的想法。</p>
              <div className="ih-options">
                {roundOptions.map((opt) => (
                  <button
                    key={opt.option_id as string}
                    className={`ih-option${opt.is_preferred ? " ih-option--preferred" : ""}`}
                    disabled={isTyping}
                    onClick={() => handleSelect(opt.option_id as string)}
                  >
                    {opt.text as string}
                  </button>
                ))}
              </div>
              <div className="ih-socratic-input-row">
                <input
                  type="text"
                  placeholder="也可以输入你的想法…"
                  value={customInput}
                  onChange={(e) => setCustomInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") handleCustomSend(); }}
                  disabled={isTyping}
                />
                <button className="ih-btn ih-btn--primary" onClick={handleCustomSend} disabled={isTyping || !customInput.trim()}>
                  发送
                </button>
              </div>
              <div className="ih-socratic-panel__goal">
                <strong>对话目标：</strong> {goal}
              </div>
            </>
          ) : (
            <div className="ih-socratic-done">
              <p>全部 {rounds.length} 轮对话已完成，思考很深入！</p>
            </div>
          )}
          <div style={{ marginTop: 12 }}>
            <button className="ih-btn ih-btn--secondary" onClick={reset}>重新开始</button>
          </div>
        </div>
      </div>
    </div>
  );
};

// ---- ScenarioBlock (dual-column: scene + chat log) ----

export const ScenarioBlock: React.FC<DialogueBlockProps> = ({
  block, lessonId, sessionId, sectionId, onSubmitEvent, onScore,
}) => {
  const data = getData(block);
  const scenarioTitle = (data.scenario_title as string) ?? "";
  const background = (data.background as string) ?? "";
  const role = data.role as string | undefined;
  const scenes = (data.scenes as Array<Record<string, unknown>>) ?? [];
  const interactionId = block.block_data?.interaction_id as string | undefined;
  const [currentScene, setCurrentScene] = useState(0);
  const [chatLog, setChatLog] = useState<ChatMessage[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [done, setDone] = useState(false);
  const chatRef = useRef<HTMLDivElement>(null);

  const logMessage = (role: ChatMessage["role"], text: string) => {
    setChatLog((prev) => [...prev, { role, text }]);
    setTimeout(() => {
      if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }, 50);
  };

  // Initialize
  useEffect(() => {
    if (scenes.length > 0 && chatLog.length === 0) {
      logMessage("system", "情景教学开始，你扮演课程设计师。");
      logMessage("ai", `当前任务：${scenes[0].task as string}`);
    }
  }, []);

  const scene = scenes[currentScene];
  if (!scene) return null;

  const sceneChoices = (scene.choices as Array<Record<string, unknown>>) ?? [];
  const sceneId = scene.scene_id as string;

  const handleChoose = (choiceId: string) => {
    if (isTyping || done) return;
    const choice = sceneChoices.find((c) => c.choice_id === choiceId);
    if (!choice) return;

    logMessage("user", `我选择：${choice.text as string}`);
    setIsTyping(true);

    setTimeout(() => {
      setIsTyping(false);
      logMessage("ai", choice.feedback as string);
      if ((choice.is_preferred as boolean) && onScore) onScore(5);

      onSubmitEvent({
        section_id: sectionId,
        block_id: block.block_id,
        interaction_id: interactionId ?? null,
        event_type: "scenario_choice_selected",
        payload: { selected_option_ids: [choiceId] },
      });

      if (currentScene < scenes.length - 1) {
        setCurrentScene((s) => s + 1);
        const nextScene = scenes[currentScene + 1];
        setTimeout(() => logMessage("system", (nextScene.context ?? nextScene.task) as string), 400);
      } else {
        setTimeout(() => {
          logMessage("system", "情景任务完成！回顾你的教学设计决策。");
          setDone(true);
          if (onScore) onScore(5);
        }, 400);
      }
    }, 500 + Math.random() * 400);
  };

  const reset = () => {
    setCurrentScene(0);
    setChatLog([]);
    setDone(false);
    setIsTyping(false);
    setTimeout(() => {
      logMessage("system", "情景已重新开始。");
      logMessage("ai", `当前任务：${scenes[0].task as string}`);
    }, 100);
  };

  return (
    <div className="ih-interactive ih-scenario">
      <h3 className="ih-scenario-scene__title">{scenarioTitle}</h3>

      <div className="ih-scenario-layout">
        {/* Scene panel */}
        <div className="ih-scenario-scene">
          <div className="ih-scenario-scene__context">
            <strong>背景：</strong> {background}
            {role && <p style={{ marginTop: 8 }}><strong>你的角色：</strong> {role}</p>}
          </div>
          {!done ? (
            <>
              <p className="ih-scenario-scene__task">
                <strong>任务 {currentScene + 1}：</strong> {scene.task as string}
              </p>
              <div className="ih-options">
                {sceneChoices.map((choice) => (
                  <button
                    key={choice.choice_id as string}
                    className={`ih-option${choice.is_preferred ? " ih-option--preferred" : ""}`}
                    disabled={isTyping}
                    onClick={() => handleChoose(choice.choice_id as string)}
                  >
                    {choice.text as string}
                  </button>
                ))}
              </div>
            </>
          ) : (
            <div className="ih-scenario-done">
              <p>情景任务完成，你已做出 {scenes.length} 项教学设计决策。</p>
            </div>
          )}
          <div style={{ marginTop: 14 }}>
            <button className="ih-btn ih-btn--secondary" onClick={reset}>重新开始</button>
          </div>
        </div>

        {/* Chat log panel */}
        <div className="ih-scenario-chat" ref={chatRef}>
          <h4 className="ih-scenario-chat__title">对话记录</h4>
          {chatLog.map((msg, i) => (
            <div key={i} className={`ih-bubble ih-bubble--${msg.role}`}>{msg.text}</div>
          ))}
          {isTyping && <div className="ih-typing"><i /><i /><i /></div>}
        </div>
      </div>
    </div>
  );
};
