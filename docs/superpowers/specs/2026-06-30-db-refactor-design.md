# Content Generation DB Refactor Design

## Goal

Refactor backend persistence to match `docs/content_generator_agent_db_design.md` while preserving migratable historical data through Alembic.

## Scope

The Agent database keeps `content_generation_task`, `content_generation_artifact`, `content_generation_reference`, `content_generation_asset`, and `knowledge_chunk_cache`. Active use of `content_generation_event` and `content_generation_metric` is removed; their API routes remain as empty compatible responses.

## Architecture

`content_generation_task` is lifecycle-only. Generated payloads are stored in `content_generation_artifact`; preview, partial preview, unit preview, unit text, and export read the latest matching artifact.

References are split between `knowledge_chunk_cache`, keyed by `sha256(normalized_text)`, and `content_generation_reference`, keyed by task/unit/source relation. Reference writes cache text first, then upsert the relation.

The Alembic migration uses replacement tables to preserve task summaries, artifacts, reference excerpts as cached text, and asset records, then removes event and metric tables.

## Testing

Tests cover the slim schema, cached reference deduplication, artifact-backed previews and exports, compatible event/metric responses, and the full backend API regression suite.
