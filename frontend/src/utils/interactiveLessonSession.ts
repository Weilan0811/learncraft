import type { CreateSessionResponse } from "../types/interactiveHtml";

export function normalizeLessonId(lessonId: string): string {
  return lessonId.startsWith("partial_lesson_") ? lessonId.slice("partial_".length) : lessonId;
}

function sessionKeys(lessonId: string): string[] {
  const canonicalId = normalizeLessonId(lessonId);
  const ids = [canonicalId];
  if (canonicalId.startsWith("lesson_")) ids.push(`partial_${canonicalId}`);
  return ids.map((id) => `interactive-html-session:${id}`);
}

export function readStoredSession(lessonId: string): CreateSessionResponse | null {
  const canonicalId = normalizeLessonId(lessonId);
  for (const key of sessionKeys(canonicalId)) {
    try {
      const raw = localStorage.getItem(key);
      if (!raw) continue;
      const parsed = JSON.parse(raw) as Partial<CreateSessionResponse>;
      if (parsed.session_id && parsed.lesson_id && normalizeLessonId(parsed.lesson_id) === canonicalId) {
        return { session_id: parsed.session_id, lesson_id: canonicalId, state: parsed.state ?? {} };
      }
    } catch {
      localStorage.removeItem(key);
    }
  }
  return null;
}

export function storeSession(session: CreateSessionResponse): void {
  const [key, partialKey] = sessionKeys(session.lesson_id);
  localStorage.setItem(key, JSON.stringify({ ...session, lesson_id: normalizeLessonId(session.lesson_id) }));
  if (partialKey) localStorage.removeItem(partialKey);
}

export function clearStoredSession(lessonId: string): void {
  for (const key of sessionKeys(lessonId)) localStorage.removeItem(key);
}
