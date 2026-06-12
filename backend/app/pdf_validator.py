import json
import os
import subprocess
from pathlib import Path

import pikepdf
from lxml import etree

from app.issue_builder import build_issue
from app.pdf_extractor import extract_xml_from_pdf

VERAPDF_BIN = os.getenv("VERAPDF_BIN", "/opt/verapdf/verapdf")
FACTURX_NS = {
    "fx": "urn:factur-x:pdfa:CrossIndustryDocument:invoice:1p0#",
    "pdfa": "http://www.aiim.org/pdfa/ns/id/",
}


def _run_verapdf(filepath: str) -> dict:
    if not Path(VERAPDF_BIN).exists():
        return {
            "available": False,
            "valid": None,
            "profile": None,
            "issues": [
                build_issue(
                    level="warning",
                    category="PDF/A",
                    rule_code="RM-PDFA-UNAVAILABLE",
                    description="PDF/A-Prüfung ist auf diesem Server nicht verfügbar.",
                    text="PDF/A-Prüfung ist auf diesem Server nicht verfügbar.",
                    step_id="pdfa",
                    source="pdf",
                )
            ],
        }

    result = subprocess.run(
        [VERAPDF_BIN, "-f", "3b", "--format", "json", filepath],
        capture_output=True,
        text=True,
        timeout=120,
    )

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "available": False,
            "valid": None,
            "profile": "PDF/A-3b",
            "issues": [
                build_issue(
                    level="warning",
                    category="PDF/A",
                    rule_code="RM-PDFA-ERROR",
                    description="Die PDF/A-Prüfung konnte nicht ausgewertet werden.",
                    text=result.stderr.strip() or "PDF/A-Prüfung fehlgeschlagen.",
                    step_id="pdfa",
                    source="pdf",
                )
            ],
        }

    validation_results = (
        payload.get("report", {})
        .get("jobs", [{}])[0]
        .get("validationResult", [])
    )
    if not validation_results:
        return {"available": True, "valid": True, "profile": "PDF/A-3b", "issues": []}

    details = validation_results[0]
    compliant = details.get("compliant", False)
    issues = []

    for rule in details.get("details", {}).get("ruleSummaries", []):
        if rule.get("ruleStatus") != "FAILED":
            continue
        for check in rule.get("checks", []):
            if check.get("status") != "failed":
                continue
            message = check.get("errorMessage") or rule.get("description") or "PDF/A-Regel verletzt"
            issues.append(
                build_issue(
                    level="error",
                    category="PDF/A",
                    rule_code=f"PDFA-{rule.get('clause')}-{rule.get('testNumber')}",
                    description=f"[PDF/A]-{message}",
                    text=message,
                    location=check.get("context"),
                    step_id="pdfa",
                    source="pdf",
                )
            )

    if not issues and not compliant:
        issues.append(
            build_issue(
                level="error",
                category="PDF/A",
                rule_code="PDFA-3B",
                description="[PDF/A]-Die PDF-Datei ist nicht PDF/A-3b-konform.",
                text="Die PDF-Datei ist nicht PDF/A-3b-konform.",
                step_id="pdfa",
                source="pdf",
            )
        )

    return {
        "available": True,
        "valid": compliant,
        "profile": details.get("profileName", "PDF/A-3b"),
        "issues": issues,
    }


def _read_facturx_xmp(filepath: str) -> dict:
    with pikepdf.open(filepath) as pdf:
        pdfa_status = None
        with pdf.open_metadata() as meta:
            pdfa_status = meta.pdfa_status
            xmp_bytes = meta._get_xml_bytes()

    root = etree.fromstring(xmp_bytes)
    document_type = root.xpath("string(//fx:DocumentType)", namespaces=FACTURX_NS).strip()
    document_file = root.xpath("string(//fx:DocumentFileName)", namespaces=FACTURX_NS).strip()
    version_elements = root.xpath("//fx:Version", namespaces=FACTURX_NS)
    if version_elements:
        version = (version_elements[0].text or "").strip()
        version_present = True
    else:
        version = None
        version_present = False
    conformance = root.xpath("string(//fx:ConformanceLevel)", namespaces=FACTURX_NS).strip()
    has_null = "\x00" in xmp_bytes.decode("utf-8", errors="replace")

    return {
        "pdfa_status": str(pdfa_status) if pdfa_status else None,
        "document_type": document_type or None,
        "document_file": document_file or None,
        "version": version if version_present else None,
        "version_present": version_present,
        "version_empty": version_present and not version,
        "conformance": conformance or None,
        "has_null": has_null,
    }


