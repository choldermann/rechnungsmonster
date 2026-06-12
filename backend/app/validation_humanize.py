import re
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from io import BytesIO

from lxml import etree

CII_LINE_NS = {
    "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
}

ELEMENT_LABELS = {
    "Invoice": "Rechnung",
    "CrossIndustryInvoice": "Rechnung",
    "AccountingSupplierParty": "Verkäufer",
    "AccountingCustomerParty": "Käufer",
    "Party": "Beteiligter",
    "PartyName": "Name",
    "PartyLegalEntity": "Unternehmen",
    "PostalAddress": "Adresse",
    "Contact": "Kontakt",
    "TaxTotal": "Steuer",
    "TaxSubtotal": "Steuerposition",
    "LegalMonetaryTotal": "Summen",
    "InvoiceLine": "Rechnungsposition",
    "PaymentMeans": "Zahlungsart",
    "PaymentTerms": "Zahlungsbedingungen",
    "Delivery": "Lieferung",
    "SellerTradeParty": "Verkäufer",
    "BuyerTradeParty": "Käufer",
    "IncludedSupplyChainTradeLineItem": "Rechnungsposition",
    "SpecifiedTradeSettlementHeaderMonetarySummation": "Summen",
    "ExchangedDocument": "Dokumentkopf",
}

STEP_LABELS = {
    "val-xml": "XML-Verarbeitung",
    "val-xsd": "XML-Schema",
    "val-sch.1": "EN 16931",
    "val-sch.2": "XRechnung",
}

STEP_CATEGORIES = {
    "val-xsd": "Formatfehler",
    "val-sch.1": "Inhaltsfehler, EN 16931",
    "val-sch.2": "Inhaltsfehler, XRechnung",
}

NS_PREFIX_MAP = {
    "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100": "rsm",
    "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100": "ram",
    "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100": "udt",
    "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2": "ubl",
    "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2": "cbc",
    "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2": "cac",
}

MESSAGE_TRANSLATIONS = {
    "Buyer electronic address MUST be provided": (
        "Die elektronische Adresse des Käufers fehlt (z. B. Leitweg-ID oder Peppol-ID)."
    ),
    "Seller electronic address MUST be provided": (
        "Die elektronische Adresse des Verkäufers fehlt."
    ),
    "An Invoice shall have an Invoice number": "Die Rechnungsnummer fehlt.",
    "An Invoice shall have an Invoice issue date": "Das Rechnungsdatum fehlt.",
}


def humanize_xpath(xpath_location: str | None) -> str | None:
    if not xpath_location:
        return None

    parts = re.findall(r"Q\{[^}]+\}([^/\[]+)", xpath_location)
    if not parts:
        return None

    labels = [ELEMENT_LABELS.get(part, part) for part in parts]
    if labels and labels[0] == "Rechnung":
        labels = labels[1:]

    return " → ".join(labels) if labels else None


def extract_rule_code(text: str) -> str | None:
    match = re.search(r"\[([^\]]+)\]", text or "")
    return match.group(1) if match else None


def clean_message_text(text: str) -> str:
    cleaned = re.sub(r"^\[[^\]]+\]-?\s*", "", text.strip())
    return MESSAGE_TRANSLATIONS.get(cleaned, cleaned)


def format_description(text: str, rule_code: str | None = None) -> str:
    raw = (text or "").strip()
    match = re.match(r"^(\[[^\]]+\]-?)(.*)$", raw, re.DOTALL)
    if match:
        prefix, body = match.groups()
        translated = MESSAGE_TRANSLATIONS.get(body.strip(), body.strip())
        return f"{prefix}{translated}"

    translated = MESSAGE_TRANSLATIONS.get(raw, raw)
    if rule_code:
        return f"[{rule_code}]-{translated}"
    return translated


def format_xpath_path(xpath_location: str | None) -> str | None:
    if not xpath_location:
        return None

    segments = []
    for namespace, local_name, index_text in _xpath_parts(xpath_location):
        prefix = NS_PREFIX_MAP.get(namespace, "ns")
        index = index_text or "1"
        segments.append(f"/{prefix}:{local_name}[{index}]")

    return "\n".join(segments) if segments else None


def format_line_reference(line_number: str | int | None, column_number: str | int | None = None) -> str | None:
    if not line_number:
        return None
    if column_number:
        return f"Zeile {line_number}, Spalte {column_number}"
    return f"Zeile {line_number}"


def _xpath_parts(xpath_location: str) -> list[tuple[str, str, str | None]]:
    return re.findall(r"Q\{([^}]+)\}([^/\[]+)(?:\[(\d+)\])?", xpath_location)


