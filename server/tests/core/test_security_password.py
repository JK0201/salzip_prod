from pathlib import Path

import pytest

from app.core.security import hash_password, verify_password


def test_pyproject_has_argon2_cffi():
    content = Path("pyproject.toml").read_text()
    assert "argon2-cffi" in content


def test_hash_password_returns_str_with_argon2_prefix():
    result = hash_password("test_pw_123")
    assert isinstance(result, str)
    assert result.startswith("$argon2")


def test_hash_password_salt_randomness():
    h1 = hash_password("same_password")
    h2 = hash_password("same_password")
    assert h1 != h2


def test_verify_password_correct():
    raw = "correct_horse_battery_staple"
    hashed = hash_password(raw)
    assert verify_password(raw, hashed) is True


def test_verify_password_wrong_password_returns_false():
    hashed = hash_password("right")
    assert verify_password("wrong", hashed) is False


def test_verify_password_invalid_hash_returns_false_no_exception():
    result = verify_password("any", "not-a-valid-hash")
    assert result is False
