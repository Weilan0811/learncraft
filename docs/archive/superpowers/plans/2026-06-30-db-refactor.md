# Content Generation DB Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild content generation persistence around slim tasks, artifacts, reference cache, and lightweight assets while preserving migratable legacy data.

**Architecture:** SQLModel models define the final five-table Agent schema. `SQLModelTaskRepository` owns task lifecycle and artifact-backed read/write behavior. `ArtifactRepository` writes artifacts and cached references only; event and metric table writes are removed.

**Tech Stack:** Python 3.13, FastAPI, SQLModel, SQLAlchemy, Alembic, pytest, SQLite test database, MySQL-compatible DDL.

---

## Tasks

- [x] Update SQLModel models and metadata exports to the final five Agent tables.
- [x] Add `KnowledgeChunkCache` and cached reference write helpers.
- [x] Rewrite task persistence so task rows store lifecycle data only.
- [x] Move preview, partial preview, units, unit text, and export reads to artifacts.
- [x] Keep event and metric routes compatible with empty responses while removing persistence.
- [x] Add Alembic replacement-table migration preserving legacy task, artifact, reference, and asset data.
- [x] Update API and repository tests for the refactored schema.
- [x] Verify full backend test suite and Alembic upgrade.