def resolve_element_from_xpath(xml_content: str, xpath_location: str | None):
    if not xml_content or not xpath_location:
        return None

    parts = _xpath_parts(xpath_location)
    if not parts:
        return None

    try:
        tree = etree.parse(BytesIO(xml_content.encode("utf-8")))
        current = tree.getroot()
    except etree.XMLSyntaxError:
        return None

    root_qname = etree.QName(current)

    for step, (namespace, local_name, index_text) in enumerate(parts):
        index = int(index_text) if index_text else 1

        if (
            step == 0
            and root_qname.localname == local_name
            and (root_qname.namespace or "") == namespace
        ):
            if index != 1:
                return None
            continue

        matches = [
            element
            for element in current
            if etree.QName(element).localname == local_name
            and (etree.QName(element).namespace or "") == namespace
        ]
        if len(matches) < index:
            return None
        current = matches[index - 1]

    return current


def resolve_line_from_xpath(xml_content: str, xpath_location: str | None) -> int | None:
    element = resolve_element_from_xpath(xml_content, xpath_location)
    if element is None:
        return None
    return element.sourceline


def _truncate_text(text: str, max_length: int = 320) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= max_length:
        return compact
    return compact[: max_length - 1] + "…"


def get_physical_line_content(xml_content: str, line_number: str | int | None) -> str | None:
    if not xml_content or not line_number:
        return None

    try:
        line_index = int(line_number) - 1
        lines = xml_content.splitlines()
        if 0 <= line_index < len(lines):
            return lines[line_index].rstrip()
    except ValueError:
        return None

    return None


def get_line_content(
    xml_content: str,
    line_number: str | int | None,
    xpath_location: str | None = None,
) -> str | None:
    physical_line = get_physical_line_content(xml_content, line_number)
    if physical_line is not None:
        return _truncate_text(physical_line.strip())

    element = resolve_element_from_xpath(xml_content, xpath_location) if xpath_location else None
    if element is not None:
        return _truncate_text(etree.tostring(element, encoding="unicode"))

    return None


def humanize_xsd_message(text: str) -> str:
    lowered = text.lower()
    if "invalid content was found" in lowered or "is expected" in lowered:
        return (
            "Die XML-Struktur ist an dieser Stelle ungültig. "
            "Ein Pflichtfeld fehlt oder die Element-Reihenfolge ist falsch."
        )
    if "is not complete" in lowered:
        return "Die XML-Struktur ist unvollständig – ein Pflichtfeld fehlt."
    return text.strip()


def format_issue(message: dict, xml_content: str | None = None) -> dict:
    raw_text = (message.get("text") or "").strip()
    location = humanize_xpath(message.get("xpath_location"))
    xpath_path = format_xpath_path(message.get("xpath_location"))
    rule_code = extract_rule_code(raw_text) or message.get("code")
    step_id = message.get("step_id")
    category = STEP_CATEGORIES.get(step_id, "Inhaltsfehler, Sonstige")

    line_number = message.get("line_number")
    column_number = message.get("column_number")

    if not line_number and xml_content:
        resolved_line = resolve_line_from_xpath(xml_content, message.get("xpath_location"))
        if resolved_line:
            line_number = str(resolved_line)

    line_reference = format_line_reference(line_number, column_number)
    line_content = get_line_content(xml_content, line_number, message.get("xpath_location"))

    if message.get("line_number") and not message.get("xpath_location"):
        description = humanize_xsd_message(raw_text)
        text = description
    else:
        description = format_description(raw_text, rule_code)
        text = clean_message_text(raw_text)

    level = message.get("level")
    level_label = "Warnung" if level == "warning" else "FEHLER"

    return {
        "level": level,
        "level_label": level_label,
        "location": location,
        "line": line_number,
        "column": column_number,
        "line_reference": line_reference,
        "line_content": line_content,
        "text": text,
        "description": description,
        "rule_code": rule_code,
        "error_number": message.get("code"),
        "category": category,
        "xpath_path": xpath_path,
        "step_id": step_id,
        "source": "kosit",
    }


def _to_decimal(value: str | None) -> Decimal | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _line_item_index(issue: dict) -> int | None:
    xpath = (issue.get("xpath_path") or issue.get("xpath_location") or "").replace("\n", "")
    match = re.search(r"IncludedSupplyChainTradeLineItem\[(\d+)\]", xpath)
    if not match:
        match = re.search(r"InvoiceLine\[(\d+)\]", xpath)
    if not match:
        return None
    return int(match.group(1))


def _line_total_matches_quantity_times_price(tree, issue: dict) -> bool:
    index = _line_item_index(issue)
    if index is None:
        return False

    cii_lines = tree.xpath("//ram:IncludedSupplyChainTradeLineItem", namespaces=CII_LINE_NS)
    if 1 <= index <= len(cii_lines):
        line_item = cii_lines[index - 1]
        net_amount = _to_decimal(
            line_item.xpath(
                "string(.//ram:NetPriceProductTradePrice/ram:ChargeAmount)",
                namespaces=CII_LINE_NS,
            )
        )
        billed_quantity = _to_decimal(
            line_item.xpath("string(.//ram:BilledQuantity)", namespaces=CII_LINE_NS)
        )
        line_total = _to_decimal(
            line_item.xpath(
                "string(.//ram:SpecifiedTradeSettlementLineMonetarySummation/ram:LineTotalAmount)",
                namespaces=CII_LINE_NS,
            )
        )
        if net_amount is None or billed_quantity is None or line_total is None:
            return False
        expected = _money(net_amount * billed_quantity)
        return expected == line_total

    return False


