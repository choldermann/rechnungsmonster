from io import BytesIO

from lxml import etree

from app.issue_builder import build_issue
from app.validation_humanize import get_line_content

CII_NS = {
    "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
    "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
}

UBL_NS = {
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
}


def _payment_xpath_cii() -> str:
    return (
        "/rsm:CrossIndustryInvoice[1]\n"
        "/rsm:SupplyChainTradeTransaction[1]\n"
        "/ram:ApplicableHeaderTradeSettlement[1]\n"
        "/ram:SpecifiedTradeSettlementPaymentMeans[1]"
    )


def _check_br_co_27_cii(tree, xml_content: str) -> list[dict]:
    issues = []
    for payment in tree.xpath("//ram:SpecifiedTradeSettlementPaymentMeans", namespaces=CII_NS):
        iban = payment.xpath(
            "string(.//ram:PayeePartyCreditorFinancialAccount/ram:IBANID)",
            namespaces=CII_NS,
        ).strip()
        proprietary = payment.xpath(
            "string(.//ram:PayeePartyCreditorFinancialAccount/ram:ProprietaryID)",
            namespaces=CII_NS,
        ).strip()
        if not iban or not proprietary:
            continue

        line = str(payment.sourceline) if payment.sourceline else None
        description = (
            "[BR-CO-27]-Für BT-84 ist entweder die IBAN oder eine proprietäre ID zu verwenden. "
            "Es dürfen nicht beide Angaben gleichzeitig gemacht werden."
        )
        issues.append(
            build_issue(
                level="error",
                category="Formatfehler",
                rule_code="BR-CO-27",
                description=description,
                text=(
                    "Für das Zahlungskonto (BT-84) dürfen IBAN und nationale Kontonummer "
                    "nicht gleichzeitig angegeben werden."
                ),
                location="Zahlungsart → Zahlungskonto",
                line=line,
                column="13",
                line_content=get_line_content(xml_content, line, None),
                xpath_path=_payment_xpath_cii(),
                step_id="xml-rules",
                source="xml-rules",
            )
        )
    return issues


def _check_br_co_27_ubl(tree, xml_content: str) -> list[dict]:
    issues = []
    for payment in tree.xpath("//cac:PaymentMeans", namespaces=UBL_NS):
        iban = payment.xpath("string(.//cac:PayeeFinancialAccount/cbc:ID)", namespaces=UBL_NS).strip()
        name = payment.xpath("string(.//cac:PayeeFinancialAccount/cbc:Name)", namespaces=UBL_NS).strip()
        if iban and name and iban != name:
            continue
        if not iban:
            continue

        proprietary = payment.xpath(
            "string(.//cac:PayeeFinancialAccount/cac:FinancialInstitutionBranch/cbc:ID)",
            namespaces=UBL_NS,
        ).strip()
        if iban and proprietary and iban != proprietary:
            line = str(payment.sourceline) if payment.sourceline else None
            description = (
                "[BR-CO-27]-Für BT-84 ist entweder die IBAN oder eine proprietäre ID zu verwenden. "
                "Es dürfen nicht beide Angaben gleichzeitig gemacht werden."
            )
            issues.append(
                build_issue(
                    level="error",
                    category="Formatfehler",
                    rule_code="BR-CO-27",
                    description=description,
                    text=(
                        "Für das Zahlungskonto (BT-84) dürfen IBAN und proprietäre Kennung "
                        "nicht gleichzeitig angegeben werden."
                    ),
                    location="Zahlungsart",
                    line=line,
                    line_content=get_line_content(xml_content, line, None),
                    step_id="xml-rules",
                    source="xml-rules",
                )
            )
    return issues


def validate_xml_rules(xml_content: str) -> list[dict]:
    if not xml_content:
        return []

    try:
        tree = etree.parse(BytesIO(xml_content.encode("utf-8")))
    except etree.XMLSyntaxError:
        return []

    root_name = etree.QName(tree.getroot()).localname
    issues: list[dict] = []

    if root_name == "CrossIndustryInvoice":
        issues.extend(_check_br_co_27_cii(tree, xml_content))
    elif root_name == "Invoice":
        issues.extend(_check_br_co_27_ubl(tree, xml_content))

    return issues
