from app.services.requirement_extractor import extract_requirements


def test_extract_requirements_from_bullets() -> None:
    text = """
    - User logs into the system.
    - User resets password using OTP.
    - Admin deactivates a user account.
    """
    items = extract_requirements(text)

    assert len(items) == 3
    assert items[0].startswith("User logs")


def test_extract_requirements_from_paragraph() -> None:
    text = "User logs in. System locks account after failed attempts. Admin reviews alerts."
    items = extract_requirements(text)

    assert len(items) == 3
