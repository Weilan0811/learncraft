export function resolveExportLabel(exportType: string): string {
  // TODO(MVP-export): Centralize export labels, extensions, MIME types, and
  // download filename generation for all supported export formats.
  if (exportType === "slide_json") return "Slide JSON";
  return exportType.toUpperCase();
}
