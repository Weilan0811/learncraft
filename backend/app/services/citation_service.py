from app.schemas.elements import Citation
from app.schemas.state import RetrievedChunk


class CitationService:
    def from_chunks(self, chunks: list[RetrievedChunk]) -> list[Citation]:
        # TODO(P1-citations): Deduplicate sources, preserve page/section
        # metadata, and format citations for lecture, PDF, and slide views.
        return [
            Citation(
                id=f"citation_{chunk.id}",
                title=chunk.source_title,
                source_id=chunk.source_id,
                source_title=chunk.source_title,
                content=chunk.content,
            )
            for chunk in chunks
        ]
