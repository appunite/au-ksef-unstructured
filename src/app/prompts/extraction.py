EXTRACTION_PROMPT = """You are an expert document data extraction specialist.

Extract structured data from the following document text according to the provided schema.

Rules:
- Return ONLY data explicitly present in the document.
- If a field cannot be found in the document, use null.
- For numeric fields, extract the numeric value without currency symbols.
- For date fields, use ISO 8601 format (YYYY-MM-DD) when possible.
- Be precise — do not infer or guess values that are not clearly stated.

Document text:
{document_text}"""
