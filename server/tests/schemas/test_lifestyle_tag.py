import uuid

import pydantic
import pytest

from app.schemas.lifestyle_tag import LifestyleTagOut


def test_import_succeeds():
    assert LifestyleTagOut is not None


def test_is_basemodel_subclass():
    assert issubclass(LifestyleTagOut, pydantic.BaseModel)


def test_model_fields_keys_exact():
    assert set(LifestyleTagOut.model_fields.keys()) == {"id", "name"}


def test_id_field_annotation_is_uuid():
    assert LifestyleTagOut.model_fields["id"].annotation is uuid.UUID


def test_name_field_annotation_is_str():
    assert LifestyleTagOut.model_fields["name"].annotation is str


def test_model_dump_returns_correct_shape():
    instance = LifestyleTagOut(id="550e8400-e29b-41d4-a716-446655440000", name="식도락")
    dumped = instance.model_dump()
    assert dumped == {"id": uuid.UUID("550e8400-e29b-41d4-a716-446655440000"), "name": "식도락"}
