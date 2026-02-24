from app.services.requirement_parser import parse_requirement


def test_parser_extracts_core_fields() -> None:
    parsed = parse_requirement("User logs into the system when credentials are valid.")

    assert parsed["actor"] == "user"
    assert parsed["action"] is not None
    assert parsed["obj"] is not None
    assert parsed["conditions"] is not None


def test_parser_detects_missing_actor() -> None:
    parsed = parse_requirement("Logs into the system using email and password.")

    assert parsed["actor"] is None
    assert parsed["action"] is not None
