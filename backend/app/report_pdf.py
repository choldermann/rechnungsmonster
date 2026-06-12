import io
from datetime import datetime, timezone
from io import BytesIO

from fpdf import FPDF
from lxml import etree

FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

VALIDATOR_VERSION = (
    "KoSIT Validator 1.6.1 / XRechnung 3.0.2 / veraPDF 1.30.1 / Rechnungsmonster Zusatzprüfungen"
)

SITE_URL = "https://rechnungsmonster.monstersuite.de"
SITE_LABEL = "rechnungsmonster.monstersuite.de"

DISCLAIMER = (
    "Die von Rechnungsmonster bereitgestellten Validierungsergebnisse, Hinweise und Empfehlungen "
    "dienen ausschließlich der technischen Prüfung elektronischer Rechnungen und stellen keine "
    "Rechts-, Steuer- oder Unternehmensberatung dar.\n\n"
    "Die Validierung erfolgt auf Basis der jeweils unterstützten Standards und Regelwerke. "
    "Trotz sorgfältiger Entwicklung übernimmt Rechnungsmonster keine Gewähr für die Richtigkeit, "
    "Vollständigkeit oder Aktualität der bereitgestellten Informationen und Prüfergebnisse.\n\n"
    "Die Nutzung der Ergebnisse erfolgt auf eigenes Risiko. Für Entscheidungen oder Maßnahmen, "
    "die auf Grundlage der bereitgestellten Informationen getroffen werden, wird keine Haftung "
    "übernommen. Im Zweifel sollte fachkundiger Rat eingeholt werden.\n\n"
    "Hinweis: Ein erfolgreiches Validierungsergebnis bedeutet nicht automatisch, dass eine "
    "Rechnung steuerlich, rechtlich oder buchhalterisch korrekt ist."
)


class ReportPDF(FPDF):
    def footer(self):
        self.set_y(-12)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(90, 90, 90)
        self.set_x(self.l_margin)
        self.cell(0, 6, SITE_LABEL, link=SITE_URL, align="L")
        self.set_y(-12)
        self.set_x(self.l_margin)
        self.cell(0, 6, f"Seite {self.page_no()}/{{nb}}", align="R")


def _safe_text(value) -> str:
    if value is None or value == "":
        return "-"
    return str(value)


def _status_label(ok: bool | None) -> str:
    if ok is True:
        return "Fehlerfrei"
    if ok is False:
        return "Nicht fehlerfrei"
    return "Nicht geprüft"


