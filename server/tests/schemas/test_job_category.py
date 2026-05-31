import uuid

import pydantic
import pytest

from app.schemas.job_category import JobCategoryOut


def test_import_succeeds():
    assert JobCategoryOut is not None


def test_is_basemodel_subclass():
    assert issubclass(JobCategoryOut, pydantic.BaseModel)


def test_model_fields_keys():
    assert set(JobCategoryOut.model_fields.keys()) == {"id", "name"}


def test_id_field_annotation_is_uuid():
    assert JobCategoryOut.model_fields["id"].annotation is uuid.UUID


def test_name_field_annotation_is_str():
    assert JobCategoryOut.model_fields["name"].annotation is str


def test_id_coerced_to_uuid_from_string():
    instance = JobCategoryOut(id="550e8400-e29b-41d4-a716-446655440000", name="개발")
    assert isinstance(instance.id, uuid.UUID)
    assert instance.id == uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
