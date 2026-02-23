import json
import logging
from typing import TypeVar

import anthropic
import httpx
from anthropic import transform_schema
from pydantic import BaseModel

from src.app.prompts.extraction import EXTRACTION_PROMPT

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Connect timeout stays short; read timeout must be long enough for LLM generation.
_CONNECT_TIMEOUT = 10.0


class LLMExtractor:
    """Abstraction over Anthropic SDK for structured data extraction.

    Provides two extraction paths:
    - extract_with_model: uses SDK's messages.parse() with a Pydantic model
    - extract_with_schema: uses messages.create() with a raw JSON Schema dict
    """

    def __init__(self, api_key: str, model: str, timeout: int = 120) -> None:
        self.client = anthropic.Anthropic(
            api_key=api_key,
            timeout=httpx.Timeout(timeout, connect=_CONNECT_TIMEOUT),
        )
        self.default_model = model

    def extract_with_model(
        self, text: str, output_format: type[T], model: str | None = None
    ) -> dict:
        """Extract structured data using a Pydantic model.

        Uses SDK's messages.parse() which handles schema transformation
        and response parsing automatically.

        Args:
            text: Document text extracted from PDF.
            output_format: Pydantic model class defining the output structure.
            model: Optional model override.

        Returns:
            dict from the parsed Pydantic model.
        """
        resolved_model = model or self.default_model
        prompt = EXTRACTION_PROMPT.format(document_text=text)

        logger.info(
            "Calling Anthropic API (parse): model=%s prompt_length=%d output_format=%s",
            resolved_model,
            len(prompt),
            output_format.__name__,
        )

        response = self.client.messages.parse(
            model=resolved_model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
            output_format=output_format,
        )

        logger.info(
            "Anthropic API response: request_id=%s input_tokens=%d output_tokens=%d stop_reason=%s",
            response.id,
            response.usage.input_tokens,
            response.usage.output_tokens,
            response.stop_reason,
        )

        return response.parsed_output.model_dump()

    def extract_with_schema(self, text: str, output_schema: dict, model: str | None = None) -> dict:
        """Extract structured data using a raw JSON Schema dict.

        Uses transform_schema() to clean the schema before passing
        it to the API via output_config.

        Args:
            text: Document text extracted from PDF.
            output_schema: JSON Schema dict with field names, types, and descriptions.
            model: Optional model override.

        Returns:
            dict guaranteed to conform to output_schema.
        """
        resolved_model = model or self.default_model
        prompt = EXTRACTION_PROMPT.format(document_text=text)
        transformed = transform_schema(output_schema)

        logger.info(
            "Calling Anthropic API (create): model=%s prompt_length=%d schema_fields=%d",
            resolved_model,
            len(prompt),
            len(output_schema.get("properties", {})),
        )

        response = self.client.messages.create(
            model=resolved_model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
            output_config={
                "format": {
                    "type": "json_schema",
                    "schema": transformed,
                }
            },
        )

        logger.info(
            "Anthropic API response: request_id=%s input_tokens=%d output_tokens=%d stop_reason=%s",
            response.id,
            response.usage.input_tokens,
            response.usage.output_tokens,
            response.stop_reason,
        )

        return json.loads(response.content[0].text)
