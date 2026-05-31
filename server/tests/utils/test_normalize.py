from app.utils.normalize import normalize_email


def test_normalize_email_strips_and_lowercases():
    assert normalize_email("  A@B.com ") == "a@b.com"


def test_normalize_email_already_normalized_unchanged():
    assert normalize_email("user@x.com") == "user@x.com"


def test_normalize_email_uppercased():
    assert normalize_email("USER@X.COM") == "user@x.com"


def test_normalize_email_empty_string_passthrough():
    assert normalize_email("") == ""


def test_normalize_email_returns_str():
    result = normalize_email("Test@Example.com")
    assert isinstance(result, str)
