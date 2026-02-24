from app.utils.helpers import unique_in_order

MISSING_FIELD_QUESTIONS = {
    "actor": "Who is the primary actor performing this requirement?",
    "action": "What exact action should be performed?",
    "object": "What system component or entity is affected by this action?",
}

DOMAIN_GAP_QUESTIONS = {
    "login: authentication method": (
        "Which authentication methods should be supported (password, OAuth, SSO, MFA)?"
    ),
    "login: session management": (
        "How should session timeout, refresh, and logout invalidation be handled?"
    ),
    "login: failure handling": (
        "What should happen after repeated failed login attempts (lockout, cooldown, alerts)?"
    ),
    "login: recovery flow": (
        "What account recovery flow is required (email OTP, SMS OTP, reset link)?"
    ),
    "payment: payment method support": (
        "Which payment methods and providers should be supported?"
    ),
    "payment: failure handling": (
        "How should failed or partial payment transactions be handled?"
    ),
    "payment: security controls": (
        "What payment security controls are mandatory (PCI, tokenization, encryption)?"
    ),
    "payment: confirmation flow": (
        "What confirmation artifacts should users receive after payment?"
    ),
    "booking: availability checks": (
        "How should availability be validated before confirming a booking?"
    ),
    "booking: change or cancel flow": (
        "What are the reschedule and cancellation rules?"
    ),
    "booking: notification flow": (
        "Which booking notifications should be sent and via which channels?"
    ),
    "booking: payment linkage": (
        "Is payment required before booking confirmation?"
    ),
}

DOMAIN_DECISION_QUESTIONS = {
    "healthcare": [
        "Which clinical workflows are in scope for this release?",
        "What healthcare interoperability standards should be supported (FHIR/HL7)?",
        "What audit trail depth is required for patient data changes?",
    ],
    "finance": [
        "What transaction risk controls and approval thresholds are required?",
        "Which reconciliation process will be used for failed or delayed payments?",
        "Which compliance framework applies to this product (PCI, AML, KYC)?",
    ],
    "ecommerce": [
        "What order fulfillment and cancellation policy should the system enforce?",
        "What inventory consistency strategy is required across channels?",
        "What checkout abandonment recovery strategy is expected?",
    ],
    "education": [
        "What learner roles and assessment permissions must be differentiated?",
        "How should grading, re-evaluation, and audit policies be governed?",
        "What student progress analytics are required for decision-making?",
    ],
    "logistics": [
        "What SLA targets are required for dispatch, transit, and delivery stages?",
        "How should route exceptions and delay escalations be handled?",
        "What tracking granularity is needed for operational decisions?",
    ],
    "security": [
        "What threat model and security baseline should this system follow?",
        "What incident response and breach notification workflow is required?",
        "What identity lifecycle controls are required for user onboarding/offboarding?",
    ],
    "hr": [
        "What approval workflow is required for leave, payroll, and profile changes?",
        "Which employee data fields are mandatory versus optional?",
        "What compliance and retention rules apply to HR records?",
    ],
    "government": [
        "What public-service eligibility and verification rules must be enforced?",
        "What legal retention and audit requirements govern this workflow?",
        "What multilingual/accessibility standards are mandatory?",
    ],
    "legal": [
        "Which contract lifecycle stages are in scope for automation?",
        "What legal approval checkpoints are required before finalization?",
        "What evidence and versioning policy is required for traceability?",
    ],
    "iot": [
        "What device onboarding and trust model should be enforced?",
        "What telemetry retention policy is required for analytics and forensics?",
        "How should offline synchronization conflicts be resolved?",
    ],
}

STOP_WORDS = {
    "what",
    "which",
    "how",
    "should",
    "would",
    "could",
    "is",
    "are",
    "the",
    "for",
    "and",
    "this",
    "that",
    "with",
    "from",
    "into",
    "your",
    "their",
    "must",
    "can",
    "will",
}


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _contains_all(text: str, keywords: list[str]) -> bool:
    return all(keyword in text for keyword in keywords)


