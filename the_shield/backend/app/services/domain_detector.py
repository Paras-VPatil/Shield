from app.utils.helpers import unique_in_order

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "healthcare": ["patient", "medical", "hospital", "clinic", "ehr", "emr", "hipaa"],
    "finance": ["payment", "invoice", "loan", "bank", "kyc", "transaction", "wallet"],
    "ecommerce": ["cart", "catalog", "order", "checkout", "product", "inventory"],
    "education": ["student", "teacher", "course", "exam", "grading", "lms"],
    "logistics": ["shipment", "warehouse", "delivery", "fleet", "routing"],
    "security": ["authentication", "authorization", "mfa", "audit", "compliance", "encryption"],
    "hr": ["employee", "recruitment", "payroll", "leave", "attendance"],
    "government": ["citizen", "permit", "compliance", "public service", "regulatory"],
    "legal": ["contract", "clause", "case", "litigation", "legal hold"],
    "iot": ["sensor", "device", "telemetry", "edge", "firmware"],
}


def detect_domains(text: str) -> list[str]:
    lower = text.lower()
    matches: list[str] = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(keyword in lower for keyword in keywords):
            matches.append(domain)
    return unique_in_order(matches)
