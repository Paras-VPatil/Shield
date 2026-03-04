# RequiMind AI

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
- NLP capability insights for:
  - complex-problem investigation and disciplined decision support
  - service improvement opportunity discovery
  - business opportunity identification
  - stakeholder communication/dissemination planning
- LLM summarization modes:
  - `auto` (try local Ollama, then Gemini, then fallback)
  - `ollama` / `local` (offline/local-first)
  - `gemini`
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
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-1.5-flash
LLM_MODE=local
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2
CORS_ORIGINS=*
MONGODB_URI=mongodb://127.0.0.1:27017
MONGODB_DB_NAME=the_shield
```

4. Initialize MongoDB schema and indexes:

```bash
python scripts/init_mongo_schema.py
```

Or with `mongosh` (no Python dependency):

```bash
mongosh "mongodb://127.0.0.1:27017/admin?replicaSet=rs0" scripts/init_mongo_schema.js
```

5. Run backend:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. Open `frontend/index.html` and set API Base URL to `http://localhost:8000`.

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

## Local NLP Model Training (Gemini-Reduction Path)

- Recommended base model for fine-tuning: `microsoft/Phi-3.5-mini-instruct` (permissive MIT license).
- NLP embedding model for retrieval/reranking: `sentence-transformers/all-MiniLM-L6-v2` (Apache-2.0).
- Training script: `backend/scripts/train_requirement_nlp_lora.py`
- Training dependency file: `backend/requirements-train.txt`
- Detailed plan: `docs/model_training_plan.md`

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
GEMINI_API_KEY=xxxxx
```
