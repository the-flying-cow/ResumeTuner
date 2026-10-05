from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT_FILE = PROJECT_ROOT / "output" / "report.md"


def load_report():
    if not REPORT_FILE.is_file():
        raise FileNotFoundError(
            f"Markdown report was not found at {REPORT_FILE}. Run src/main.py to generate it."
        )

    try:
        report = REPORT_FILE.read_text(encoding="utf-8")
    except OSError as exc:
        raise OSError(f"Could not read {REPORT_FILE}: {exc}") from exc

    if not report.strip():
        raise ValueError(f"Markdown report is empty: {REPORT_FILE}")
    return report


def show_report(report):
    st.markdown(report)


st.set_page_config(page_title="ResumeTuner", page_icon="📄", layout="wide")

try:
    show_report(load_report())
except FileNotFoundError as exc:
    st.error(str(exc))
except ValueError as exc:
    st.error(f"The Markdown report could not be displayed: {exc}")
except OSError as exc:
    st.error(f"Could not load the analysis file: {exc}")
except Exception as exc:
    st.error(f"Unexpected error while displaying the analysis: {exc}")
