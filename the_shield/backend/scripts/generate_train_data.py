import json
import random
from pathlib import Path

DOMAINS = ["login", "payment", "booking", "healthcare", "analytics", "integration"]

EXAMPLES = [
    {
        "domain": "login",
        "requirement": "The user should be able to log in to the application.",
        "parsing": {"actor": "user", "action": "log in", "obj": "application", "conditions": ""},
        "gaps": ["authentication method (password, SSO, OAuth)", "MFA requirements", "session timeout"],
        "questions": ["Which authentication methods should be supported?", "Is multi-factor authentication required?"],
        "insights": {
            "complexity_score": 45,
            "decision_readiness_score": 60,
            "top_concepts": ["login", "authentication", "user"],
            "investigation_actions": ["Define supported auth providers.", "Specify MFA policies."],
            "service_improvements": ["Standardize security protocols across all entry points."],
            "business_opportunities": ["Offer SSO integration as a premium feature for enterprise clients."]
        },
        "summary": "The requirement describes a basic login flow. It lacks detail on authentication methods and MFA, which are critical for security."
    },
    {
        "domain": "payment",
        "requirement": "Customers can pay for their orders using a credit card.",
        "parsing": {"actor": "customers", "action": "pay for", "obj": "orders", "conditions": "using a credit card"},
        "gaps": ["supported card types", "currency handling", "PCI compliance", "refund/retry logic"],
        "questions": ["Which credit card networks (Visa, MC, etc.) are supported?", "How should transaction failures be handled?"],
        "insights": {
            "complexity_score": 65,
            "decision_readiness_score": 55,
            "top_concepts": ["payment", "credit card", "order", "transaction"],
            "investigation_actions": ["Clarify currency support.", "Define retry and refund workflows."],
            "service_improvements": ["Implement robust reconciliation and fraud detection logic."],
            "business_opportunities": ["Partner with multiple payment gateways to reduce processing fees."]
        },
        "summary": "Requirement for credit card payment. Needs clarification on supported networks and error handling for PCI-compliant processing."
    },
    {
        "domain": "healthcare",
        "requirement": "A doctor can view patient records in the system.",
        "parsing": {"actor": "doctor", "action": "view", "obj": "patient records", "conditions": "in the system"},
        "gaps": ["access control (RBAC)", "HIPAA compliance", "audit logging", "emergency access policy"],
        "questions": ["Are there specific access levels for different doctors?", "How is patient data privacy guaranteed (HIPAA/GDPR)?"],
        "insights": {
            "complexity_score": 75,
            "decision_readiness_score": 50,
            "top_concepts": ["doctor", "patient", "record", "privacy"],
            "investigation_actions": ["Validate RBAC implementation against HIPAA.", "Define audit logging requirements."],
            "service_improvements": ["Incorporate end-to-end encryption and strict clinical workflow validations."],
            "business_opportunities": ["Market the system as a HIPAA-compliant SaaS for private practices."]
        },
        "summary": "Requirement for viewing patient records. High complexity due to regulatory (HIPAA) and privacy constraints. Access controls need explicit definition."
    }
]

def generate_task_data():
    dataset = []
    
    for ex in EXAMPLES:
        # Task 1: Parsing
        dataset.append({
            "instruction": "Extract requirement structure (actor, action, object, conditions).",
            "input": ex["requirement"],
            "output": json.dumps(ex["parsing"])
        })
        
        # Task 2: Gaps
        dataset.append({
            "instruction": "Identify missing fields and domain gaps in this requirement.",
            "input": ex["requirement"],
            "output": json.dumps({"gaps": ex["gaps"], "status": "gap_detected"})
        })
        
        # Task 3: Questions
        dataset.append({
            "instruction": "Generate clarification questions for the following requirement and detected gaps.",
            "input": f"Requirement: {ex['requirement']}\nGaps: {', '.join(ex['gaps'])}",
            "output": json.dumps(ex["questions"])
        })
        
        # Task 4: Insights
        dataset.append({
            "instruction": "Generate capability insights, business opportunities, and stakeholder communication plans for this requirement.",
            "input": ex["requirement"],
            "output": json.dumps(ex["insights"])
        })
        
        # Task 5: Summary
        dataset.append({
            "instruction": "Provide a concise requirement summary including risks and interpretation.",
            "input": ex["requirement"],
            "output": ex["summary"]
        })

    return dataset

def main():
    output_path = Path("backend/data/requirements_train.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = generate_task_data()
    
    with open(output_path, "w") as f:
        for entry in data:
            f.write(json.dumps(entry) + "\n")
            
    print(f"Generated {len(data)} examples to {output_path}")

if __name__ == "__main__":
    main()
