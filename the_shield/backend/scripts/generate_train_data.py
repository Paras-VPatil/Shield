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
        "questions": [
            {"text": "Which authentication methods should be supported?", "priority": 1},
            {"text": "Is multi-factor authentication required?", "priority": 1}
        ],
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
        "questions": [
            {"text": "Which credit card networks (Visa, MC, etc.) are supported?", "priority": 2},
            {"text": "How should transaction failures be handled?", "priority": 1}
        ],
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
        "questions": [
            {"text": "Are there specific access levels for different doctors?", "priority": 2},
            {"text": "How is patient data privacy guaranteed (HIPAA/GDPR)?", "priority": 1}
        ],
        "insights": {
            "complexity_score": 75,
            "decision_readiness_score": 50,
            "top_concepts": ["doctor", "patient", "record", "privacy"],
            "investigation_actions": ["Validate RBAC implementation against HIPAA.", "Define audit logging requirements."],
            "service_improvements": ["Incorporate end-to-end encryption and strict clinical workflow validations."],
            "business_opportunities": ["Market the system as a HIPAA-compliant SaaS for private practices."]
        },
        "summary": "Requirement for viewing patient records. High complexity due to regulatory (HIPAA) and privacy constraints. Access controls need explicit definition."
    },
    {
        "domain": "cloud_infra",
        "requirement": "The system must auto-scale based on CPU utilization and request latency to maintain 99.99% availability.",
        "parsing": {"actor": "system", "action": "auto-scale", "obj": "resources", "conditions": "based on CPU and latency for 99.99% availability"},
        "gaps": ["minimum/maximum instance limits", "cooldown period", "cross-region scaling strategy"],
        "questions": [
            {"text": "What are the hard minimum and maximum instance count limits?", "priority": 2},
            {"text": "Does the scaling policy need to support cross-region failover?", "priority": 1}
        ],
        "insights": {
            "complexity_score": 85,
            "decision_readiness_score": 40,
            "top_concepts": ["auto-scaling", "availability", "cloud infra"],
            "investigation_actions": ["Define cooldown metrics.", "Validate regional availability zones."],
            "service_improvements": ["Transition to serverless architecture to simplify scaling."],
            "business_opportunities": ["Leverage spot instances to optimize scaling costs."]
        },
        "summary": "High-availability scaling requirement. Requires precise definition of infrastructure limits and regional strategy."
    },
    {
        "domain": "ai_ml",
        "requirement": "All AI model predictions must include an explainability score and be logged for periodic drift analysis.",
        "parsing": {"actor": "system", "action": "include/log", "obj": "explainability scores and predictions", "conditions": "for drift analysis"},
        "gaps": ["explainability method (SHAP, LIME)", "logging destination", "drift detection threshold"],
        "questions": [
            {"text": "Which explainability algorithm (e.g., SHAP, Integrated Gradients) should be used?", "priority": 2},
            {"text": "What is the acceptable threshold for model drift before re-training is triggered?", "priority": 1}
        ],
        "insights": {
            "complexity_score": 90,
            "decision_readiness_score": 35,
            "top_concepts": ["explainable AI", "model drift", "observability"],
            "investigation_actions": ["Select explainability framework.", "Design drift monitoring dashboard."],
            "service_improvements": ["Implement a unified MLOps pipeline for automated auditing."],
            "business_opportunities": ["Offer 'AI Trust' reports as an upsell for enterprise audits."]
        },
        "summary": "ML management requirement focused on trust and stability. Requires technical selection of explainability methods."
    },
    {
        "domain": "fintech",
        "requirement": "The ledger must strictly adhere to Double-Entry accounting principles and support immutable audit logs.",
        "parsing": {"actor": "ledger system", "action": "adhere/support", "obj": "double-entry and immutable logs", "conditions": "strictly"},
        "gaps": ["concurrency control (locking)", "audit log storage (blockchain, WORM)", "reconciliation frequency"],
        "questions": [
            {"text": "What mechanism will ensure audit logs remain immutable (e.g., HMAC chains, WORM storage)?", "priority": 1},
            {"text": "How should the system resolve momentary ledger imbalances during high-concurrency periods?", "priority": 2}
        ],
        "insights": {
            "complexity_score": 95,
            "decision_readiness_score": 30,
            "top_concepts": ["fintech", "compliance", "ledger", "immutability"],
            "investigation_actions": ["Design immutable data structure.", "Audit concurrency locking mechanism."],
            "service_improvements": ["Enable real-time reconciliation to detect fraud instantly."],
            "business_opportunities": ["Certify the platform for SOC2 Type II compliance."]
        },
        "summary": "Mission-critical financial ledger. Requires extreme focus on data integrity and immutability."
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
        
        # Task 3: Questions with Priority
        dataset.append({
            "instruction": "Generate clarification questions with priority levels (1=Critical, 2=High, 3=Standard).",
            "input": f"Requirement: {ex['requirement']}\nGaps: {', '.join(ex['gaps'])}",
            "output": json.dumps(ex["questions"])
        })
        
        # Task 4: Insights
        dataset.append({
            "instruction": "Generate capability insights, business opportunities, and stakeholder communication plans.",
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
    # Detect output path based on current directory
    output_path = Path("backend/data/requirements_train.jsonl")
    if not output_path.parent.exists():
        # Fallback for nested structure seen in environment list_dir
        output_path = Path("backend/backend/data/requirements_train.jsonl")
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = generate_task_data()
    
    with open(output_path, "w") as f:
        for entry in data:
            f.write(json.dumps(entry) + "\n")
            
    print(f"Generated {len(data)} examples to {output_path}")

if __name__ == "__main__":
    main()
