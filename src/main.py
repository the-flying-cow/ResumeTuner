import importlib.util
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"
TEXT_DIR = PROJECT_ROOT / "text_files"
ANALYSIS_FILE = OUTPUT_DIR / "analysis.json"
REPORT_FILE = OUTPUT_DIR / "report.md"
STREAMLIT_APP = Path(__file__).resolve().parent / "streamlit_app.py"


def ensure_directories():
    try:
        for directory in (INPUT_DIR, OUTPUT_DIR, TEXT_DIR):
            directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise RuntimeError(f"Could not create the required application directories: {exc}") from exc


def ensure_dependencies():
    required_packages = {
        "pymupdf": "PyMuPDF",
        "ollama": "ollama",
        "pydantic": "Pydantic",
        "streamlit": "Streamlit",
    }
    missing_packages = [
        display_name
        for module_name, display_name in required_packages.items()
        if importlib.util.find_spec(module_name) is None
    ]
    if missing_packages:
        names = ", ".join(missing_packages)
        raise RuntimeError(
            f"Missing required packages: {names}. Install the project dependencies "
            "with 'pip install -r requirements.txt'."
        )


def find_pdf_by_keywords(*keywords):
    try:
        pdf_files = sorted(INPUT_DIR.glob("*.pdf"))
    except OSError as exc:
        raise RuntimeError(f"Could not read PDFs in {INPUT_DIR}: {exc}") from exc

    for pdf_file in pdf_files:
        if any(keyword in pdf_file.stem.lower() for keyword in keywords):
            return pdf_file
    return None


def prompt_for_files():
    while True:
        choice = input(
            "Place the resume PDF and job description PDF in the input folder. "
            "Type Y when ready, or N to exit: "
        ).strip().upper()
        if choice in {"Y", "N"}:
            return choice == "Y"
        print("Please enter Y or N.")


def validate_input_files():
    resume_pdf = find_pdf_by_keywords("resume", "cv")
    jd_pdf = find_pdf_by_keywords("jd", "job", "description")

    if resume_pdf is None:
        raise FileNotFoundError(
            f"No resume PDF found in {INPUT_DIR}. Name it with 'resume' or 'cv' in the filename."
        )
    if jd_pdf is None:
        raise FileNotFoundError(
            f"No job description PDF found in {INPUT_DIR}. Include 'jd', 'job', or 'description' "
            "in its filename."
        )
    if resume_pdf == jd_pdf:
        raise ValueError("The resume and job description resolved to the same PDF file.")

    return resume_pdf, jd_pdf


def run_pdf_parsing(resume_pdf, jd_pdf):
    try:
        from pdf_parser import pdf_to_text

        resume_text = TEXT_DIR / "resume.txt"
        jd_text = TEXT_DIR / "jd.txt"
        pdf_to_text(resume_pdf, resume_text)
        pdf_to_text(jd_pdf, jd_text)
        return resume_text, jd_text
    except Exception as exc:
        raise RuntimeError(f"Could not extract text from the input PDFs: {exc}") from exc


def run_llm_analysis(resume_text, jd_text):
    try:
        from llm import analyze_resume

        result_path = analyze_resume(resume_text, jd_text, ANALYSIS_FILE)
        if not Path(result_path).is_file():
            raise RuntimeError(f"LLM analysis did not produce the expected JSON file: {result_path}")
        return Path(result_path)
    except Exception as exc:
        raise RuntimeError(f"Resume analysis failed: {exc}") from exc


def generate_markdown_report():
    try:
        from formatter import format_json_to_markdown

        return format_json_to_markdown(ANALYSIS_FILE, REPORT_FILE)
    except Exception as exc:
        raise RuntimeError(f"Could not format the validated analysis as Markdown: {exc}") from exc


def launch_streamlit():
    if importlib.util.find_spec("streamlit") is None:
        raise RuntimeError(
            "Streamlit is not installed. Install the project requirements before running the app."
        )
    if not STREAMLIT_APP.is_file():
        raise FileNotFoundError(f"Streamlit application file is missing: {STREAMLIT_APP}")
    if not REPORT_FILE.is_file():
        raise FileNotFoundError(f"Markdown report is missing: {REPORT_FILE}")

    print("Analysis is ready. Starting the Streamlit application...")
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(STREAMLIT_APP),
            "--server.address",
            "127.0.0.1",
        ],
        cwd=PROJECT_ROOT,
        check=False,
    ).returncode


def main():
    try:
        ensure_directories()
        if not prompt_for_files():
            print("Cancelled. Add the PDF files to the input folder and run again.")
            return 0

        ensure_dependencies()
        resume_pdf, jd_pdf = validate_input_files()
        resume_text, jd_text = run_pdf_parsing(resume_pdf, jd_pdf)
        run_llm_analysis(resume_text, jd_text)
        generate_markdown_report()
        return launch_streamlit()
    except (FileNotFoundError, ValueError, RuntimeError, OSError) as exc:
        print(f"Error: {exc}")
        return 1
    except KeyboardInterrupt:
        print("\nStopped by user.")
        return 130
    except Exception as exc:
        print(f"Unexpected error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
