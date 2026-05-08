import type { LectureRenderModel } from "../../../types/lecture";
import { CitationList } from "../../elements/CitationList";
import { LectureSection } from "./LectureSection";

interface LectureRendererProps {
  model: LectureRenderModel;
}

export function LectureRenderer({ model }: LectureRendererProps) {
  return (
    <article className="lecture-renderer">
      <header className="lecture-header">
        <p className="eyebrow">Lecture Preview</p>
        <h2>{model.title}</h2>
        {model.objectives.length > 0 && (
          <div className="objectives">
            <h3>学习目标</h3>
            <ul className="objective-list">
              {model.objectives.map((objective, i) => (
                <li key={i}>{objective}</li>
              ))}
            </ul>
          </div>
        )}
      </header>
      <div className="lecture-content">
        {model.sections.map((section) => (
          <LectureSection key={section.id} section={section} />
        ))}
      </div>
      <footer className="lecture-footer">
        <CitationList citations={[]} />
      </footer>
    </article>
  );
}
