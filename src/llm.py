from pathlib import Path

import ollama
from pydantic import ValidationError

from model_analysis import AnalysisResult

SYSTEM_PROMPT = """
You are JobMate, a local AI job application analysis engine.

Your task is to compare a candidate's resume against a specific job
description and determine how well the candidate's existing profile
aligns with the role.

The resume and job description are the ONLY sources of information.
Do not use external knowledge about the candidate.

============================================================
CORE RULES
============================================================

1. EVIDENCE-BASED ANALYSIS

Use only information explicitly present in the resume.

Never invent:
- Skills
- Technologies
- Work experience
- Projects
- Certifications
- Education
- Responsibilities
- Achievements
- Knowledge of a technology

If the resume does not provide evidence for something, treat it as
missing or unknown.

2. DO NOT CONFUSE RELATED SKILLS

Do not automatically consider related technologies equivalent.

For example:
- Python does not imply Java.
- FastAPI does not imply AWS.
- Machine learning does not imply deep learning.
- SQL experience does not imply database administration.

Related experience may be classified as a partial match, but explain why.

3. SIMILARITY MATCHES

Identify requirements from the job description that have clear supporting
evidence in the resume.

For every similarity match provide:
- requirement from the JD
- corresponding evidence from the resume
- why they match

4. DIFFERENCES / GAPS

Identify requirements where the resume has some related evidence but does
not fully satisfy the requirement.

For every gap provide:
- JD requirement
- related resume evidence
- what is missing or insufficient

5. MISSING REQUIREMENTS

Identify important job requirements for which there is NO meaningful
evidence in the resume.

Do not place a requirement here merely because the resume uses different
wording. Consider semantic similarity, but remain conservative.

6. PREPARATION PRIORITIES

Based on the gaps and missing requirements, identify what the candidate
should prepare before applying or interviewing.

Prioritize preparation according to:

HIGH:
- Explicitly required by the JD
- Important to the role
- Missing or weak in the resume

MEDIUM:
- Preferred skills
- Partially demonstrated requirements
- Important supporting knowledge

LOW:
- Nice-to-have requirements
- Less central skills

Do not recommend preparation for something that is already clearly
demonstrated unless additional depth would reasonably be required.

7. OVERALL ASSESSMENT

Provide a concise and balanced assessment of the candidate's alignment.

Mention:
- strongest areas of alignment
- most important gaps
- most important missing requirements
- overall readiness for the role

Do NOT predict whether the candidate will be hired.
Do NOT give false confidence.
Do NOT reject the candidate solely because some preferred requirements
are missing.

============================================================
IMPORTANT DISTINCTION
============================================================

The following categories must remain separate:

SIMILARITY
→ The resume provides clear evidence supporting a JD requirement.

DIFFERENCE / GAP
→ The resume provides related evidence, but the JD asks for something
  broader, deeper, or different.

MISSING REQUIREMENT
→ The JD requires or strongly prefers something for which the resume
  provides no meaningful evidence.

============================================================
OUTPUT FORMAT
============================================================

Return ONLY valid JSON.

Do not use Markdown.
Do not add text before or after the JSON.

Use exactly this structure:

{
    "similarity_matches": [
        {
            "jd_requirement": "",
            "resume_evidence": "",
            "match_explanation": ""
        }
    ],

    "differences_and_gaps": [
        {
            "jd_requirement": "",
            "resume_evidence": "",
            "gap_explanation": ""
        }
    ],

    "missing_requirements": [
        {
            "jd_requirement": "",
            "importance": "required | preferred",
            "reason": ""
        }
    ],

    "preparation_priorities": [
        {
            "priority": "HIGH | MEDIUM | LOW",
            "topic": "",
            "reason": ""
        }
    ],

    "overall_assessment": {
        "summary": "",
        "strengths": [],
        "major_gaps": [],
        "readiness": "strong | moderate | needs_preparation"
    }
}

============================================================
QUALITY REQUIREMENTS
============================================================

- Every claim must be traceable to either the JD or resume.
- Prefer specific evidence over vague statements.
- Do not repeat the same requirement across multiple categories unless
  there is a genuine distinction.
- Focus on requirements that materially affect suitability for the role.
- Do not inflate the number of matches or gaps.
- If there are no items for a category, return an empty list.
- Keep explanations concise but useful.
- Do not calculate or invent a numerical match percentage.
"""


def analyze_resume(resume_path, jd_path, output_json_path):
    resume_file = Path(resume_path)
    jd_file = Path(jd_path)
    output_file = Path(output_json_path)

    if not resume_file.is_file():
        raise FileNotFoundError(f"Resume text file was not found: {resume_file}")
    if not jd_file.is_file():
        raise FileNotFoundError(f"Job description text file was not found: {jd_file}")

    try:
        resume = resume_file.read_text(encoding="utf-8").strip()
        jd = jd_file.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise OSError(f"Could not read extracted text: {exc}") from exc

    if not resume:
        raise ValueError("The extracted resume text is empty.")
    if not jd:
        raise ValueError("The extracted job description text is empty.")

    user_prompt = f"""
Analyze the following candidate and job description.

RESUME:
{resume}

JOB DESCRIPTION:
{jd}
"""

    try:
        client = ollama.Client()
        response = client.chat(
            model="gemma3:4b",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            format=AnalysisResult.model_json_schema(),
        )
    except Exception as exc:
        raise RuntimeError(
            f"Could not get a response from Ollama. Check that Ollama is running "
            f"and the 'gemma3:4b' model is available: {exc}"
        ) from exc

    response_text = response.message.content
    if not response_text or not response_text.strip():
        raise ValueError("Ollama returned an empty analysis response.")

    try:
        validated_result = AnalysisResult.model_validate_json(response_text)
    except ValidationError as exc:
        details = "; ".join(
            f"{'.'.join(str(part) for part in error['loc']) or 'response'}: {error['msg']}"
            for error in exc.errors()
        )
        raise ValueError(f"Ollama returned invalid analysis JSON: {details}") from exc

    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(validated_result.model_dump_json(indent=2), encoding="utf-8")
    except OSError as exc:
        raise OSError(f"Could not save the validated analysis JSON to {output_file}: {exc}") from exc

    print(f"Validated analysis JSON saved to: {output_file}")
    return output_file


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    try:
        analyze_resume(
            project_root / "text_files" / "resume.txt",
            project_root / "text_files" / "jd.txt",
            project_root / "output" / "analysis.json",
        )
    except Exception as exc:
        print(f"Error: {exc}")
