from pathlib import Path

from lxml import etree

from app.pdf_extractor import extract_xml_from_pdf


def resolve_xml_source(filepath: str) -> tuple[str | None, dict]:
    path = Path(filepath)

    if path.suffix.lower() == ".xml":
        return str(path), {"source": "xml"}

    if path.suffix.lower() == ".pdf":
        xml_content, attachment_name = extract_xml_from_pdf(filepath)
        if not xml_content:
            return None, {
                "source": "pdf",
                "embedded_xml": False,
                "pdf_xml_status": "Kein eingebettetes Rechnungs-XML gefunden",
            }

        xml_path = path.with_suffix(path.suffix + ".xml")
        xml_path.write_text(xml_content, encoding="utf-8")
        return str(xml_path), {
            "source": "pdf",
            "embedded_xml": True,
            "attachment_name": attachment_name,
            "pdf_xml_status": "XML aus PDF extrahiert",
        }

    return None, {"source": "unknown"}


def detect_invoice_format(filepath: str, xml_path: str | None = None, meta: dict | None = None) -> dict:
    path = Path(filepath)
    meta = meta or {}

    if path.suffix.lower() == ".pdf":
        if xml_path:
            xml_detected = detect_invoice_format(xml_path)
            return {
                "file_type": "pdf",
                "format": f"ZUGFeRD/Factur-X ({xml_detected['format']})",
                "parser_status": meta.get("pdf_xml_status", "XML aus PDF extrahiert"),
                "embedded_attachment": meta.get("attachment_name"),
                "xml_format": xml_detected,
            }

        return {
            "file_type": "pdf",
            "format": "PDF ohne eingebettetes Rechnungs-XML",
            "parser_status": meta.get("pdf_xml_status", "Kein eingebettetes XML"),
        }

    if path.suffix.lower() != ".xml":
        return {
            "file_type": "unknown",
            "format": "Unbekannt",
            "parser_status": "Nicht unterstützt",
        }

    tree = etree.parse(str(path))
    root = tree.getroot()

    root_name = etree.QName(root).localname
    namespace = etree.QName(root).namespace or ""

    if "CrossIndustryInvoice" in root_name:
        invoice_format = "CII / XRechnung"
    elif "Invoice" in root_name and "ubl" in namespace.lower():
        invoice_format = "UBL / XRechnung"
    else:
        invoice_format = "Unbekannte XML-Rechnung"

    return {
        "file_type": "xml",
        "format": invoice_format,
        "root": root_name,
        "namespace": namespace,
        "parser_status": "erkannt",
    }


def text_or_none(tree, xpath, namespaces):
    result = tree.xpath(xpath, namespaces=namespaces)
    if not result:
        return None
    if hasattr(result[0], "text"):
        return result[0].text
    return str(result[0])


def extract_basic_invoice_data(filepath: str) -> dict:
    path = Path(filepath)

    if path.suffix.lower() != ".xml":
        return {}

    tree = etree.parse(str(path))
    root = tree.getroot()
    namespace = etree.QName(root).namespace or ""

    if "ubl" in namespace.lower():
        ns = {
            "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
            "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
        }

        return {
            "invoice_number": text_or_none(tree, "//cbc:ID", ns),
            "invoice_date": text_or_none(tree, "//cbc:IssueDate", ns),
            "currency": text_or_none(tree, "//cbc:DocumentCurrencyCode", ns),
            "supplier": text_or_none(tree, "//cac:AccountingSupplierParty//cac:PartyName//cbc:Name", ns),
            "customer": text_or_none(tree, "//cac:AccountingCustomerParty//cac:PartyName//cbc:Name", ns),
            "net_amount": text_or_none(tree, "//cac:LegalMonetaryTotal//cbc:TaxExclusiveAmount", ns),
            "gross_amount": text_or_none(tree, "//cac:LegalMonetaryTotal//cbc:TaxInclusiveAmount", ns),
            "payable_amount": text_or_none(tree, "//cac:LegalMonetaryTotal//cbc:PayableAmount", ns),
        }

    ns = {
        "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
        "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
        "udt": "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100",
    }

    return {
        "invoice_number": text_or_none(tree, "//rsm:ExchangedDocument/ram:ID", ns),
        "invoice_date": text_or_none(tree, "//rsm:ExchangedDocument/ram:IssueDateTime/udt:DateTimeString", ns),
        "currency": text_or_none(tree, "//ram:InvoiceCurrencyCode", ns),
        "supplier": text_or_none(tree, "//ram:SellerTradeParty/ram:Name", ns),
        "customer": text_or_none(tree, "//ram:BuyerTradeParty/ram:Name", ns),
        "net_amount": text_or_none(tree, "//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:TaxBasisTotalAmount", ns),
        "gross_amount": text_or_none(tree, "//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:GrandTotalAmount", ns),
        "payable_amount": text_or_none(tree, "//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:DuePayableAmount", ns),
    }


def extract_invoice_lines(filepath: str) -> list:
    path = Path(filepath)

    if path.suffix.lower() != ".xml":
        return []

    tree = etree.parse(str(path))
    root = tree.getroot()
    namespace = etree.QName(root).namespace or ""

    if "ubl" in namespace.lower():
        ns = {
            "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
            "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
        }

        lines = []

        for line in tree.xpath("//cac:InvoiceLine", namespaces=ns):
            lines.append({
                "description": text_or_none(line, ".//cac:Item//cbc:Name", ns),
                "quantity": text_or_none(line, ".//cbc:InvoicedQuantity", ns),
                "unit_price": text_or_none(line, ".//cac:Price//cbc:PriceAmount", ns),
                "line_total": text_or_none(line, ".//cbc:LineExtensionAmount", ns),
            })

        return lines

    ns = {
        "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
        "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
        "udt": "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100",
    }

    lines = []

    for line in tree.xpath("//ram:IncludedSupplyChainTradeLineItem", namespaces=ns):
        lines.append({
            "description": text_or_none(line, ".//ram:SpecifiedTradeProduct/ram:Name", ns),
            "quantity": text_or_none(line, ".//ram:BilledQuantity", ns),
            "unit_price": text_or_none(line, ".//ram:NetPriceProductTradePrice/ram:ChargeAmount", ns),
            "line_total": text_or_none(line, ".//ram:SpecifiedTradeSettlementLineMonetarySummation/ram:LineTotalAmount", ns),
        })

    return lines


def process_invoice_file(filepath: str) -> dict:
    xml_path, xml_meta = resolve_xml_source(filepath)
    detected = detect_invoice_format(filepath, xml_path, xml_meta)

    if xml_path:
        invoice_data = extract_basic_invoice_data(xml_path)
        invoice_lines = extract_invoice_lines(xml_path)
        with open(xml_path, encoding="utf-8") as handle:
            xml_content = handle.read()
    else:
        invoice_data = {}
        invoice_lines = []
        xml_content = None

    return {
        "detected": detected,
        "invoice": invoice_data,
        "lines": invoice_lines,
        "xml_content": xml_content,
        "xml_meta": xml_meta,
    }
