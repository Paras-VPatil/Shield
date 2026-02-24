def _auth_headers(client, username="demo_user", password="demo_pass_123"):
    register = client.post("/auth/register", json={"username": username, "password": password})
    if register.status_code == 200:
        token = register.json()["access_token"]
    else:
        login = client.post("/auth/login", json={"username": username, "password": password})
        assert login.status_code == 200
        token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_meeting_create_and_list(client):
    headers = _auth_headers(client, username="meeting_user", password="meeting_pass_123")
    create = client.post("/meetings", json={"title": "Sprint Planning"}, headers=headers)
    assert create.status_code == 200
    listing = client.get("/meetings", headers=headers)
    assert listing.status_code == 200
    assert any(item["title"] == "Sprint Planning" for item in listing.json())


def test_meeting_analyze_tracks_open_and_resolved_questions(client):
    headers = _auth_headers(client, username="analyst_user", password="analyst_pass_123")
    created = client.post("/meetings", json={"title": "Healthcare Discovery"}, headers=headers)
    meeting_id = created.json()["id"]

    first = client.post(
        f"/meetings/{meeting_id}/analyze",
        json={
            "text": "Healthcare portal with patient records, doctor login, and AI analytics.",
            "speaker_segments": [],
        },
        headers=headers,
    )
    assert first.status_code == 200
    first_body = first.json()
    assert len(first_body["open_questions"]) >= 1

    second = client.post(
        f"/meetings/{meeting_id}/analyze",
        json={
            "text": (
                "Decision: We will support Google and Microsoft OAuth. "
                "Doctors will have read-only access to medical records. "
                "The system must follow HIPAA and FHIR."
            ),
            "speaker_segments": [],
        },
        headers=headers,
    )
    assert second.status_code == 200
    second_body = second.json()
    assert isinstance(second_body["resolved_questions"], list)
    assert len(second_body["resolved_questions"]) >= 1


def test_meeting_transcript_download(client):
    headers = _auth_headers(client, username="download_user", password="download_pass_123")
    created = client.post("/meetings", json={"title": "Transcript Meeting"}, headers=headers)
    meeting_id = created.json()["id"]

    analyzed = client.post(
        f"/meetings/{meeting_id}/analyze",
        json={"text": "User logs into the healthcare portal.", "speaker_segments": []},
        headers=headers,
    )
    assert analyzed.status_code == 200

    download = client.get(f"/meetings/{meeting_id}/transcript", headers=headers)
    assert download.status_code == 200
    assert "Meeting: Transcript Meeting" in download.text
