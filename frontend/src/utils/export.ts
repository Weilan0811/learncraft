export function resolveExportLabel(exportType: string): string {
  if (exportType === "slide_json") return "Slide JSON";
  return exportType.toUpperCase();
}
