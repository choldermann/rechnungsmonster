from app.validation_humanize import (
    combine_overall_result,
    filter_kosit_line_total_warnings,
    overall_traffic_light,
    recompute_checks_from_issues,
)
from app.xml_rules import validate_xml_rules
from app.pdf_validator import validate_pdf_hybrid

def _dedupe_issues(issues: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for issue in issues:
        key = (
            issue.get("level"),
            issue.get("rule_code"),
            issue.get("line"),
            issue.get("xpath_path"),
            issue.get("text"),
            issue.get("source"),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(issue)
    return unique


def _tag_kosit_issues(issues: list[dict]) -> list[dict]:
    tagged = []
    for issue in issues:
        item = dict(issue)
        item.setdefault("source", "kosit")
        tagged.append(item)
    return tagged


def _section_summary(
    *,
    valid: bool | None,
    checks: list[dict],
    issues: list[dict],
) -> dict:
    errors = [issue for issue in issues if issue.get("level") in ("error", "fatal")]
    warnings = [issue for issue in issues if issue.get("level") == "warning"]
    section_valid = len(errors) == 0

    traffic_light, traffic_label = overall_traffic_light(section_valid, checks, issues)

    return {
        "valid": section_valid,
        "traffic_light": traffic_light,
        "traffic_label": traffic_label,
        "checks": checks,
        "issues": issues,
        "error_count": len(errors),
        "warning_count": len(warnings),
    }


def merge_validation(
    kosit_validation: dict | None,
    *,
    xml_content: str | None,
    filepath: str,
    is_pdf: bool,
) -> dict:
    if not kosit_validation:
        kosit_validation = {
            "available": False,
            "valid": None,
            "summary": None,
        }

    kosit_summary = dict(kosit_validation.get("summary") or {})
    kosit_issues = filter_kosit_line_total_warnings(
        _tag_kosit_issues(list(kosit_summary.get("issues") or [])),
        xml_content,
    )
    kosit_checks = recompute_checks_from_issues(
        list(kosit_summary.get("checks") or []),
        kosit_issues,
    )

    extended_checks: list[dict] = []
    extended_issues: list[dict] = []

    extended_issues.extend(validate_xml_rules(xml_content or ""))

    pdf_meta = {}
    if is_pdf:
        pdf_result = validate_pdf_hybrid(filepath)
        pdf_meta = pdf_result.get("metadata", {})
        extended_checks.extend(pdf_result.get("checks", []))
        extended_issues.extend(pdf_result.get("issues", []))

    extended_issues = _dedupe_issues(extended_issues)
    all_issues = _dedupe_issues(kosit_issues + extended_issues)
    all_checks = kosit_checks + extended_checks

    kosit_section = _section_summary(
        valid=None,
        checks=kosit_checks,
        issues=kosit_issues,
    )
    extended_section = _section_summary(
        valid=None if not extended_checks and not extended_issues else None,
        checks=extended_checks,
        issues=extended_issues,
    )
    if not extended_checks and not extended_issues:
        extended_section = {
            **extended_section,
            "valid": True,
            "traffic_light": "green",
            "traffic_label": "Keine Zusatzbefunde",
            "checks": [],
            "issues": [],
            "error_count": 0,
            "warning_count": 0,
        }
    elif extended_section.get("error_count", 0) > 0:
        extended_section = {
            **extended_section,
            "traffic_light": "yellow",
            "traffic_label": "Abweichungen in Zusatzprüfungen",
        }
    elif extended_section.get("warning_count", 0) > 0:
        extended_section = {
            **extended_section,
            "traffic_light": "yellow",
            "traffic_label": "Hinweise in Zusatzprüfungen",
        }

    overall_valid, overall_traffic, overall_label, overall_note = combine_overall_result(
        kosit_available=bool(kosit_validation.get("available")),
        kosit_issues=kosit_issues,
        extended_issues=extended_issues,
    )

    errors = [issue for issue in all_issues if issue.get("level") in ("error", "fatal")]
    warnings = [issue for issue in all_issues if issue.get("level") == "warning"]

    merged_summary = {
        **kosit_summary,
        "valid": overall_valid,
        "traffic_light": overall_traffic,
        "traffic_label": overall_label,
        "overall_note": overall_note,
        "checks": all_checks,
        "issues": all_issues,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "pdf_metadata": pdf_meta,
        "kosit": {
            "available": kosit_validation.get("available"),
            "title": "KoSIT Validator",
            "subtitle": "Offizielle XML-Validierung (XRechnung / EN 16931)",
            "scenario": kosit_summary.get("scenario"),
            **kosit_section,
        },
        "extended": {
            "available": bool(extended_checks or extended_issues or is_pdf or xml_content),
            "title": "Zusatzprüfungen",
            "subtitle": (
                "Erweitertes Verfahren: PDF/A, XMP-Metadaten und ergänzende XML-Regeln – "
                "beeinflusst das offizielle KoSIT-Ergebnis nicht"
            ),
            **extended_section,
        },
    }

    return {
        **kosit_validation,
        "valid": overall_valid,
        "summary": merged_summary,
    }
