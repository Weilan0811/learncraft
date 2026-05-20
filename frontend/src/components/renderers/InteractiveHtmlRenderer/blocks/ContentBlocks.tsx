import React from "react";
import type { InteractiveHtmlRenderBlock } from "../../../../types/interactiveHtml";

function getData(block: InteractiveHtmlRenderBlock): Record<string, unknown> {
  return (block.block_data ?? {}) as Record<string, unknown>;
}

const CALLOUT_LABELS: Record<string, string> = {
  tip: "提示",
  important: "重要",
  warning: "注意",
  reflection: "思考",
};

export const HeadingBlock: React.FC<{ block: InteractiveHtmlRenderBlock }> = ({ block }) => {
  const data = getData(block);
  const level = (data.level as number) ?? 2;
  const text = (data.text as string) ?? "";
  if (level === 3) return <h3 className="ih-heading">{text}</h3>;
  if (level === 4) return <h4 className="ih-heading">{text}</h4>;
  return <h2 className="ih-heading">{text}</h2>;
};

export const ParagraphBlock: React.FC<{ block: InteractiveHtmlRenderBlock }> = ({ block }) => {
  const data = getData(block);
  const text = (data.text as string) ?? "";
  return (
    <div className="ih-paragraph">
      {text.split("\n").map((line, i) => (
        <p key={i}>{line}</p>
      ))}
    </div>
  );
};

export const ConceptCardBlock: React.FC<{ block: InteractiveHtmlRenderBlock }> = ({ block }) => {
  const data = getData(block);
  const explanation = (data.explanation as string) ?? "";
  const keyTerms = (data.key_terms as string[]) ?? [];
  return (
    <div className="ih-concept-card">
      <div className="ih-concept-card__explanation">{explanation}</div>
      {keyTerms.length > 0 && (
        <div className="ih-concept-card__terms">
          {keyTerms.map((term) => (
            <span key={term} className="ih-concept-card__term">{term}</span>
          ))}
        </div>
      )}
    </div>
  );
};

export const CalloutBlock: React.FC<{ block: InteractiveHtmlRenderBlock }> = ({ block }) => {
  const data = getData(block);
  const variant = (data.variant as string) ?? "tip";
  const content = (data.content as string) ?? "";
  const label = CALLOUT_LABELS[variant] ?? variant;
  return (
    <div className={`ih-callout ih-callout--${variant}`}>
      <span className="ih-callout__label">{label}</span>
      <p>{content}</p>
    </div>
  );
};

export const ExampleBlock: React.FC<{ block: InteractiveHtmlRenderBlock }> = ({ block }) => {
  const data = getData(block);
  return (
    <div className="ih-example">
      <h4>{(data.scenario as string) ?? "示例"}</h4>
      <p className="ih-example__explanation">{(data.explanation as string) ?? ""}</p>
      <p className="ih-example__takeaway"><strong>要点总结：</strong> {(data.takeaway as string) ?? ""}</p>
    </div>
  );
};

export const SummaryBlock: React.FC<{ block: InteractiveHtmlRenderBlock }> = ({ block }) => {
  const data = getData(block);
  const points = (data.points as string[]) ?? [];
  const useGrid = points.length >= 3;
  return (
    <div className="ih-summary">
      <h3>本节要点</h3>
      {useGrid ? (
        <div className="ih-summary__grid">
          {points.map((point, i) => (
            <div key={i} className="ih-summary__card">
              <span className="ih-summary__card-num">{i + 1}</span>
              <p>{point}</p>
            </div>
          ))}
        </div>
      ) : (
        <ul>
          {points.map((point, i) => (
            <li key={i}>{point}</li>
          ))}
        </ul>
      )}
    </div>
  );
};
