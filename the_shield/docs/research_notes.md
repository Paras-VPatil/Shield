# Requirements Analysis Notes

## Objective Alignment

- Core objective is early-stage requirement risk reduction.
- MVP must prioritize deterministic, fast baseline logic before advanced NLP.
- LLM usage should enrich output, not block core functionality.

## Key Requirement Mappings

- Requirement parsing maps to extraction of actor/action/object/conditions.
- Completeness detection maps to missing-field checks over parsed output.
- Domain gap detection maps to domain-specific heuristics for login/payment/booking.
- Clarification question generation maps to missing fields plus domain gaps.
- LLM summary maps to optional Gemini call with mandatory local fallback.

## Constraints That Shape Design

- API response target under 3 seconds suggests simple local heuristics + short LLM prompt.
- Reliability requirement implies robust fallback when API key or provider is unavailable.
- Security requirement implies `.env` key loading and strict `.gitignore`.
- Stateless deployment requirement suggests no hard dependency on database in MVP.

## Decisions for MVP

- Use FastAPI with modular services under `app/services`.
- Keep parsing heuristic-based for predictable behavior and easy testing.
- Implement domain rule packs for `login`, `payment`, and `booking`.
- Provide structured JSON response with parse data, gaps, questions, and summary.
- Build plain HTML/CSS/JS frontend for quick interaction and demo readiness.

## Open Technical Risks

- Heuristic parsing may miss complex grammar.
- Domain gap coverage limited to configured rule sets.
- Gemini model availability may vary by account/region.

## Mitigation

- Keep parser and domain rules isolated for iterative improvement.
- Ensure fallback summary always returns usable output.
- Add focused tests for required MVP scenarios.
