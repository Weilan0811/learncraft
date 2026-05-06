interface ChartElementProps {
  title: string;
}

export function ChartElement({ title }: ChartElementProps) {
  // TODO(P1-chart): Accept ChartElementSpec and render it with ECharts, with
  // responsive resize and static image export for PDF/Slide embedding.
  return (
    <div className="content-block chart-placeholder">
      <h4>{title}</h4>
      <p>ECharts adapter placeholder</p>
    </div>
  );
}
