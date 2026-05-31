import json

import pytest

from app.services.agents.sse import format_sse


def test_format_sse_starts_with_event_line():
    result = format_sse("token", {"agent": "echo", "text": "a"})
    assert result.startswith("event: token\n")


def test_format_sse_ends_with_double_newline():
    result = format_sse("token", {"agent": "echo", "text": "a"})
    assert result.endswith("\n\n")


def test_format_sse_data_line_contains_json_serialized_dict():
    data = {"agent": "echo", "text": "a"}
    result = format_sse("token", data)
    lines = result.split("\n")
    # lines: ["event: token", "data: <json>", "", ""]
    data_line = lines[1]
    assert data_line.startswith("data: ")
    parsed = json.loads(data_line[len("data: "):])
    assert parsed == data


def test_format_sse_korean_not_escaped():
    data = {"text": "안녕하세요"}
    result = format_sse("message", data)
    assert "안녕하세요" in result
    assert "\\uc548" not in result
