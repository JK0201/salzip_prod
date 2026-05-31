import hashlib
import hmac
import secrets

import argon2
import argon2.exceptions

_HASHER = argon2.PasswordHasher()


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_token_hash(token: str, expected_hash: str) -> bool:
    return hmac.compare_digest(hash_session_token(token), expected_hash)


def hash_password(raw: str) -> str:
    return _HASHER.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return _HASHER.verify(hashed, raw)
    except (argon2.exceptions.VerifyMismatchError, argon2.exceptions.InvalidHashError):
        return False
