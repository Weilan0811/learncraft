interface CitationListProps {
  citations: string[];
}

export function CitationList({ citations }: CitationListProps) {
  return (
    <section className="citation-list">
      <h3>引用来源</h3>
      {citations.length === 0 ? (
        <p>引用来源将在 Retriever 和 CitationService 实现后展示。</p>
      ) : (
        <ol>
          {citations.map((citation) => (
            <li key={citation}>{citation}</li>
          ))}
        </ol>
      )}
    </section>
  );
}