def filter_kosit_line_total_warnings(issues: list[dict], xml_content: str | None) -> list[dict]:
    if not xml_content:
        return issues

    try:
        tree = etree.parse(BytesIO(xml_content.encode("utf-8")))
    except etree.XMLSyntaxError:
        return issues

    filtered = []
    for issue in issues:
        rule_code = issue.get("rule_code") or ""
        if rule_code != "PEPPOL-EN16931-R120":
            filtered.append(issue)
            continue
        if _line_total_matches_quantity_times_price(tree, issue):
            continue
        filtered.append(issue)
    return filtered


def recompute_checks_from_issues(checks: list[dict], issues: list[dict]) -> list[dict]:
    issues_by_step: dict[str, list[dict]] = defaultdict(list)
    for issue in issues:
        step_id = issue.get("step_id")
        if step_id:
            issues_by_step[step_id].append(issue)

    recomputed = []
    for check in checks:
        step_id = check.get("id")
        step_issues = issues_by_step.get(step_id, [])
        if not step_issues:
            recomputed.append(
                {
                    **check,
                    "valid": True,
                    "status": "green",
                }
            )
            continue

        status = step_status(check.get("valid", True), step_issues)
        recomputed.append(
            {
                **check,
                "valid": status == "green",
                "status": status,
            }
        )
    return recomputed


def step_status(step_valid: bool, messages: list[dict]) -> str:
    levels = {message.get("level") for message in messages}
    if not step_valid or "error" in levels or "fatal" in levels:
        return "red"
    if "warning" in levels:
        return "yellow"
    return "green"


def combine_overall_result(
    *,
    kosit_available: bool,
    kosit_issues: list[dict],
    extended_issues: list[dict],
) -> tuple[bool | None, str, str, str]:
    if not kosit_available:
        return (
            None,
            "gray",
            "Validierung nicht möglich",
            "Der offizielle KoSIT-Validator war nicht erreichbar.",
        )

    kosit_errors = [
        issue for issue in kosit_issues if issue.get("level") in ("error", "fatal")
    ]
    kosit_warnings = [issue for issue in kosit_issues if issue.get("level") == "warning"]
    extended_errors = [
        issue for issue in extended_issues if issue.get("level") in ("error", "fatal")
    ]
    extended_warnings = [
        issue for issue in extended_issues if issue.get("level") == "warning"
    ]

    if kosit_errors:
        return (
            False,
            "red",
            "Die Rechnung ist nach KoSIT ungültig",
            (
                "Das offizielle Prüfergebnis meldet Fehler in der XML-Validierung "
                "(XRechnung / EN 16931). Eine Verarbeitung als E-Rechnung ist damit "
                "in der Regel nicht möglich."
            ),
        )

    if not extended_issues:
        if kosit_warnings:
            return (
                True,
                "yellow",
                "Offiziell gültig mit Hinweisen",
                "KoSIT meldet nur Hinweise, keine Fehler. Zusatzprüfungen ohne Befund.",
            )
        return (
            True,
            "green",
            "Die Rechnung ist gültig",
            "KoSIT und Zusatzprüfungen ohne Beanstandung.",
        )

    if extended_errors:
        label = "Offiziell gültig – Zusatzprüfungen mit Abweichungen"
    else:
        label = "Offiziell gültig – Zusatzprüfungen mit Hinweisen"

    return (
        True,
        "yellow",
        label,
        (
            "Das offizielle KoSIT-Ergebnis ist gültig. Zusatzprüfungen melden weitere "
            "Abweichungen (z. B. PDF/A, XMP-Metadaten, ergänzende XML-Regeln). "
            "Die Datei kann nach XRechnung-Standard verarbeitet werden – manche Empfänger "
            "oder Tools prüfen strenger und lehnen solche Abweichungen ggf. ab."
        ),
    )


def overall_traffic_light(valid: bool, checks: list[dict], issues: list[dict]) -> tuple[str, str]:
    if not checks and not valid:
        return "red", "Die Rechnung ist ungültig"

    if not valid:
        return "red", "Die Rechnung ist ungültig"

    if any(issue["level"] == "warning" for issue in issues):
        return "yellow", "Die Rechnung ist gültig, enthält aber Hinweise"

    if any(check["status"] == "yellow" for check in checks):
        return "yellow", "Die Rechnung ist gültig, enthält aber Hinweise"

    return "green", "Die Rechnung ist gültig"
