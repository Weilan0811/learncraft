interface ChartElementProps {
  title: string;
}

export function ChartElement({ title }: ChartElementProps) {
  return (
    <div className="content-block chart-placeholder">
      <h4>{title}</h4>
      <p>ECharts adapter placeholder</p>
    </div>
  );
}
