"""Response parsing and validation utilities for LLM outputs."""

import json
import logging
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMResponseParser:
    """Parse and validate LLM responses."""

    def __init__(self, max_retries: int = 3) -> None:
        """Initialize parser.

        Args:
            max_retries: Maximum number of retry attempts for validation failures
        """
        self.max_retries = max_retries

    def extract_json(self, response: str) -> str:
        """Extract JSON from response (handle markdown code blocks).

        Args:
            response: Raw LLM response string

        Returns:
            Extracted JSON string

        Raises:
            ValueError: If no valid JSON found in response
        """
        response = response.strip()

        # Remove markdown code blocks if present
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            if end != -1:
                return response[start:end].strip()

        elif "```" in response:
            # Generic code block - try to extract first block
            start = response.find("```") + 3
            # Skip any language identifier (e.g., "json", "yaml")
            newline = response.find("\n", start)
            if newline != -1:
                start = newline + 1
            end = response.find("```", start)
            if end != -1:
                extracted = response[start:end].strip()
                # Validate it looks like JSON
                if extracted.startswith(("{", "[")):
                    return extracted

        # If no code blocks, check if the entire response is JSON
        if response.startswith(("{", "[")):
            return response

        # Try to find JSON object/array in the response
        # Look for first { or [ and corresponding closing bracket
        json_start = -1
        for char in ("{", "["):
            pos = response.find(char)
            if pos != -1 and (json_start == -1 or pos < json_start):
                json_start = pos

        if json_start != -1:
            # Try to find matching closing bracket
            open_char = response[json_start]
            close_char = "}" if open_char == "{" else "]"
            depth = 0
            for i in range(json_start, len(response)):
                if response[i] == open_char:
                    depth += 1
                elif response[i] == close_char:
                    depth -= 1
                    if depth == 0:
                        return response[json_start : i + 1]

        raise ValueError("No valid JSON found in response")

    def parse_json(self, json_str: str) -> Any:
        """Parse JSON string.

        Args:
            json_str: JSON string to parse

        Returns:
            Parsed JSON data

        Raises:
            ValueError: If JSON parsing fails
        """
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            raise ValueError(f"Invalid JSON: {e}") from e

    def validate_model(self, data: Any, model_class: type[T]) -> T:
        """Validate data against Pydantic model.

        Args:
            data: Data to validate
            model_class: Pydantic model class

        Returns:
            Validated model instance

        Raises:
            ValueError: If validation fails
        """
        try:
            if isinstance(data, list):
                # Handle list of models
                return [model_class.model_validate(item) for item in data]  # type: ignore
            else:
                return model_class.model_validate(data)
        except ValidationError as e:
            logger.error(f"Validation failed for {model_class.__name__}: {e}")
            raise ValueError(
                f"Validation failed for {model_class.__name__}: {e}"
            ) from e

    def parse_and_validate(
        self, response: str, model_class: type[T]
    ) -> T | list[T]:
        """Parse JSON response and validate against Pydantic model.

        Args:
            response: Raw LLM response string
            model_class: Pydantic model class for validation

        Returns:
            Validated model instance or list of instances

        Raises:
            ValueError: If parsing or validation fails
        """
        # Extract JSON
        json_str = self.extract_json(response)

        # Parse JSON
        data = self.parse_json(json_str)

        # Validate
        return self.validate_model(data, model_class)

    def create_retry_prompt(
        self, original_prompt: str, error: str, previous_response: str
    ) -> str:
        """Create a retry prompt with error feedback.

        Args:
            original_prompt: The original prompt
            error: Error message from parsing/validation
            previous_response: The previous failed response

        Returns:
            Enhanced prompt for retry
        """
        retry_prompt = f"""{original_prompt}

IMPORTANT: Your previous response had an error:
{error}

Previous response (first 200 chars): {previous_response[:200]}...

Please provide a valid JSON response following the exact format specified above.
Double-check that:
1. Your response is valid JSON
2. All required fields are included
3. Field types match the specification
4. Use proper JSON syntax (quotes, commas, brackets)

Provide ONLY the JSON output, no additional text."""

        return retry_prompt