def validate_pdf_hybrid(filepath: str) -> dict:
    path = Path(filepath)
    if path.suffix.lower() != ".pdf":
        return {
            "available": False,
            "checks": [],
            "issues": [],
            "metadata": {},
        }

    issues: list[dict] = []
    checks: list[dict] = []

    xml_content, attachment_name = extract_xml_from_pdf(filepath)
    embedding_valid = xml_content is not None

    checks.append(
        {
            "id": "embedding",
            "label": "XML-Einbettung",
            "valid": embedding_valid,
            "status": "green" if embedding_valid else "red",
        }
    )

    if not embedding_valid:
        issues.append(
            build_issue(
                level="error",
                category="Einbettung",
                rule_code="RM-EMBED-MISSING",
                description="[RM-EMBED]-In der PDF-Datei wurde kein Rechnungs-XML gefunden.",
                text="In der PDF-Datei wurde kein Rechnungs-XML gefunden.",
                step_id="embedding",
                source="embedding",
            )
        )
        return {"available": True, "checks": checks, "issues": issues, "metadata": {}}

    checks.append(
        {
            "id": "embedding-name",
            "label": "Dateiname der Einbettung",
            "valid": bool(attachment_name),
            "status": "green" if attachment_name else "yellow",
        }
    )

    try:
        xmp = _read_facturx_xmp(filepath)
    except Exception as exc:
        xmp = {}
        issues.append(
            build_issue(
                level="warning",
                category="Einbettung",
                rule_code="RM-XMP-READ",
                description=f"[RM-XMP]-XMP-Metadaten konnten nicht gelesen werden: {exc}",
                text="XMP-Metadaten konnten nicht gelesen werden.",
                step_id="embedding",
                source="embedding",
            )
        )

    xmp_valid = True
    if xmp.get("has_null"):
        xmp_valid = False
        issues.append(
            build_issue(
                level="error",
                category="Einbettung",
                rule_code="RM-XMP-NULL",
                description=(
                    "[RM-XMP-032]-Die XMP-Metadaten der PDF-Datei enthalten unzulässige Zeichen "
                    "(z. B. NULL)."
                ),
                text="Die XMP-Metadaten enthalten unzulässige Zeichen.",
                step_id="embedding",
                source="embedding",
            )
        )

    if not xmp.get("version_present") or xmp.get("version_empty"):
        xmp_valid = False
        issues.append(
            build_issue(
                level="error",
                category="Einbettung",
                rule_code="RM-XMP-023",
                description=(
                    "[RM-XMP-023]-Der Wert der im PDF angegebenen Version des hybriden Dokuments "
                    "ist ungültig oder leer."
                ),
                text="Die Factur-X-Version in den XMP-Metadaten fehlt oder ist leer.",
                step_id="embedding",
                source="embedding",
            )
        )
        issues.append(
            build_issue(
                level="warning",
                category="Einbettung",
                rule_code="RM-XMP-025",
                description=(
                    "[RM-XMP-025]-Der Wert der im PDF angegebenen Version des hybriden Dokuments "
                    "soll >>3.0<< sein."
                ),
                text="Die erwartete Factur-X-Version 3.0 fehlt in den XMP-Metadaten.",
                step_id="embedding",
                source="embedding",
            )
        )
    elif xmp.get("version") != "3.0":
        xmp_valid = False
        issues.append(
            build_issue(
                level="warning",
                category="Einbettung",
                rule_code="RM-XMP-025",
                description=(
                    "[RM-XMP-025]-Der Wert der im PDF angegebenen Version des hybriden Dokuments "
                    f"soll >>3.0<< sein (gefunden: {xmp.get('version')})."
                ),
                text=f"Erwartete Factur-X-Version 3.0, gefunden: {xmp.get('version')}.",
                step_id="embedding",
                source="embedding",
            )
        )

    expected_file = xmp.get("document_file")
    if expected_file and attachment_name and expected_file != attachment_name:
        xmp_valid = False
        issues.append(
            build_issue(
                level="warning",
                category="Einbettung",
                rule_code="RM-XMP-FILENAME",
                description=(
                    f"[RM-XMP-FILE]-Der in den XMP-Metadaten genannte Dateiname ({expected_file}) "
                    f"weicht vom eingebetteten Anhang ({attachment_name}) ab."
                ),
                text="Der XMP-Dateiname stimmt nicht mit dem eingebetteten XML überein.",
                step_id="embedding",
                source="embedding",
            )
        )

    checks.append(
        {
            "id": "xmp",
            "label": "XMP Metadaten",
            "valid": xmp_valid,
            "status": "green" if xmp_valid else "red",
        }
    )

    pdfa = _run_verapdf(filepath)
    checks.append(
        {
            "id": "pdfa",
            "label": "PDF/A-3",
            "valid": pdfa.get("valid"),
            "status": "green" if pdfa.get("valid") else "red" if pdfa.get("valid") is False else "gray",
        }
    )
    issues.extend(pdfa.get("issues", []))

    return {
        "available": True,
        "checks": checks,
        "issues": issues,
        "metadata": {
            **xmp,
            "attachment_name": attachment_name,
            "pdfa_profile": pdfa.get("profile"),
            "pdfa_valid": pdfa.get("valid"),
        },
    }
