import type { ChartElementSpec } from "../types/elements";

export function chartSpecToEchartsOption(chart: ChartElementSpec): Record<string, unknown> {
  // TODO(P1-chart): Complete bar/line/pie option generation, validation,
  // color/theme mapping, labels, legends, and export-safe defaults.
  return {
    title: { text: chart.title },
    tooltip: {},
    xAxis: chart.x_axis,
    yAxis: chart.y_axis,
    series: chart.series.map((series) => ({ ...series, type: chart.chart_type }))
  };
}
