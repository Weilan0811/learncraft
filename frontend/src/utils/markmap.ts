export function normalizeMindmapMarkdown(
  markdown: string | null | undefined,
  fallbackTitle = "思维导图",
): string {
  const source = (markdown ?? "").trim();

  if (!source) {
    return `# ${fallbackTitle}`;
  }

  // 已经有一级标题，直接交给 Markmap
  if (/^\s*#\s+/m.test(source)) {
    return source;
  }

  // 只有二级/三级标题或列表时，补一个根节点
  if (/^\s*#{2,6}\s+/m.test(source) || /^\s*[-*+]\s+/m.test(source)) {
    return `# ${fallbackTitle}\n${source}`;
  }

  // 普通文本兜底成列表结构
  const lines = source
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => `- ${line}`);

  return `# ${fallbackTitle}\n${lines.join("\n")}`;
}
