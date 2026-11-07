import type { LectureRenderModel } from "../../../types/lecture";
import { CitationList } from "../../elements/CitationList";
import { LectureSection } from "./LectureSection";

interface LectureRendererProps {
  model: LectureRenderModel;
}

export function LectureRenderer({ model }: LectureRendererProps) {
  const objectives = model.objectives ?? [];
  const sections = model.sections ?? [];
  return (
    <article className="lecture-renderer">
      <header className="lecture-header">
        <p className="eyebrow">Lecture Preview</p>
        <h2>{model.title}</h2>
        {objectives.length > 0 && (
          <div className="objectives">
            <h3>学习目标</h3>
            <ul className="objective-list">
              {objectives.map((objective, i) => (
                <li key={i}>{objective}</li>
              ))}
            </ul>
          </div>
        )}
      </header>
      <div className="lecture-content">
        {sections.map((section) => (
          <LectureSection key={section.id} section={section} />
        ))}
      </div>
      <footer className="lecture-footer">
        <CitationList citations={[]} />
      </footer>
    </article>
  );
}
