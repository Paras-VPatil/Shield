from typing import Dict, List

from app.utils.helpers import build_status_message

DOMAIN_RULES: Dict[str, dict] = {
    "login": {
        "keywords": ["login", "log in", "logs in", "logs into", "sign in", "authenticate", "auth"],
        "expected": {
            "authentication method": ["password", "oauth", "sso", "mfa", "otp"],
            "session management": ["session", "timeout", "token", "jwt"],
            "failure handling": ["lockout", "failed", "retry", "rate limit"],
            "recovery flow": ["forgot password", "reset password", "recovery"],
        },
    },
    "payment": {
        "keywords": ["payment", "pay", "checkout", "transaction", "invoice"],
        "expected": {
            "payment method support": ["card", "bank", "wallet", "paypal", "upi"],
            "failure handling": ["failed", "declined", "retry", "rollback", "refund"],
            "security controls": ["pci", "cvv", "fraud", "tokenization", "encryption"],
            "confirmation flow": ["receipt", "confirmation", "reference", "invoice"],
        },
    },
    "booking": {
        "keywords": ["booking", "book", "reservation", "reserve", "appointment"],
        "expected": {
            "availability checks": ["availability", "slot", "inventory"],
            "change or cancel flow": ["cancel", "reschedule", "cancellation"],
            "notification flow": ["email", "sms", "notification", "reminder"],
            "payment linkage": ["payment", "deposit", "prepay"],
        },
    },
}


def analyze_requirement_completeness(text: str, parsed: dict) -> dict:
    lower = text.lower()
    missing_fields: List[str] = []
    if not parsed.get("actor"):
        missing_fields.append("actor")
    if not parsed.get("action"):
        missing_fields.append("action")
    if not parsed.get("obj"):
        missing_fields.append("object")

    domain_gaps: List[str] = []
    active_domains: List[str] = []
    for domain, rules in DOMAIN_RULES.items():
        if any(keyword in lower for keyword in rules["keywords"]):
            active_domains.append(domain)

    for domain in active_domains:
        expected = DOMAIN_RULES[domain]["expected"]
        for feature, keywords in expected.items():
            if not any(keyword in lower for keyword in keywords):
                domain_gaps.append(f"{domain}: {feature}")

    status = "complete"
    if domain_gaps:
        status = "gap_detected"
    elif missing_fields:
        status = "incomplete"

    message = build_status_message(status, missing_fields, domain_gaps)
    return {
        "status": status,
        "message": message,
        "missing_fields": missing_fields,
        "domain_gaps": domain_gaps,
    }
