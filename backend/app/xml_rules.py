from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
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

_TOLERANCE = Decimal("0.02")


def _to_dec(s: str) -> Decimal | None:
    if not s or not s.strip():
        return None
    try:
        return Decimal(s.strip())
    except InvalidOperation:
        return None


def _r2(d: Decimal) -> Decimal:
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _arith_issue(rule_code: str, description: str, text: str, location: str,
                 line: str | None, xml_content: str) -> dict:
    return build_issue(
        level="error",
        category="Arithmetik",
        rule_code=rule_code,
        description=description,
        text=text,
        location=location,
        line=line,
        line_content=get_line_content(xml_content, line, None) if line else None,
        step_id="xml-rules",
        source="xml-rules",
    )


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


def _check_arithmetic_cii(tree, xml_content: str) -> list[dict]:
    issues = []
    line_totals_sum = Decimal("0")

    for idx, line in enumerate(
        tree.xpath("//ram:IncludedSupplyChainTradeLineItem", namespaces=CII_NS), start=1
    ):
        qty = _to_dec(line.xpath("string(.//ram:BilledQuantity)", namespaces=CII_NS))
        price = _to_dec(line.xpath("string(.//ram:NetPriceProductTradePrice/ram:ChargeAmount)", namespaces=CII_NS))
        basis_raw = _to_dec(line.xpath("string(.//ram:NetPriceProductTradePrice/ram:BasisQuantity)", namespaces=CII_NS))
        basis = basis_raw if basis_raw and basis_raw != 0 else Decimal("1")
        line_total = _to_dec(line.xpath("string(.//ram:LineTotalAmount)", namespaces=CII_NS))
        src = str(line.sourceline) if line.sourceline else None

        if line_total is not None:
            line_totals_sum += line_total

        if qty is not None and price is not None and line_total is not None:
            expected = _r2(qty * price / basis)
            actual = _r2(line_total)
            if abs(expected - actual) > _TOLERANCE:
                issues.append(_arith_issue(
                    "RM-ARITH-LINE",
                    f"[RM-ARITH]-Position {idx}: BT-131 LineTotalAmount={actual} "
                    f"stimmt nicht mit BT-129 BilledQuantity × BT-146 ChargeAmount / BasisQuantity "
                    f"({qty} × {price} / {basis} = {expected}) überein.",
                    f"Position {idx}: LineTotalAmount {actual} ≠ erwartet {expected} "
                    f"(BilledQuantity {qty} × ChargeAmount {price} / BasisQuantity {basis}).",
                    f"Position {idx} / ram:LineTotalAmount", src, xml_content,
                ))

    for tax in tree.xpath("//ram:ApplicableTradeTax", namespaces=CII_NS):
        basis = _to_dec(tax.xpath("string(ram:BasisAmount)", namespaces=CII_NS))
        rate = _to_dec(tax.xpath("string(ram:RateApplicablePercent)", namespaces=CII_NS))
        calc = _to_dec(tax.xpath("string(ram:CalculatedAmount)", namespaces=CII_NS))
        src = str(tax.sourceline) if tax.sourceline else None

        if basis is not None and rate is not None and calc is not None:
            expected = _r2(basis * rate / Decimal("100"))
            actual = _r2(calc)
            if abs(expected - actual) > _TOLERANCE:
                issues.append(_arith_issue(
                    "RM-ARITH-TAX",
                    f"[RM-ARITH]-Steuer: BT-117 CalculatedAmount={actual} stimmt nicht mit "
                    f"BT-116 BasisAmount × BT-119 RateApplicablePercent / 100 "
                    f"({basis} × {rate}% / 100 = {expected}) überein.",
                    f"CalculatedAmount {actual} ≠ erwartet {expected} "
                    f"(BasisAmount {basis} × {rate}% / 100).",
                    "ram:ApplicableTradeTax / ram:CalculatedAmount", src, xml_content,
                ))

    summation = tree.xpath(
        "//ram:SpecifiedTradeSettlementHeaderMonetarySummation", namespaces=CII_NS
    )
    if summation:
        s = summation[0]
        line_hdr = _to_dec(s.xpath("string(ram:LineTotalAmount)", namespaces=CII_NS))
        tax_basis = _to_dec(s.xpath("string(ram:TaxBasisTotalAmount)", namespaces=CII_NS))
        tax_total = _to_dec(s.xpath("string(ram:TaxTotalAmount)", namespaces=CII_NS))
        grand = _to_dec(s.xpath("string(ram:GrandTotalAmount)", namespaces=CII_NS))
        prepaid = _to_dec(s.xpath("string(ram:TotalPrepaidAmount)", namespaces=CII_NS)) or Decimal("0")
        due = _to_dec(s.xpath("string(ram:DuePayableAmount)", namespaces=CII_NS))

        if line_hdr is not None and line_totals_sum:
            exp = _r2(line_totals_sum)
            act = _r2(line_hdr)
            if abs(exp - act) > _TOLERANCE:
                issues.append(_arith_issue(
                    "RM-ARITH-LINESUM",
                    f"[RM-ARITH]-BT-106 LineTotalAmount={act} stimmt nicht mit der "
                    f"Summe aller BT-131 LineTotalAmount der Positionen ({exp}) überein.",
                    f"LineTotalAmount {act} ≠ Summe der Positionsbeträge {exp}.",
                    "ram:SpecifiedTradeSettlementHeaderMonetarySummation / ram:LineTotalAmount",
                    None, xml_content,
                ))

        if tax_basis is not None and tax_total is not None and grand is not None:
            expected = _r2(tax_basis + tax_total)
            actual = _r2(grand)
            if abs(expected - actual) > _TOLERANCE:
                issues.append(_arith_issue(
                    "RM-ARITH-GRAND",
                    f"[RM-ARITH]-BT-112 GrandTotalAmount={actual} stimmt nicht mit "
                    f"BT-109 TaxBasisTotalAmount + BT-110 TaxTotalAmount "
                    f"({_r2(tax_basis)} + {_r2(tax_total)} = {expected}) überein.",
                    f"GrandTotalAmount {actual} ≠ erwartet {expected} "
                    f"(TaxBasisTotalAmount {_r2(tax_basis)} + TaxTotalAmount {_r2(tax_total)}).",
                    "ram:SpecifiedTradeSettlementHeaderMonetarySummation / ram:GrandTotalAmount",
                    None, xml_content,
                ))

        if grand is not None and due is not None:
            expected = _r2(grand - prepaid)
            actual = _r2(due)
            if abs(expected - actual) > _TOLERANCE:
                issues.append(_arith_issue(
                    "RM-ARITH-DUE",
                    f"[RM-ARITH]-BT-115 DuePayableAmount={actual} stimmt nicht mit "
                    f"BT-112 GrandTotalAmount - BT-113 TotalPrepaidAmount "
                    f"({_r2(grand)} - {_r2(prepaid)} = {expected}) überein.",
                    f"DuePayableAmount {actual} ≠ erwartet {expected} "
                    f"(GrandTotalAmount {_r2(grand)} - TotalPrepaidAmount {_r2(prepaid)}).",
                    "ram:SpecifiedTradeSettlementHeaderMonetarySummation / ram:DuePayableAmount",
                    None, xml_content,
                ))

    return issues


