import json

import anthropic

from src.app.prompts.extraction import EXTRACTION_PROMPT


class LLMExtractor:
    """Abstraction over Anthropic SDK for structured data extraction.

    Uses Anthropic's Structured Output feature (output_config with json_schema)
    to guarantee the response conforms to the caller-provided JSON schema.
    """

    def __init__(self, api_key: str, model: str) -> None:
        self.client = anthropic.Anthropic(api_key=api_key)
        self.default_model = model

    def extract(self, text: str, output_schema: dict, model: str | None = None) -> dict:
        """Extract structured data from text.

        Args:
            text: Document text extracted from PDF.
            output_schema: JSON Schema with field names, types, and descriptions.
            model: Optional model override.

        Returns:
            dict guaranteed to conform to output_schema.
        """
        prompt = EXTRACTION_PROMPT.format(document_text=text)

        response = self.client.messages.create(
            model=model or self.default_model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
            output_config={
                "format": {
                    "type": "json_schema",
                    "schema": output_schema,
                }
            },
        )

        return json.loads(response.content[0].text)
