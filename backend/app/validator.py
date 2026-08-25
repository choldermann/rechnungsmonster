import os
import urllib.error
import urllib.parse
import urllib.request
from xml.etree import ElementTree as ET

from app.validation_humanize import (
    STEP_LABELS,
    format_issue,
    overall_traffic_light,
    step_status,
)

VALIDATOR_URL = os.getenv("VALIDATOR_URL", "http://validator:8081")
REP_NS = "http://www.xoev.de/de/validator/varl/1"
SCENARIO_NS = "http://www.xoev.de/de/validator/framework/1/scenarios"


def _rep_tag(name: str) -> str:
    return f"{{{REP_NS}}}{name}"


def _scenario_tag(name: str) -> str:
    return f"{{{SCENARIO_NS}}}{name}"


def _parse_message_node(message) -> dict:
    return {
        "level": message.attrib.get("level"),
        "code": message.attrib.get("code"),
        "text": (message.text or "").strip(),
        "xpath_location": message.attrib.get("xpathLocation"),
        "line_number": message.attrib.get("lineNumber"),
        "column_number": message.attrib.get("columnNumber"),
    }


def parse_validation_report(report_xml: str, xml_content: str | None = None) -> dict:
    root = ET.fromstring(report_xml)
    valid = root.attrib.get("valid") == "true"

    scenario = None
    scenario_node = root.find(
        f".//{_rep_tag('scenarioMatched')}/{_scenario_tag('scenario')}/{_scenario_tag('name')}"
    )
    if scenario_node is not None and scenario_node.text:
        scenario = scenario_node.text.strip()

    raw_messages = []
    for step in root.findall(f".//{_rep_tag('validationStepResult')}"):
        step_id = step.attrib.get("id", "")
        for message in step.findall(_rep_tag("message")):
            parsed_message = _parse_message_node(message)
            parsed_message["step_id"] = step_id
            raw_messages.append(parsed_message)

    issues = [
        format_issue(message, xml_content)
        for message in raw_messages
        if message.get("level") in ("error", "warning", "fatal")
    ]

    checks = []
    for step in root.findall(f".//{_rep_tag('validationStepResult')}"):
        step_id = step.attrib.get("id", "")
        step_messages = [_parse_message_node(message) for message in step.findall(_rep_tag("message"))]
        status = step_status(step.attrib.get("valid") == "true", step_messages)
        checks.append(
            {
                "id": step_id,
                "label": STEP_LABELS.get(step_id, step_id),
                "status": status,
                "valid": step.attrib.get("valid") == "true",
            }
        )

    if root.find(f".//{_rep_tag('noScenarioMatched')}") is not None:
        checks = [
            {
                "id": "scenario",
                "label": "Rechnungsformat",
                "status": "red",
                "valid": False,
            }
        ]
        issues.insert(
            0,
            {
                "level": "error",
                "location": "Rechnung",
                "text": (
                    "Die Datei konnte keinem unterstützten XRechnung-Format zugeordnet werden. "
                    "Prüfen Sie, ob es sich um eine gültige XRechnung (UBL oder CII) handelt."
                ),
            },
        )

    traffic_light, traffic_label = overall_traffic_light(valid, checks, issues)

    errors = [issue for issue in issues if issue["level"] in ("error", "fatal")]
    warnings = [issue for issue in issues if issue["level"] == "warning"]

    return {
        "valid": valid,
        "traffic_light": traffic_light,
        "traffic_label": traffic_label,
        "scenario": scenario,
        "checks": checks,
        "issues": issues,
        "error_count": len(errors),
        "warning_count": len(warnings),
    }


def validate_invoice_xml(xml_content: str, filename: str = "invoice.xml") -> dict:
    if not xml_content.strip():
        return {
            "available": False,
            "valid": None,
            "http_status": None,
            "summary": None,
            "report": None,
            "error": "Kein XML-Inhalt vorhanden",
        }

    url = f"{VALIDATOR_URL.rstrip('/')}/{urllib.parse.quote(filename)}"
    request = urllib.request.Request(
        url,
        data=xml_content.encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/xml"},
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            report = response.read().decode("utf-8")
            return {
                "available": True,
                "valid": response.status == 200,
                "http_status": response.status,
                "summary": parse_validation_report(report, xml_content),
                "report": report,
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        report = exc.read().decode("utf-8")
        summary = (
            parse_validation_report(report, xml_content)
            if report.strip().startswith("<?xml")
            else None
        )
        return {
            "available": True,
            "valid": False,
            "http_status": exc.code,
            "summary": summary,
            "report": report,
            "error": None,
        }
    except urllib.error.URLError as exc:
        return {
            "available": False,
            "valid": None,
            "http_status": None,
            "summary": {
                "traffic_light": "gray",
                "traffic_label": "Validierung nicht möglich",
                "checks": [],
                "issues": [
                    {
                        "level": "error",
                        "location": None,
                        "text": f"Der Validator ist nicht erreichbar ({exc.reason}).",
                    }
                ],
                "error_count": 1,
                "warning_count": 0,
            },
            "report": None,
            "error": f"Validator nicht erreichbar: {exc.reason}",
        }
