import type { ElementType, MvpContentType } from "./content";

export interface OutlineSection {
  id: string;
  title: string;
  goal: string;
  key_points: string[];
  recommended_elements: ElementType[];
  estimated_minutes?: number | null;
  assessment_points: string[];
  citations: string[];
}

export interface Outline {
  id: string;
  content_type: MvpContentType;
  title: string;
  audience?: string | null;
  learning_objectives: string[];
  sections: OutlineSection[];
  metadata: Record<string, unknown>;
}