def _write_section_title(pdf: ReportPDF, title: str) -> None:
    pdf.ln(3)
    pdf.set_font("DejaVu", "B", 12)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def _write_key_value(pdf: ReportPDF, key: str, value: str, key_width: float = 52) -> None:
    pdf.set_x(pdf.l_margin)
    y = pdf.get_y()
    pdf.set_font("DejaVu", "B", 9)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(key_width, 5, key, new_x="RIGHT", new_y="TOP")
    pdf.set_xy(pdf.l_margin + key_width, y)
    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(20, 20, 20)
    pdf.multi_cell(pdf.epw - key_width, 5, _safe_text(value), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def _write_overview_row(pdf: ReportPDF, key: str, value: str) -> None:
    pdf.set_font("DejaVu", "B", 9)
    pdf.cell(78, 6, key)
    pdf.set_font("DejaVu", "", 9)
    pdf.multi_cell(pdf.epw - 78, 6, _safe_text(value), new_x="LMARGIN", new_y="NEXT")


def _write_detail_rows(pdf: ReportPDF, rows: list[tuple[str, str]]) -> None:
    for key, value in rows:
        pdf.set_x(pdf.l_margin)
        y = pdf.get_y()
        pdf.set_font("DejaVu", "B", 8)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(42, 5, key, new_x="RIGHT", new_y="TOP")
        pdf.set_xy(pdf.l_margin + 42, y)
        pdf.set_font("DejaVu", "", 8)
        pdf.set_text_color(20, 20, 20)
        pdf.multi_cell(pdf.epw - 42, 4.8, _safe_text(value), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(0.5)


def _extract_xml_metadata(xml_content: str | None) -> dict:
    if not xml_content:
        return {}

    try:
        tree = etree.parse(BytesIO(xml_content.encode("utf-8")))
    except etree.XMLSyntaxError:
        return {}

    ns = {
        "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
        "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    }

    customization = tree.xpath(
        "string(//ram:GuidelineSpecifiedDocumentContextParameter/ram:ID)",
        namespaces=ns,
    )
    if not customization:
        customization = tree.xpath("string(//cbc:CustomizationID)", namespaces=ns)

    country = tree.xpath(
        "string(//ram:SellerTradeParty/ram:PostalTradeAddress/ram:CountryID)",
        namespaces=ns,
    )
    if not country:
        country = tree.xpath(
            "string(//cac:AccountingSupplierParty//cac:Country/cbc:IdentificationCode)",
            namespaces=ns,
        )

    return {
        "customization_id": customization or None,
        "seller_country": country or None,
    }


def _detect_variant(detected: dict, xml_meta: dict) -> str:
    customization = (xml_meta.get("customization_id") or "").lower()
    format_name = (detected.get("format") or "").lower()

    if "xrechnung" in customization or "xrechnung" in format_name:
        return "XRECHNUNG"
    if "cii" in format_name or "crossindustry" in format_name:
        return "CII"
    if "ubl" in format_name:
        return "UBL"
    return "UNBEKANNT"


def _detect_version(detected: dict) -> str:
    format_name = (detected.get("format") or "").lower()
    if "cii" in format_name or "zugferd" in format_name or "factur" in format_name:
        return "XRechnung 3.0.2 CII"
    if "ubl" in format_name:
        return "XRechnung 3.0.2 UBL"
    return "XRechnung 3.0.2"


def _check_by_id(checks: list[dict], step_id: str) -> dict | None:
    for check in checks:
        if check.get("id") == step_id:
            return check
    return None


def _build_overall_summary(issues: list[dict], valid: bool) -> list[str]:
    errors = [issue for issue in issues if issue.get("level") in ("error", "fatal")]
    warnings = [issue for issue in issues if issue.get("level") == "warning"]
    paragraphs = []

    if errors:
        numbers = ", ".join(str(index + 1) for index in range(len(errors)))
        paragraphs.append(
            "Die Datei enthält inhaltliche Abweichungen in Bezug auf Geschäftsregeln des "
            f"verwendeten Formats. Grund sind die folgenden Fehlernummern: {numbers}"
        )

    format_errors = [issue for issue in errors if issue.get("step_id") == "val-xsd"]
    if format_errors:
        numbers = ", ".join(
            str(index + 1)
            for index, issue in enumerate(issues)
            if issue.get("step_id") == "val-xsd" and issue.get("level") in ("error", "fatal")
        )
        paragraphs.append(
            "Hinweis:\nDie Datei enthält Formatfehler. Es handelt sich somit nicht um eine "
            "E-Rechnung im Sinne des § 14 UStG, sondern um eine sonstige Rechnung in einem "
            f"anderen elektronischen Format. Grund sind die folgenden Fehlernummern: {numbers}"
        )

    if warnings and not errors:
        numbers = ", ".join(
            str(index + 1)
            for index, issue in enumerate(issues)
            if issue.get("level") == "warning"
        )
        paragraphs.append(
            "Die Datei enthält Hinweise und Warnungen. Betroffene Nummern: "
            f"{numbers}"
        )

    if valid and not warnings:
        paragraphs.append("Die Datei ist bezüglich der geprüften XML-Regeln fehlerfrei.")

    return paragraphs


def generate_report_pdf(
    *,
    original_filename: str,
    detected: dict,
    invoice: dict,
    lines: list,
    validation: dict | None,
    xml_content: str | None = None,
) -> bytes:
    pdf = ReportPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_font("DejaVu", "", FONT_REGULAR)
    pdf.add_font("DejaVu", "B", FONT_BOLD)
    pdf.add_page()

    checked_at = datetime.now(timezone.utc).astimezone().strftime("%d. %B %Y, %H:%M:%S")
    checked_at = (
        checked_at.replace("January", "Januar")
        .replace("February", "Februar")
        .replace("March", "März")
        .replace("April", "April")
        .replace("May", "Mai")
        .replace("June", "Juni")
        .replace("July", "Juli")
        .replace("August", "August")
        .replace("September", "September")
        .replace("October", "Oktober")
        .replace("November", "November")
        .replace("December", "Dezember")
    )

    summary = validation.get("summary") if validation else None
    checks = summary.get("checks", []) if summary else []
    issues = summary.get("issues", []) if summary else []
    valid = summary.get("valid") if summary else None
    kosit_summary = summary.get("kosit") if summary else None
    extended_summary = summary.get("extended") if summary else None
    kosit_issues = (kosit_summary or {}).get("issues") or [
        issue for issue in issues if issue.get("source") == "kosit" or not issue.get("source")
    ]
    extended_issues = (extended_summary or {}).get("issues") or [
        issue for issue in issues if issue.get("source") not in (None, "kosit")
    ]
    xml_meta = _extract_xml_metadata(xml_content)

    is_hybrid = detected.get("file_type") == "pdf" and detected.get("embedded_attachment")
    pruefmodus = "HYBRID_DOCUMENT" if is_hybrid else "XML_DOCUMENT"

    pdf.set_font("DejaVu", "B", 16)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 10, "Validierungsbericht", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 5, "Rechnungsmonster", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    _write_section_title(pdf, "Allgemeine Informationen")
    _write_key_value(pdf, "Getestete Datei", original_filename)
    _write_key_value(pdf, "Belegnummer", invoice.get("invoice_number"))
    _write_key_value(pdf, "Belegdatum (XML)", invoice.get("invoice_date"))
    _write_key_value(pdf, "Verkäufer", invoice.get("supplier"))
    _write_key_value(pdf, "Verkäuferland", xml_meta.get("seller_country"))
    _write_key_value(pdf, "Getestet am", checked_at)
    _write_key_value(pdf, "Version", VALIDATOR_VERSION)
    _write_key_value(pdf, "Prüfmodus", pruefmodus)
    _write_key_value(pdf, "Dokumentenart", "INVOICE")

    overall_note = summary.get("overall_note") if summary else None
    overall_label = summary.get("traffic_label") if summary else None
    if overall_note:
        overall_text = f"{overall_label}\n\n{overall_note}"
    else:
        overall_text = "\n\n".join(_build_overall_summary(issues, bool(valid)))
        if not overall_text:
            overall_text = _safe_text(overall_label)
    _write_key_value(pdf, "Gesamtergebnis", overall_text)

    _write_section_title(pdf, "Ergebnisübersicht")
    _write_overview_row(pdf, "1) KoSIT – offizielle XML-Validierung", "")
    _write_overview_row(
        pdf,
        "Ergebnis KoSIT",
        _status_label(kosit_summary.get("valid") if kosit_summary else valid),
    )
    if kosit_summary and kosit_summary.get("scenario"):
        _write_overview_row(pdf, "Szenario", kosit_summary.get("scenario"))
    _write_overview_row(pdf, "Validierung der XML-Datei", "")
    _write_overview_row(pdf, "Gesamtergebnis XML", _status_label(kosit_summary.get("valid") if kosit_summary else valid))
    _write_overview_row(pdf, "Gefundene CIUS/Extension", xml_meta.get("customization_id") or "-")
    _write_overview_row(pdf, "Variante", _detect_variant(detected, xml_meta))
    _write_overview_row(pdf, "Version", _detect_version(detected))
    _write_overview_row(
        pdf,
        "Formatfehler",
        _status_label(_check_by_id(checks, "val-xsd")["valid"] if _check_by_id(checks, "val-xsd") else None),
    )
    content_issue = any(
        issue.get("level") in ("error", "fatal", "warning")
        and issue.get("step_id") != "val-xsd"
        for issue in issues
    )
    _write_overview_row(pdf, "Inhaltsfehler, Sonstige", _status_label(not content_issue))
    _write_overview_row(
        pdf,
        "XML-Struktur (Schema)",
        _status_label(_check_by_id(checks, "val-xsd")["valid"] if _check_by_id(checks, "val-xsd") else None),
    )
    _write_overview_row(pdf, "Kodierung (UTF-8)", _status_label(_check_by_id(checks, "val-xml")["valid"] if _check_by_id(checks, "val-xml") else None))
    _write_overview_row(
        pdf,
        "Gibt es Warnungen?",
        "Es sind Warnungen vorhanden"
        if any(i.get("level") == "warning" for i in kosit_issues)
        else "Keine Warnungen",
    )

    if extended_summary:
        pdf.ln(2)
        _write_overview_row(pdf, "Zusatzprüfungen Rechnungsmonster", "")
        _write_overview_row(
            pdf,
            "Ergebnis Zusatzprüfungen",
            _status_label(extended_summary.get("valid")),
        )

    if is_hybrid:
        pdf_meta = summary.get("pdf_metadata", {}) if summary else {}
        embedding_check = _check_by_id(checks, "embedding")
        xmp_check = _check_by_id(checks, "xmp")
        pdfa_check = _check_by_id(checks, "pdfa")

        pdf.ln(2)
        _write_overview_row(pdf, "2) Einbettung der XML-Datei in die PDF-Datei", "")
        _write_overview_row(
            pdf,
            "Korrekte Einbettung",
            _status_label(embedding_check.get("valid") if embedding_check else None),
        )
        _write_overview_row(
            pdf,
            "Dateiname korrekt",
            _safe_text(pdf_meta.get("attachment_name") or detected.get("embedded_attachment")),
        )
        _write_overview_row(pdf, "Extraktion der XML-Datei", "Möglich" if embedding_check and embedding_check.get("valid") else "Nicht möglich")
        _write_overview_row(
            pdf,
            "XMP Metadaten",
            _status_label(xmp_check.get("valid") if xmp_check else None),
        )
        version_value = pdf_meta.get("version")
        if pdf_meta.get("version_empty"):
            version_value = "(leer)"
        elif not pdf_meta.get("version_present"):
            version_value = "(fehlt)"
        _write_overview_row(pdf, "Factur-X Version", _safe_text(version_value))
        _write_overview_row(
            pdf,
            "Factur-X Konformitätsstufe",
            _safe_text(pdf_meta.get("conformance")),
        )

        pdf.ln(2)
        _write_overview_row(pdf, "3) PDF/A-Konformität", "")
        _write_overview_row(
            pdf,
            "Profil",
            _safe_text(pdf_meta.get("pdfa_profile") or "PDF/A-3b"),
        )
        _write_overview_row(
            pdf,
            "Ergebnis",
            _status_label(pdfa_check.get("valid") if pdfa_check else None),
        )

    def _write_issue_block(section_issues: list[dict], section_title: str) -> None:
        if not section_issues:
            return

        _write_section_title(pdf, section_title)
        for index, issue in enumerate(section_issues, start=1):
            if pdf.get_y() > 250:
                pdf.add_page()

            pdf.set_font("DejaVu", "B", 10)
            pdf.set_text_color(20, 20, 20)
            pdf.cell(0, 6, f"{index})", new_x="LMARGIN", new_y="NEXT")

            line_col = issue.get("line_reference", "-")
            if issue.get("column"):
                line_col = f"{issue.get('line', '-')}, {issue.get('column')}"

            source_label = "XML" if issue.get("source") == "kosit" else "Zusatzprüfung"
            rows = [
                ("Kategorie", f"{issue.get('level_label', 'FEHLER')} ({source_label})"),
                ("Fehlernummer", issue.get("error_number") or issue.get("rule_code") or "-"),
                ("Fehlerkategorie", issue.get("category") or "-"),
                ("Beschreibung", issue.get("description") or issue.get("text") or "-"),
                ("Zeile, Spalte", line_col),
            ]
            if issue.get("line_content"):
                rows.append(("XML-Zeile", issue.get("line_content")))
            if issue.get("xpath_path"):
                rows.append(("XML Path", issue.get("xpath_path")))
            elif issue.get("location"):
                rows.append(("Pfad", issue.get("location")))

            _write_detail_rows(pdf, rows)
            pdf.ln(2)

    if kosit_issues:
        _write_issue_block(kosit_issues, "KoSIT – Validierungsdetails (offiziell)")
    if extended_issues:
        _write_issue_block(extended_issues, "Zusatzprüfungen – Validierungsdetails")
    if not kosit_issues and not extended_issues and valid:
        _write_section_title(pdf, "Validierungsdetails")
        _write_key_value(pdf, "Ergebnis", "Keine Fehler oder Warnungen gefunden.")

    pdf.ln(4)
    pdf.set_font("DejaVu", "", 7.5)
    pdf.set_text_color(100, 100, 100)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw, 4, DISCLAIMER, new_x="LMARGIN", new_y="NEXT")

    buffer = io.BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()
