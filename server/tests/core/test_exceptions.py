def test_unauthorized_error_class_exists():
    from app.core.exceptions import UnauthorizedError  # noqa: F401


def test_unauthorized_error_inherits_app_error():
    from app.core.exceptions import AppError, UnauthorizedError

    assert issubclass(UnauthorizedError, AppError)


def test_unauthorized_error_status_code_is_401():
    from app.core.exceptions import UnauthorizedError

    assert UnauthorizedError.status_code == 401


# T-053: AddressNotFound


def test_address_not_found_importable():
    from app.core.exceptions import AddressNotFound  # noqa: F401


def test_address_not_found_inherits_app_error():
    from app.core.exceptions import AddressNotFound, AppError

    assert issubclass(AddressNotFound, AppError)


def test_address_not_found_status_code_is_400():
    from app.core.exceptions import AddressNotFound

    assert AddressNotFound.status_code == 400


def test_address_not_found_message_stored():
    from app.core.exceptions import AddressNotFound

    exc = AddressNotFound("address_not_found")
    assert exc.message == "address_not_found"


def test_existing_exceptions_still_importable():
    from app.core.exceptions import (  # noqa: F401
        AppError,
        ConflictError,
        NotFoundError,
        UnauthorizedError,
        ValidationError,
    )