def _count_matches(text: str, keywords: list[str]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def _generate_contextual_questions(requirement_text: str) -> list[str]:
    lower = requirement_text.lower()
    questions: list[str] = []

    healthcare_keywords = ["healthcare", "patient", "medical", "ehr", "emr", "clinic", "hospital"]
    patient_data_keywords = [
        "patient information",
        "patient profile",
        "name",
        "dob",
        "allerg",
        "history",
        "medication",
        "vitals",
    ]
    auth_keywords = ["login", "log in", "sign in", "oauth", "authentication", "sso"]
    oauth_provider_keywords = ["google", "microsoft", "github", "apple", "facebook", "linkedin"]
    role_keywords = ["user", "doctor", "admin", "patient", "nurse", "staff"]
    role_permission_keywords = ["permission", "role-based", "rbac", "authorization", "access control"]
    record_keywords = ["medical record", "records", "ehr", "emr", "chart"]
    record_control_keywords = ["modify", "edit", "update", "write", "read-only", "readonly"]
    privacy_standard_keywords = ["hipaa", "gdpr", "fhir", "hl7", "privacy act", "security standard"]
    ai_keywords = ["ai", "analytics", "machine learning", "prediction", "insight", "recommendation"]
    ai_detail_keywords = ["risk score", "dashboard", "forecast", "anomaly", "report", "trend"]

    if _contains_any(lower, healthcare_keywords) and not _contains_any(lower, patient_data_keywords):
        questions.append("What specific patient information will be displayed?")

    if _contains_any(lower, auth_keywords) and not _contains_any(lower, oauth_provider_keywords):
        questions.append("Which OAuth providers will be supported?")

    if _count_matches(lower, role_keywords) >= 2 and not _contains_any(lower, role_permission_keywords):
        questions.append("What permissions are assigned to user, doctor, and admin roles?")

    if _contains_any(lower, ["doctor"]) and _contains_any(lower, record_keywords) and not _contains_any(
        lower, record_control_keywords
    ):
        questions.append("Can doctors modify medical records?")

    if _contains_any(lower, healthcare_keywords) and not _contains_any(lower, privacy_standard_keywords):
        questions.append("What healthcare data privacy standards must be followed?")

    if _contains_any(lower, ai_keywords) and not _contains_any(lower, ai_detail_keywords):
        questions.append("What AI analytics capabilities are required?")

    if _contains_all(lower, ["otp"]) and not _contains_any(lower, ["email otp", "sms otp", "authenticator"]):
        questions.append("Should OTP be delivered via email, SMS, authenticator app, or multiple channels?")

    return questions


def _generate_domain_questions(domains: list[str]) -> list[str]:
    questions: list[str] = []
    for domain in domains:
        questions.extend(DOMAIN_DECISION_QUESTIONS.get(domain, []))
    return questions


def _is_reasonable_question(question: str) -> bool:
    cleaned = question.strip()
    if len(cleaned) < 12:
        return False
    if not cleaned.endswith("?"):
        return False
    tokens = [token.strip(" ,.:;!?").lower() for token in cleaned.split()]
    keywords = [token for token in tokens if token and token not in STOP_WORDS]
    return len(keywords) >= 3


def generate_questions(
    missing_fields: list[str],
    domain_gaps: list[str],
    requirement_text: str = "",
    domains: list[str] | None = None,
    max_questions: int = 15,
) -> list[str]:
    questions: list[str] = []

    for field in missing_fields:
        question = MISSING_FIELD_QUESTIONS.get(field)
        if question:
            questions.append(question)

    for gap in domain_gaps:
        template_question = DOMAIN_GAP_QUESTIONS.get(gap)
        if template_question:
            questions.append(template_question)
            continue

        if ":" in gap:
            domain, feature = gap.split(":", maxsplit=1)
            questions.append(
                f"For {domain.strip()}, how should the system handle {feature.strip()}?"
            )
        else:
            questions.append(f"Can you clarify the missing detail: {gap}?")

    if requirement_text.strip():
        questions.extend(_generate_contextual_questions(requirement_text))

    if domains:
        questions.extend(_generate_domain_questions(domains))

    if (missing_fields or domain_gaps) and len(questions) < 2:
        questions.append("What are the acceptance criteria for this requirement?")
        questions.append("Are there edge cases or failure scenarios to include?")

    reasonable = [question for question in questions if _is_reasonable_question(question)]
    deduped = unique_in_order(reasonable)
    return deduped[:max_questions]
