# Local NLP Model Training Plan (Gemini Reduction + Paper Track)

## Objective

Build a local NLP model stack for requirement engineering so the system can:

- Investigate/analyze/visualize complex requirement problems.
- Detect service and business improvement opportunities.
- Improve requirement communication across stakeholders.
- Reduce dependency on Gemini API for core analysis and summarization.

## Recommended Models (Permissive Licenses)

Primary model to fine-tune:

- `microsoft/Phi-3.5-mini-instruct` (model card: <https://huggingface.co/microsoft/Phi-3.5-mini-instruct>)
- License shown on model card: `MIT` (permissive)

Alternative larger model:

- `mistralai/Mistral-7B-Instruct-v0.2` (model card: <https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2>)
- License shown on model card: `Apache-2.0` (permissive)

Embedding model for NLP retrieval/reranking:

- `sentence-transformers/all-MiniLM-L6-v2` (model card: <https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2>)
- License shown on model card: `Apache-2.0`

Use permissive-license checkpoints for publication-safe reproducibility and industry transferability.

## NLP Task Design

Use a multi-task instruction dataset with these task families:

1. Requirement parsing:
   - Input: requirement text
   - Output: actor/action/object/conditions JSON
2. Gap and ambiguity detection:
   - Input: requirement text
   - Output: missing fields + domain gaps + status
3. Clarification question generation:
   - Input: requirement text and detected gaps
   - Output: high-value clarification questions
4. Capability insights:
   - Input: requirement text
   - Output: service improvements, business opportunities, stakeholder communication plan
5. Summarization:
   - Input: meeting notes + context
   - Output: concise summary with risks and decisions

## Training Pipeline

1. Create dataset as JSONL:

```json
{"instruction":"Extract requirement structure","input":"User logs in with OTP","output":"{\"actor\":\"user\",\"action\":\"logs in\",\"obj\":\"system\",\"conditions\":\"with OTP\"}"}
```

2. Install training dependencies:

```bash
cd backend
pip install -r requirements-train.txt
```

3. Run LoRA fine-tuning:

```bash
python scripts/train_requirement_nlp_lora.py --dataset data/requirements_train.jsonl --model-name microsoft/Phi-3.5-mini-instruct --output-dir outputs/phi35-requimind-lora
```

4. Evaluate on held-out split:
   - Parsing: exact/partial slot match
   - Gap detection: macro F1
   - Question generation: BLEU/ROUGE + human rating
   - Summary quality: human evaluation rubric

5. Deploy local model:
   - Serve fine-tuned model locally (Transformers or vLLM/TGI)
   - Route `LLM_MODE=local` and keep Gemini only as optional fallback

## Paper-Ready Experiment Setup

- Baselines:
  - Rule-based only (current deterministic pipeline)
  - Gemini-backed summary
  - Fine-tuned local model (Phi-3.5 + LoRA)
- Ablations:
  - with/without context history
  - with/without capability insight prompts
  - different LoRA ranks (`r=8`, `r=16`, `r=32`)
- Report:
  - Accuracy/F1 + inference latency + cost per 1,000 requests
  - Error analysis by domain (security, healthcare, payment, booking)

## Licensing Note

Always confirm the latest license terms on the model cards before final publication or commercialization.
