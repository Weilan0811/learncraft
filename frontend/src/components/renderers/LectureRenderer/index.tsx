import type { LectureRenderModel } from "../../../types/lecture";
import { CitationList } from "../../elements/CitationList";
import { LectureSection } from "./LectureSection";

interface LectureRendererProps {
  model: LectureRenderModel;
}

export function LectureRenderer({ model }: LectureRendererProps) {
  return (
    <article className="lecture-renderer">
      <header>
        <p className="eyebrow">Lecture Preview</p>
        <h2>{model.title}</h2>
        <ul className="objective-list">
          {model.objectives.map((objective) => (
            <li key={objective}>{objective}</li>
          ))}
        </ul>
      </header>
      {model.sections.map((section) => (
        <LectureSection key={section.id} section={section} />
      ))}
      <CitationList citations={[]} />
    </article>
  );
}
