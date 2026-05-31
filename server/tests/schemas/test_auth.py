import datetime
import uuid

import pytest
from pydantic import BaseModel, ValidationError

from app.schemas.auth import AuthResponse, LoginRequest, SignupRequest, UserResponse


# ── 클래스 존재 및 BaseModel 상속 (acceptance #2~#5) ─────────────────────────

def test_signup_request_is_pydantic_model():
    assert issubclass(SignupRequest, BaseModel)


def test_login_request_is_pydantic_model():
    assert issubclass(LoginRequest, BaseModel)


def test_user_response_is_pydantic_model():
    assert issubclass(UserResponse, BaseModel)


def test_auth_response_is_pydantic_model():
    assert issubclass(AuthResponse, BaseModel)


# ── SignupRequest 정상 검증 통과 (acceptance #6) ─────────────────────────────

def test_signup_request_valid():
    obj = SignupRequest(email="foo@bar.com", password="12345678", name="Tester")
    assert obj.email == "foo@bar.com"
    assert obj.password == "12345678"


# ── SignupRequest password 7자 → ValidationError (acceptance #7) ─────────────

def test_signup_request_password_too_short_raises():
    with pytest.raises(ValidationError):
        SignupRequest(email="foo@bar.com", password="1234567", name="Tester")


# ── SignupRequest 잘못된 email → ValidationError (acceptance #8) ─────────────

def test_signup_request_invalid_email_raises():
    with pytest.raises(ValidationError):
        SignupRequest(email="not-an-email", password="12345678", name="Tester")


# ── LoginRequest password 1자 허용 (acceptance #9) ───────────────────────────

def test_login_request_single_char_password_passes():
    obj = LoginRequest(email="foo@bar.com", password="x")
    assert obj.password == "x"


# ── LoginRequest 잘못된 email → ValidationError (acceptance #10) ─────────────

def test_login_request_invalid_email_raises():
    with pytest.raises(ValidationError):
        LoginRequest(email="not-an-email", password="anypassword")


# ── UserResponse 필드 타입 (acceptance #4) ───────────────────────────────────

def test_user_response_fields():
    uid = uuid.uuid4()
    obj = UserResponse(id=uid, email="test@example.com", name="Tester")
    assert obj.id == uid
    assert isinstance(obj.id, uuid.UUID)
    assert obj.email == "test@example.com"


# ── AuthResponse 필드 타입 (acceptance #5) ───────────────────────────────────

def test_auth_response_fields():
    uid = uuid.uuid4()
    user = UserResponse(id=uid, email="test@example.com", name="Tester")
    expires = datetime.datetime(2026, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    obj = AuthResponse(user=user, token="test-token", expires_at=expires)
    assert isinstance(obj.user, UserResponse)
    assert isinstance(obj.expires_at, datetime.datetime)
    assert obj.expires_at == expires


# ── T-028: SignupRequest name 필드 (acceptance #1~#4) ────────────────────────

def test_signup_request_has_name_field():
    fields = SignupRequest.model_fields
    assert "name" in fields
    assert fields["name"].annotation is str


def test_signup_request_name_empty_raises():
    with pytest.raises(ValidationError):
        SignupRequest(name="", email="a@b.c", password="12345678")


def test_signup_request_name_too_long_raises():
    with pytest.raises(ValidationError):
        SignupRequest(name="x" * 51, email="a@b.c", password="12345678")


def test_signup_request_name_missing_raises():
    with pytest.raises(ValidationError):
        SignupRequest(email="a@b.c", password="12345678")


# ── T-028: UserResponse name 필드 (acceptance #5~#6) ────────────────────────

def test_user_response_has_name_field_required():
    fields = UserResponse.model_fields
    assert "name" in fields
    assert fields["name"].annotation is str
    assert fields["name"].is_required()


def test_user_response_name_missing_raises():
    with pytest.raises(ValidationError):
        UserResponse(id=uuid.uuid4(), email="a@b.c")


# ── T-028: LoginRequest name 부재 (acceptance #7) ────────────────────────────

def test_login_request_has_no_name_field():
    assert "name" not in LoginRequest.model_fields


# ── T-028: AuthResponse 필드 목록 유지 (acceptance #8) ───────────────────────

def test_auth_response_fields_unchanged():
    assert set(AuthResponse.model_fields.keys()) == {"user", "expires_at", "token"}


# ── pyproject.toml에 email-validator 의존성 포함 (acceptance #11) ─────────────

def test_pyproject_toml_has_email_validator():
    with open("pyproject.toml") as f:
        content = f.read()
    has_dep = "email-validator" in content or "pydantic[email]" in content
    assert has_dep, "pyproject.toml에 email-validator 또는 pydantic[email] 없음"
