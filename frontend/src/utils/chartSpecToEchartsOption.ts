import type { ChartElementSpec } from "../types/elements";

export function chartSpecToEchartsOption(chart: ChartElementSpec): Record<string, unknown> {
  return {
    title: { text: chart.title },
    tooltip: {},
    xAxis: chart.x_axis,
    yAxis: chart.y_axis,
    series: chart.series.map((series) => ({ ...series, type: chart.chart_type }))
  };
}
