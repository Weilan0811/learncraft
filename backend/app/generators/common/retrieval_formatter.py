RETRIEVAL_CONTENT_LIMIT = 500


def retrieval_snapshot(chunks: list) -> list[dict[str, object]]:
    return [{**chunk.model_dump(mode="json"),
             "shown_content": chunk.content[:RETRIEVAL_CONTENT_LIMIT],
             "shown_start": 0, "shown_end": min(len(chunk.content), RETRIEVAL_CONTENT_LIMIT)}
            for chunk in chunks]


def format_retrieval_results(chunks: list, *, max_chars_per_chunk: int = RETRIEVAL_CONTENT_LIMIT) -> str:
    if not chunks:
        return "No retrieval results."

    formatted = []
    for i, chunk in enumerate(chunks, 1):
        chunk_id = getattr(chunk, "id", f"chunk_{i}")
        source_title = getattr(chunk, "source_title", "")
        score = getattr(chunk, "score", 0.0)
        content = getattr(chunk, "content", "")[:max_chars_per_chunk]
        formatted.append(f"[chunk_id={chunk_id}]")
        if source_title:
            formatted.append(f"source_title: {source_title}")
        formatted.append(f"score: {score}")
        formatted.append(f"content: {content}")
        formatted.append("")

    return "\n".join(formatted)
