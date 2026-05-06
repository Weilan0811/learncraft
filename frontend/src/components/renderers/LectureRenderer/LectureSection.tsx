import type { LectureRenderSection } from "../../../types/lecture";
import { ChartBlock } from "./blocks/ChartBlock";
import { ImageBlock } from "./blocks/ImageBlock";
import { MindmapBlock } from "./blocks/MindmapBlock";
import { QuizBlock } from "./blocks/QuizBlock";
import { TableBlock } from "./blocks/TableBlock";
import { TextBlock } from "./blocks/TextBlock";

interface LectureSectionProps {
  section: LectureRenderSection;
}

export function LectureSection({ section }: LectureSectionProps) {
  return (
    <section className="lecture-section">
      <h3>{section.title}</h3>
      {section.render_blocks.map((block) => {
        if (block.type === "image") return <ImageBlock key={block.id} block={block} />;
        if (block.type === "chart") return <ChartBlock key={block.id} block={block} />;
        if (block.type === "mindmap") return <MindmapBlock key={block.id} block={block} />;
        if (block.type === "table") return <TableBlock key={block.id} block={block} />;
        if (block.type === "quiz") return <QuizBlock key={block.id} block={block} />;
        return <TextBlock key={block.id} block={block} />;
      })}
    </section>
  );
}
