# RequiMind AI MVP TODO

## 1. Project Setup

- [x] Create project directory scaffold.
- [x] Add backend dependencies to `backend/requirements.txt`.
- [x] Add `.gitignore` entries for Python, env, cache, venv, and editor files.
- [x] Document local run steps in `README.md`.

## 2. Backend Core (FastAPI)

- [x] Create FastAPI app entry in `backend/app/main.py`.
- [x] Add app settings loader in `backend/app/core/settings.py`.
- [x] Add Gemini config helper in `backend/app/core/config.py`.
- [x] Register API routes and CORS handling.

## 3. Data Models

- [x] Create request model (`AnalyzeRequest`) with validation.
- [x] Create response model (`AnalyzeResponse`) with structured fields.
- [x] Define typed parse output model for actor/action/object/conditions.

## 4. Service Layer

- [x] Implement text normalization utility.
- [x] Implement requirement parser (actor/action/object/conditions extraction).
- [x] Implement completeness and domain gap detector.
- [x] Implement clarification question generator.
- [x] Implement Gemini summary service with fallback summary.

## 5. API Endpoint

- [x] Implement `POST /analyze` in `backend/app/routes/analyze.py`.
- [x] Wire parser, gap detector, question generator, and LLM service.
- [x] Return status: `complete`, `incomplete`, or `gap_detected`.
- [x] Ensure response includes message, questions, and summary.

## 6. Frontend (MVP UI)

- [x] Build `frontend/index.html` with requirement input and output panels.
- [x] Add `frontend/style.css` for readable responsive layout.
- [x] Add `frontend/script.js` to call `/analyze` and render results.

## 7. Testing

- [x] Add parser tests (`tests/test_parser.py`).
- [x] Add endpoint tests (`tests/test_analyze.py`).
- [x] Cover cases: complete requirement, missing actor, login gap detection.

## 8. Documentation

- [x] Capture PRD in `docs/PRD.md`.
- [x] Write requirement analysis notes in `docs/research_notes.md`.
- [x] Add architecture notes in `docs/architecture.md`.
- [x] Add setup/deploy instructions in `README.md`.

## 9. Deployment Readiness

- [x] Add `.env` template variables (GEMINI_API_KEY, GEMINI_MODEL).
- [ ] Confirm Render start command.
- [x] Keep backend stateless and cloud-friendly.

## 10. Quality Gate

- [x] Run tests and confirm pass.
- [x] Verify API behavior manually with sample payloads.
- [x] Validate fallback summary when Gemini key is missing.
