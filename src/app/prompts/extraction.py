EXTRACTION_PROMPT = """You are an expert at extracting structured data from invoices.

The text below was extracted from a PDF invoice using OCR. It may contain:
- Misread characters (e.g., O/0, l/1, S/5 confusion)
- Broken or misaligned table rows
- Merged or split lines

Rules:
- Extract ONLY data explicitly present in the document.
- For fields not found on the invoice: if the schema allows null, return null. If the field is
required, return an empty string for text fields and 0 for numeric fields.
- For numeric fields, extract the numeric value without currency symbols or thousand separators.
- For date fields, use ISO 8601 format (YYYY-MM-DD). Be aware that US invoices use MM/DD/YYYY and
European invoices use DD/MM/YYYY. If the format is ambiguous (e.g. 03/04/2025), use other clues such
as language, currency, or the fact that most invoices are issued around the current date.
- For tax identification numbers, correct obvious OCR errors (O→0, l→1, S→5) when the result
produces a valid ID.
- For line items: extract only actual product/service lines, skip subtotals, totals, and summary
rows.
- Be precise — do not infer or guess values that are not clearly stated.

Additional context:
{context}

Document text:
{document_text}
"""
