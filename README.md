# ResumeTuner

ResumeTuner compares a resume with a job description using a local Ollama model. It validates the analysis with Pydantic, saves JSON and Markdown outputs, and displays the Markdown report in Streamlit.

## Main tools

- Python 3.10+
- [Ollama](https://ollama.com/) with the `gemma3:4b` model
- PyMuPDF for extracting text from PDFs
- Pydantic for validating the model response
- Streamlit for displaying the report

The Python libraries are listed in `requirements.txt`.

## Setup

1. Install Python and [Ollama](https://ollama.com/).
2. Open a terminal and download the model:

   ```powershell
   ollama pull gemma3:4b
   ```
   
3. From the project directory, create and activate a virtual environment (PowerShell):

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell does not allow activation, use the environment's Python executable directly in the following commands.

4. Install the Python dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

5. Make sure Ollama is running before launching ResumeTuner. The Ollama desktop application normally starts its local service; otherwise, start it in a separate terminal:

   ```powershell
   ollama serve
   ```

## Add your PDFs

Place one resume PDF and one job description PDF in the project's `input/` folder. Resume filenames must include `resume` or `cv`; job description filenames must include `jd`, `job`, or `description`. For example:

```text
input/
├── resume.pdf
└── job_description.pdf
```

The PDFs must contain selectable text. Scanned/image-only PDFs need OCR before processing.

## Run

From the project directory:

```powershell
python src/main.py
```

Confirm with `Y` when prompted. The program extracts the PDF text, asks Ollama to analyze it, validates and saves the response, generates a Markdown report, and then starts Streamlit in your browser. Enter `N` to exit without running the analysis.

## Output

- `text_files/resume.txt` and `text_files/jd.txt` — extracted PDF text
- `output/analysis.json` — validated structured analysis
- `output/report.md` — Markdown report shown in Streamlit

The report is available locally in the browser while the Streamlit process is running. Stop the server with `Ctrl+C` in the terminal.

## Troubleshooting

- **Ollama connection/model error:** confirm Ollama is running and `ollama list` shows `gemma3:4b`.
- **Missing PDF error:** check the `input/` folder and make sure filenames contain the expected keywords.
- **No selectable text:** OCR the PDF first; this application does not perform OCR.
- **Invalid response or validation error:** review the error shown in the terminal. The JSON is checked against the expected schema before it is saved.