# Changelog

All notable changes to this project are documented in this file. Dates are in UTC+8.

## 2026-11-07

### Fixed

- **images**: Make the image pipeline survive failures and disabled images. Rewrote the Bailian image service on the DashScope native async text2image API (the compatible-mode endpoint returns 404 for image models), added 429 throttling backoff, clamped sizes to the 512-1440 window the API enforces, plan no image slots when `include_images=false`, and replaced failed image slots with local SVG placeholders (original errors kept in metadata) instead of failing the whole task. (`467fba5`)

### Added

- **progress**: Stream generation progress over SSE with per-unit persistence. New `GET /api/content-generation/tasks/{task_id}/events/stream` endpoint pushes lightweight snapshots every ~600ms with keep-alive and terminal frames; unit results in the parallel stage are persisted one by one so partial previews appear mid-run; the frontend subscribes via EventSource with polling fallback and refreshes only when counters change; a preview error boundary keeps a renderer crash from unmounting the progress strip. (`1054cf2`)

### Docs

- **readme**: Rewrote the root README as a project showcase (one-line positioning, content type table, user-facing highlights, zero-config quick start, compact workflow diagram, roadmap) and restructured `backend/README.md` for developers (architecture overview with mermaid graph, direct/unit-loop comparison, engineering design sections on persistence / degradation / streaming / provider factory / schema source of truth, API summary, regrouped conventions). (`10b22e3`)
- Added this changelog.
