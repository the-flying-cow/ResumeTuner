import json
from pathlib import Path

from pydantic import ValidationError

from model_analysis import AnalysisResult


def _markdown_list(items, empty_message):
    if not items:
        return f"- {empty_message}"
    return "\n".join(f"- {item}" for item in items)


def analysis_to_markdown(analysis):
    lines = [
        "# Resume Match Analysis",
        "",
        "## Overall Assessment",
        "",
        analysis.overall_assessment.summary,
        "",
        f"**Readiness:** {analysis.overall_assessment.readiness}",
        "",
        "### Strengths",
        "",
        _markdown_list(analysis.overall_assessment.strengths, "No strengths identified."),
        "",
        "### Major Gaps",
        "",
        _markdown_list(analysis.overall_assessment.major_gaps, "No major gaps identified."),
        "",
        "## Similarity Matches",
        "",
    ]

    if analysis.similarity_matches:
        for match in analysis.similarity_matches:
            lines.extend(
                [
                    f"### {match.jd_requirement}",
                    "",
                    f"**Resume evidence:** {match.resume_evidence}",
                    "",
                    f"**Why it matches:** {match.match_explanation}",
                    "",
                ]
            )
    else:
        lines.extend(["No clear matches identified.", ""])

    lines.extend(["## Differences and Gaps", ""])
    if analysis.differences_and_gaps:
        for gap in analysis.differences_and_gaps:
            lines.extend(
                [
                    f"### {gap.jd_requirement}",
                    "",
                    f"**Related resume evidence:** {gap.resume_evidence}",
                    "",
                    f"**What is missing:** {gap.gap_explanation}",
                    "",
                ]
            )
    else:
        lines.extend(["No partial matches or gaps identified.", ""])

    lines.extend(["## Missing Requirements", ""])
    if analysis.missing_requirements:
        for requirement in analysis.missing_requirements:
            lines.extend(
                [
                    f"### {requirement.jd_requirement}",
                    "",
                    f"**Importance:** {requirement.importance}",
                    "",
                    f"**Reason:** {requirement.reason}",
                    "",
                ]
            )
    else:
        lines.extend(["No missing requirements identified.", ""])

    lines.extend(["## Preparation Priorities", ""])
    if analysis.preparation_priorities:
        for item in analysis.preparation_priorities:
            lines.extend(
                [
                    f"### {item.priority}: {item.topic}",
                    "",
                    item.reason,
                    "",
                ]
            )
    else:
        lines.extend(["No preparation priorities identified.", ""])

    return "\n".join(lines).rstrip() + "\n"


def format_json_to_markdown(json_path, markdown_path):
    source_path = Path(json_path)
    output_path = Path(markdown_path)

    if not source_path.is_file():
        raise FileNotFoundError(f"Analysis JSON was not found: {source_path}")

    try:
        raw_json = source_path.read_text(encoding="utf-8")
        analysis = AnalysisResult.model_validate_json(raw_json)
    except ValidationError as exc:
        errors = "; ".join(
            f"{'.'.join(str(part) for part in error['loc']) or 'response'}: {error['msg']}"
            for error in exc.errors()
        )
        raise ValueError(f"Analysis JSON failed validation: {errors}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Analysis file contains invalid JSON: {exc}") from exc
    except OSError as exc:
        raise OSError(f"Could not read analysis JSON: {exc}") from exc

    markdown = analysis_to_markdown(analysis)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
    except OSError as exc:
        raise OSError(f"Could not save Markdown report to {output_path}: {exc}") from exc

    print(f"Markdown report generated: {output_path}")
    return output_path
