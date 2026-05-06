export function normalizeMindmapMarkdown(markdown: string): string {
  return markdown.trim() || "# Mindmap";
}