def _check_arithmetic_ubl(tree, xml_content: str) -> list[dict]:
    issues = []
    line_totals_sum = Decimal("0")

    for idx, line in enumerate(
        tree.xpath("//cac:InvoiceLine", namespaces=UBL_NS), start=1
    ):
        qty = _to_dec(line.xpath("string(cbc:InvoicedQuantity)", namespaces=UBL_NS))
        price = _to_dec(line.xpath("string(cac:Price/cbc:PriceAmount)", namespaces=UBL_NS))
        basis_raw = _to_dec(line.xpath("string(cac:Price/cbc:BaseQuantity)", namespaces=UBL_NS))
        basis = basis_raw if basis_raw and basis_raw != 0 else Decimal("1")
        line_total = _to_dec(line.xpath("string(cbc:LineExtensionAmount)", namespaces=UBL_NS))
        src = str(line.sourceline) if line.sourceline else None

        if line_total is not None:
            line_totals_sum += line_total

        if qty is not None and price is not None and line_total is not None:
            expected = _r2(qty * price / basis)
            actual = _r2(line_total)
            if abs(expected - actual) > _TOLERANCE:
                issues.append(_arith_issue(
                    "RM-ARITH-LINE",
                    f"[RM-ARITH]-Position {idx}: BT-131 LineExtensionAmount={actual} "
                    f"stimmt nicht mit BT-129 InvoicedQuantity × BT-146 PriceAmount / BaseQuantity "
                    f"({qty} × {price} / {basis} = {expected}) überein.",
                    f"Position {idx}: LineExtensionAmount {actual} ≠ erwartet {expected} "
                    f"(InvoicedQuantity {qty} × PriceAmount {price} / BaseQuantity {basis}).",
                    f"InvoiceLine {idx} / cbc:LineExtensionAmount", src, xml_content,
                ))

    for subtotal in tree.xpath("//cac:TaxTotal/cac:TaxSubtotal", namespaces=UBL_NS):
        basis = _to_dec(subtotal.xpath("string(cac:TaxableAmount)", namespaces=UBL_NS))
        rate = _to_dec(subtotal.xpath("string(cac:TaxCategory/cbc:Percent)", namespaces=UBL_NS))
        tax = _to_dec(subtotal.xpath("string(cac:TaxAmount)", namespaces=UBL_NS))
        src = str(subtotal.sourceline) if subtotal.sourceline else None

        if basis is not None and rate is not None and tax is not None:
            expected = _r2(basis * rate / Decimal("100"))
            actual = _r2(tax)
            if abs(expected - actual) > _TOLERANCE:
                issues.append(_arith_issue(
                    "RM-ARITH-TAX",
                    f"[RM-ARITH]-Steuer: BT-117 TaxAmount={actual} stimmt nicht mit "
                    f"BT-116 TaxableAmount × BT-119 Percent / 100 "
                    f"({_r2(basis)} × {rate}% / 100 = {expected}) überein.",
                    f"TaxAmount {actual} ≠ erwartet {expected} "
                    f"(TaxableAmount {_r2(basis)} × {rate}% / 100).",
                    "TaxSubtotal / cac:TaxAmount", src, xml_content,
                ))

    monetary = tree.xpath("//cac:LegalMonetaryTotal", namespaces=UBL_NS)
    if monetary:
        m = monetary[0]
        line_hdr = _to_dec(m.xpath("string(cbc:LineExtensionAmount)", namespaces=UBL_NS))
        net = _to_dec(m.xpath("string(cbc:TaxExclusiveAmount)", namespaces=UBL_NS))
        gross = _to_dec(m.xpath("string(cbc:TaxInclusiveAmount)", namespaces=UBL_NS))
        prepaid = _to_dec(m.xpath("string(cbc:PrepaidAmount)", namespaces=UBL_NS)) or Decimal("0")
        payable = _to_dec(m.xpath("string(cbc:PayableAmount)", namespaces=UBL_NS))

        tax_amount_els = tree.xpath("//cac:TaxTotal/cbc:TaxAmount", namespaces=UBL_NS)
        tax_total = _to_dec(tax_amount_els[0].text or "") if tax_amount_els else None

        if line_hdr is not None and line_totals_sum:
            exp = _r2(line_totals_sum)
            act = _r2(line_hdr)
            if abs(exp - act) > _TOLERANCE:
                issues.append(_arith_issue(
                    "RM-ARITH-LINESUM",
                    f"[RM-ARITH]-BT-106 LineExtensionAmount={act} stimmt nicht mit der "
                    f"Summe aller BT-131 LineExtensionAmount der Positionen ({exp}) überein.",
                    f"LineExtensionAmount {act} ≠ Summe der Positionsbeträge {exp}.",
                    "LegalMonetaryTotal / cbc:LineExtensionAmount", None, xml_content,
                ))

        if net is not None and tax_total is not None and gross is not None:
            expected = _r2(net + tax_total)
            actual = _r2(gross)
            if abs(expected - actual) > _TOLERANCE:
                issues.append(_arith_issue(
                    "RM-ARITH-GRAND",
                    f"[RM-ARITH]-BT-112 TaxInclusiveAmount={actual} stimmt nicht mit "
                    f"BT-109 TaxExclusiveAmount + BT-110 TaxAmount "
                    f"({_r2(net)} + {_r2(tax_total)} = {expected}) überein.",
                    f"TaxInclusiveAmount {actual} ≠ erwartet {expected} "
                    f"(TaxExclusiveAmount {_r2(net)} + TaxAmount {_r2(tax_total)}).",
                    "LegalMonetaryTotal / cbc:TaxInclusiveAmount", None, xml_content,
                ))

        if gross is not None and payable is not None:
            expected = _r2(gross - prepaid)
            actual = _r2(payable)
            if abs(expected - actual) > _TOLERANCE:
                issues.append(_arith_issue(
                    "RM-ARITH-DUE",
                    f"[RM-ARITH]-BT-115 PayableAmount={actual} stimmt nicht mit "
                    f"BT-112 TaxInclusiveAmount - BT-113 PrepaidAmount "
                    f"({_r2(gross)} - {_r2(prepaid)} = {expected}) überein.",
                    f"PayableAmount {actual} ≠ erwartet {expected} "
                    f"(TaxInclusiveAmount {_r2(gross)} - PrepaidAmount {_r2(prepaid)}).",
                    "LegalMonetaryTotal / cbc:PayableAmount", None, xml_content,
                ))

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
        issues.extend(_check_arithmetic_cii(tree, xml_content))
    elif root_name == "Invoice":
        issues.extend(_check_br_co_27_ubl(tree, xml_content))
        issues.extend(_check_arithmetic_ubl(tree, xml_content))

    return issues
