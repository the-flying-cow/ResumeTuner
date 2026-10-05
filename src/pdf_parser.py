from pathlib import Path

import pymupdf


def pdf_to_text(input_pdf_path, output_txt_path):
    input_path = Path(input_pdf_path)
    output_path = Path(output_txt_path)

    if not input_path.is_file():
        raise FileNotFoundError(f"PDF file was not found: {input_path}")

    try:
        with pymupdf.open(input_path) as document:
            extracted_text = "\n\n".join(page.get_text() for page in document).strip()
    except Exception as exc:
        raise ValueError(f"Could not read PDF '{input_path}': {exc}") from exc

    if not extracted_text:
        raise ValueError(
            f"No selectable text was found in '{input_path}'. If it is a scanned PDF, "
            "run OCR on it before continuing."
        )

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(extracted_text, encoding="utf-8")
    except OSError as exc:
        raise OSError(f"Could not write extracted text to '{output_path}': {exc}") from exc

    return output_path
