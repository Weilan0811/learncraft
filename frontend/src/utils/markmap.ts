export function normalizeMindmapMarkdown(markdown: string): string {
  // TODO(P1-mindmap): Sanitize generated Markdown and normalize heading depth
  // before passing it to Markmap.
  return markdown.trim() || "# Mindmap";
}
