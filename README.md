# THE SHIELD

AI-powered software requirement analysis and ambiguity detection system.

## Key Features

- `POST /analyze` FastAPI endpoint
- Mixed-format requirement extraction (bullets, multi-line lists, or paragraphs)
- Per-requirement analysis with aggregated overall status
- Requirement parsing (`actor`, `action`, `object`, `conditions`)
- Domain detection and domain-appropriate, high-level decision questions
- Validated clarification questions (de-duplicated and filtered for quality)
- Login and meeting workspace with saved history
- Meeting-level open/resolved clarification tracking
- Multi-speaker capture workflow via speaker-tagged audio segments
- Automatic speaker labeling mode (voice-signature clustering, browser best effort)
- PDF minutes upload and continuation from previous meetings
- Meeting transcript export as downloadable `.txt`
- LLM summarization modes:
  - `local` (offline/local-first using fine-tuned Phi-3.5)
  - `ollama` (local Ollama instance)
  - deterministic fallback when model unavailable
- Enhanced frontend workflow page for auth, meeting records, PDF upload, and analysis

## Project Structure

- `backend/`: FastAPI service and business logic
- `frontend/`: static UI
- `tests/`: pytest test cases
- `docs/`: PRD, architecture, analysis notes, and task checklist

## Local Setup

1. Create and activate a Python environment inside `backend/`.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set environment variables in `backend/.env`:

```bash
LLM_MODE=local
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2
CORS_ORIGINS=*
```

4. Run backend:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Open `frontend/index.html` and set API Base URL to `http://localhost:8000`.

## Meeting Workflow

1. Register/Login in the frontend.
2. Create or select a meeting.
3. Add input in any format:
   - paragraph
   - bullet points
   - multi-speaker speech segments
4. Optionally upload PDF minutes to keep continuity.
5. Run meeting analysis.
6. Review:
   - extracted requirements
   - domain-focused questions
   - open vs resolved clarifications
   - saved meeting history
7. Add clarifications in subsequent turns; resolved questions are highlighted automatically.

## Core API Endpoints

- `POST /analyze` - standalone requirement analysis
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `GET /meetings`
- `POST /meetings`
- `GET /meetings/{meeting_id}`
- `POST /meetings/{meeting_id}/minutes/pdf`
- `POST /meetings/{meeting_id}/analyze`
- `GET /meetings/{meeting_id}/transcript`

## Example: Analyze

```json
{ "text": "User logs into the system." }
```

Response:

```json
{
  "status": "gap_detected",
  "message": "Requirement has domain gaps that need clarification (4 detected).",
  "parsed": {
    "actor": "user",
    "action": "logs into",
    "obj": "the system",
    "conditions": null
  },
  "missing_fields": [],
  "domain_gaps": ["login: authentication method"],
  "domains": ["security"],
  "questions": [
    "Which authentication methods should be supported (password, OAuth, SSO, MFA)?"
  ],
  "llm_summary": "..."
}
```

## Deployment (Render)

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 10000
```

Set environment variable:

```bash
LLM_MODE=local
OLLAMA_URL=xxxx
```
