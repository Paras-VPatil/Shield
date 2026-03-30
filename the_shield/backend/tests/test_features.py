import pytest
from app.services.llm_service import LLMService
from app.services.meeting_service import analyze_meeting_content, get_meeting_revisions, create_meeting
from app.database.db import load_db, save_db
import os

@pytest.fixture
def mock_db(tmp_path):
    db_path = tmp_path / "shield_db.json"
    os.environ["SHIELD_DB_PATH"] = str(db_path)
    save_db({"users": [], "meetings": []})
    yield db_path
    if "SHIELD_DB_PATH" in os.environ:
        del os.environ["SHIELD_DB_PATH"]

def test_sprint_planning_in_analysis(mock_db):
    llm = LLMService()
    # Mocking the local LLM output might be hard, but let's see if we can test the structure
    # Given we are using a local model, we'll assume the service handles the parsing
    user_id = "test_user"
    meeting = create_meeting(user_id, "Sprint Test")
    
    text = "We need to build a new CRM system. Phase 1: Auth and Database. Phase 2: UI and API. Phase 3: Deployment."
    
    analysis = analyze_meeting_content(
        user_id=user_id,
        meeting_id=meeting["id"],
        text=text,
        speaker_segments=[],
        llm_service=llm
    )
    
    assert "capability_insights" in analysis
    assert "sprint_plan" in analysis["capability_insights"]
    assert "proprietary_tool_suggestions" in analysis["capability_insights"]
    
    # Test revisions
    # Add another analysis to the same meeting
    text2 = "Actually, let's add a mobile app requirement."
    analyze_meeting_content(
        user_id=user_id,
        meeting_id=meeting["id"],
        text=text2,
        speaker_segments=[],
        llm_service=llm
    )
    
    revisions = get_meeting_revisions(user_id, meeting["id"])
    assert revisions["meeting_id"] == meeting["id"]
    assert revisions["previous_id"] is not None
    assert "current_id" in revisions
