from app.validation_humanize import format_line_reference


def build_issue(
    *,
    level: str,
    category: str,
    rule_code: str,
    description: str,
    text: str,
    location: str | None = None,
    line: str | None = None,
    column: str | None = None,
    line_content: str | None = None,
    xpath_path: str | None = None,
    step_id: str | None = None,
    source: str = "xml",
    error_number: str | None = None,
) -> dict:
    level_label = "Warnung" if level == "warning" else "FEHLER"
    return {
        "level": level,
        "level_label": level_label,
        "location": location,
        "line": line,
        "column": column,
        "line_reference": format_line_reference(line, column),
        "line_content": line_content,
        "text": text,
        "description": description,
        "rule_code": rule_code,
        "error_number": error_number or rule_code,
        "category": category,
        "xpath_path": xpath_path,
        "step_id": step_id,
        "source": source,
    }
