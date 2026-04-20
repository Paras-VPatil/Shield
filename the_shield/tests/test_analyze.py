def test_analyze_marks_incomplete_when_actor_missing(client) -> None:
    response = client.post("/analyze", json={"text": "Must store audit logs for all actions."})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "incomplete"
    assert "actor" in body["missing_fields"]


def test_analyze_detects_login_domain_gaps(client) -> None:
    response = client.post("/analyze", json={"text": "User logs into the system."})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "gap_detected"
    assert len(body["questions"]) >= 2
    assert any(gap.startswith("login:") for gap in body["domain_gaps"])


def test_analyze_accepts_complete_non_domain_requirement(client) -> None:
    response = client.post(
        "/analyze",
        json={"text": "Admin updates user role when manager approves the request."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "complete"


def test_analyze_supports_multiline_requirements(client) -> None:
    response = client.post(
        "/analyze",
        json={
            "text": (
                "User registers with email and password.\n"
                "User logs into the system.\n"
                "System locks account after 5 failed login attempts."
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["extracted_requirements"]) == 3
    assert len(body["item_analyses"]) == 3
    assert body["status"] in {"incomplete", "gap_detected", "complete"}


def test_analyze_generates_contextual_healthcare_questions(client) -> None:
    response = client.post(
        "/analyze",
        json={
            "text": (
                "Build a healthcare platform where patients can access medical records, "
                "doctors and admins can log in, and AI analytics provide insights."
            )
        },
    )

    assert response.status_code == 200
    questions = response.json()["questions"]
    question_texts = [q["text"] if isinstance(q, dict) else q for q in questions]
    
    expected_subset = [
        "What specific patient information will be displayed?",
        "Which OAuth providers will be supported?",
        "What permissions are assigned to user, doctor, and admin roles?",
        "Can doctors modify medical records?",
        "What healthcare data privacy standards must be followed?",
        "What AI analytics capabilities are required?",
    ]
    for expected in expected_subset:
        assert expected in question_texts
