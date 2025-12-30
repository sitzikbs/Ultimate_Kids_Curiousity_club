"""Tests for LLM response parsing utilities."""

import json

import pytest
from pydantic import BaseModel, Field

from services.llm.parsing import LLMResponseParser


class SampleModel(BaseModel):
    """Sample model for testing."""

    name: str = Field(..., description="Name field")
    value: int = Field(..., description="Value field")


class TestLLMResponseParser:
    """Tests for LLMResponseParser."""

    def test_extract_json_plain(self):
        """Test extracting JSON from plain response."""
        parser = LLMResponseParser()
        response = '{"name": "test", "value": 42}'

        result = parser.extract_json(response)
        assert result == '{"name": "test", "value": 42}'

    def test_extract_json_with_json_code_block(self):
        """Test extracting JSON from markdown json code block."""
        parser = LLMResponseParser()
        response = """Here is the JSON:
```json
{"name": "test", "value": 42}
```
Done!"""

        result = parser.extract_json(response)
        assert result == '{"name": "test", "value": 42}'

    def test_extract_json_with_generic_code_block(self):
        """Test extracting JSON from generic code block."""
        parser = LLMResponseParser()
        response = """Here is the result:
```
{"name": "test", "value": 42}
```"""

        result = parser.extract_json(response)
        assert result == '{"name": "test", "value": 42}'

    def test_extract_json_array(self):
        """Test extracting JSON array."""
        parser = LLMResponseParser()
        response = '[{"name": "test1", "value": 1}, {"name": "test2", "value": 2}]'

        result = parser.extract_json(response)
        assert result == '[{"name": "test1", "value": 1}, {"name": "test2", "value": 2}]'

    def test_extract_json_embedded_in_text(self):
        """Test extracting JSON embedded in text."""
        parser = LLMResponseParser()
        response = 'Some text before {"name": "test", "value": 42} and after'

        result = parser.extract_json(response)
        assert result == '{"name": "test", "value": 42}'

    def test_extract_json_nested_objects(self):
        """Test extracting nested JSON objects."""
        parser = LLMResponseParser()
        response = """
        Text before
        {"outer": {"inner": {"name": "test", "value": 42}}, "other": "data"}
        Text after
        """

        result = parser.extract_json(response)
        data = json.loads(result)
        assert data["outer"]["inner"]["name"] == "test"

    def test_extract_json_no_valid_json(self):
        """Test error when no valid JSON found."""
        parser = LLMResponseParser()
        response = "This is just plain text with no JSON"

        with pytest.raises(ValueError, match="No valid JSON found"):
            parser.extract_json(response)

    def test_parse_json_valid(self):
        """Test parsing valid JSON string."""
        parser = LLMResponseParser()
        json_str = '{"name": "test", "value": 42}'

        result = parser.parse_json(json_str)
        assert result == {"name": "test", "value": 42}

    def test_parse_json_invalid(self):
        """Test error on invalid JSON."""
        parser = LLMResponseParser()
        json_str = '{"name": "test", "value": }'  # Invalid JSON

        with pytest.raises(ValueError, match="Invalid JSON"):
            parser.parse_json(json_str)

    def test_validate_model_valid(self):
        """Test validating valid data."""
        parser = LLMResponseParser()
        data = {"name": "test", "value": 42}

        result = parser.validate_model(data, SampleModel)
        assert isinstance(result, SampleModel)
        assert result.name == "test"
        assert result.value == 42

    def test_validate_model_list(self):
        """Test validating list of models."""
        parser = LLMResponseParser()
        data = [
            {"name": "test1", "value": 1},
            {"name": "test2", "value": 2},
        ]

        result = parser.validate_model(data, SampleModel)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].name == "test1"
        assert result[1].name == "test2"

    def test_validate_model_missing_field(self):
        """Test validation error on missing field."""
        parser = LLMResponseParser()
        data = {"name": "test"}  # Missing 'value'

        with pytest.raises(ValueError, match="Validation failed"):
            parser.validate_model(data, SampleModel)

    def test_validate_model_wrong_type(self):
        """Test validation error on wrong type."""
        parser = LLMResponseParser()
        data = {"name": "test", "value": "not_an_int"}

        with pytest.raises(ValueError, match="Validation failed"):
            parser.validate_model(data, SampleModel)

    def test_parse_and_validate_success(self):
        """Test complete parse and validate flow."""
        parser = LLMResponseParser()
        response = """Here is the data:
```json
{"name": "test", "value": 42}
```"""

        result = parser.parse_and_validate(response, SampleModel)
        assert isinstance(result, SampleModel)
        assert result.name == "test"
        assert result.value == 42

    def test_parse_and_validate_list(self):
        """Test parse and validate with list."""
        parser = LLMResponseParser()
        response = '[{"name": "test1", "value": 1}, {"name": "test2", "value": 2}]'

        result = parser.parse_and_validate(response, SampleModel)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_parse_and_validate_failure(self):
        """Test parse and validate with invalid data."""
        parser = LLMResponseParser()
        response = '{"name": "test"}'  # Missing required field

        with pytest.raises(ValueError):
            parser.parse_and_validate(response, SampleModel)

    def test_create_retry_prompt(self):
        """Test creating retry prompt with error feedback."""
        parser = LLMResponseParser()
        original_prompt = "Generate a JSON object"
        error = "Missing required field 'value'"
        previous_response = '{"name": "test"}'

        retry_prompt = parser.create_retry_prompt(
            original_prompt, error, previous_response
        )

        assert "Generate a JSON object" in retry_prompt
        assert "Missing required field 'value'" in retry_prompt
        assert "previous response" in retry_prompt.lower()

    def test_extract_json_with_whitespace(self):
        """Test extracting JSON with extra whitespace."""
        parser = LLMResponseParser()
        response = """
        
        {"name": "test", "value": 42}
        
        """

        result = parser.extract_json(response)
        assert result.strip() == '{"name": "test", "value": 42}'

    def test_extract_json_array_in_code_block(self):
        """Test extracting JSON array from code block."""
        parser = LLMResponseParser()
        response = """```json
[
  {"name": "test1", "value": 1},
  {"name": "test2", "value": 2}
]
```"""

        result = parser.extract_json(response)
        data = json.loads(result)
        assert len(data) == 2
