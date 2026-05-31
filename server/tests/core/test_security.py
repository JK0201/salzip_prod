import hmac
import importlib
import inspect
from unittest.mock import patch

import pytest

from app.core.security import (
    generate_session_token,
    hash_session_token,
    verify_token_hash,
)


# generate_session_token


def test_generate_session_token_returns_str():
    result = generate_session_token()
    assert isinstance(result, str)


def test_generate_session_token_unique_each_call():
    token1 = generate_session_token()
    token2 = generate_session_token()
    assert token1 != token2


# hash_session_token


def test_hash_session_token_returns_64_char_hex():
    result = hash_session_token("any-token")
    assert len(result) == 64
    assert all(c in "0123456789abcdef" for c in result)


def test_hash_session_token_deterministic():
    token = "test-token-abc"
    assert hash_session_token(token) == hash_session_token(token)


def test_hash_session_token_different_tokens_different_hashes():
    assert hash_session_token("token-a") != hash_session_token("token-b")


# verify_token_hash


def test_verify_token_hash_returns_true_for_matching_pair():
    token = generate_session_token()
    expected_hash = hash_session_token(token)
    assert verify_token_hash(token, expected_hash) is True


def test_verify_token_hash_returns_false_for_wrong_token():
    token = generate_session_token()
    expected_hash = hash_session_token(token)
    assert verify_token_hash("wrong-token", expected_hash) is False


def test_verify_token_hash_returns_false_for_wrong_hash():
    token = generate_session_token()
    assert verify_token_hash(token, "a" * 64) is False


def test_verify_token_hash_uses_hmac_compare_digest():
    import app.core.security as security_module

    source = inspect.getsource(security_module)
    assert "compare_digest" in source
