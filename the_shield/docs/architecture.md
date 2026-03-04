# RequiMind AI Architecture (Enhanced MVP)

## High-Level Components

- Frontend: static HTML/CSS/JS client with login, meeting management, speaker tracking, and PDF upload.
- Backend: FastAPI service exposing standalone analysis and meeting workflow endpoints.
- Service Layer: extractor, parser, gap detector, domain detector, question generator, summary engine.
- Capability Insight Layer: NLP-driven complexity scoring, service/business opportunity detection, stakeholder dissemination guidance, and visualization recommendations.
- Auth Layer: token-based login and protected meeting endpoints.
- Persistence Layer: JSON-backed storage for users, meetings, history, open/resolved questions.
- LLM Layer: local/offline-first Ollama option, Gemini option, deterministic fallback.

## Request Lifecycle

### Standalone Analysis

1. Client sends text to `POST /analyze`.
2. Extractor converts points/paragraphs to requirement items.
3. Parser + gap detector analyze each item.
4. Domain detector identifies domain context.
5. Question generator creates decision-focused clarifications.
6. LLM service summarizes using configured mode.
7. API returns aggregated and per-item analysis.

### Meeting Workflow

1. User authenticates (`/auth/register` or `/auth/login`).
2. User creates/selects a meeting (`/meetings`).
3. User sends:
   - typed meeting notes
   - speaker-tagged transcript segments
   - optional PDF minutes upload
4. `POST /meetings/{id}/analyze` runs full analysis on current context.
5. Meeting service compares new context with previous open questions.
6. Clarifications are split into:
   - open questions
   - resolved questions (highlighted)
7. History is saved for continuity across meetings.

## Backend Module Boundaries

- `app/main.py`: FastAPI app bootstrap and middleware.
- `app/routes/analyze.py`: standalone analysis endpoint.
- `app/routes/auth.py`: register/login/me endpoints.
- `app/routes/meetings.py`: meeting CRUD, PDF upload, contextual analysis.
- `app/models/*`: request and response schemas.
- `app/services/*`: extraction, parsing, domains, questions, auth, meetings, LLM.
- `app/services/capability_insight_service.py`: deterministic NLP capability insight generation.
- `app/core/*`: settings and provider configuration.
- `app/database/db.py`: persistent JSON storage interface.
- `app/utils/*`: reusable helpers and text utilities.

## Scalability and Reliability Notes

- API remains stateless at compute layer; persisted meeting records are file-backed for MVP.
- Deterministic fallback summary avoids hard dependency on external model providers.
- Offline/local LLM mode reduces external dependency when internet is unavailable.
- Question generation is filtered for quality and de-duplicated.
- Capability insights are deterministic and local, reducing dependency on external LLM providers.

## Next Extension Path

- Replace JSON storage with PostgreSQL and proper session tables.
- Add true speaker diarization pipeline for multi-speaker audio streams.
- Add role-based authorization and admin controls.
- Add retrieval over historical minutes for long-running projects.
