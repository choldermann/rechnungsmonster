from io import BytesIO
from lxml import etree

CII_NS = {
    "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
    "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
    "udt": "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100",
}
UBL_NS = {
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
}

# Each entry: (bt, label, xpath_cii, xpath_ubl)
# xpath returning a list means repeated elements (tax lines etc.)
_CATEGORIES = [
    {
        "title": "Rechnungskopf",
        "fields": [
            ("BT-1",  "Rechnungsnummer",
             "string(//rsm:ExchangedDocument/ram:ID)",
             "string(//cbc:ID)"),
            ("BT-2",  "Rechnungsdatum",
             "string(//rsm:ExchangedDocument/ram:IssueDateTime/udt:DateTimeString)",
             "string(//cbc:IssueDate)"),
            ("BT-3",  "Rechnungsart (Code)",
             "string(//rsm:ExchangedDocument/ram:TypeCode)",
             "string(//cbc:InvoiceTypeCode)"),
            ("BT-5",  "Währung",
             "string(//ram:InvoiceCurrencyCode)",
             "string(//cbc:DocumentCurrencyCode)"),
            ("BT-9",  "Fälligkeitsdatum",
             "string(//ram:SpecifiedTradePaymentTerms/ram:DueDateDateTime/udt:DateTimeString)",
             "string(//cac:PaymentMeans/cbc:PaymentDueDate)"),
            ("BT-10", "Käuferreferenz",
             "string(//ram:BuyerReference)",
             "string(//cbc:BuyerReference)"),
            ("BT-11", "Projektreferenz",
             "string(//ram:SpecifiedHeaderTradeAgreement/ram:SpecifiedProcuringProject/ram:ID)",
             "string(//cac:ProjectReference/cbc:ID)"),
            ("BT-12", "Vertragsreferenz",
             "string(//ram:SpecifiedHeaderTradeAgreement/ram:ContractReferencedDocument/ram:IssuerAssignedID)",
             "string(//cac:ContractDocumentReference/cbc:ID)"),
            ("BT-13", "Bestellnummer (Käufer)",
             "string(//ram:SpecifiedHeaderTradeAgreement/ram:BuyerOrderReferencedDocument/ram:IssuerAssignedID)",
             "string(//cac:OrderReference/cbc:ID)"),
            ("BT-14", "Auftragsnummer (Verkäufer)",
             "string(//ram:SpecifiedHeaderTradeAgreement/ram:SellerOrderReferencedDocument/ram:IssuerAssignedID)",
             "string(//cac:OrderReference/cbc:SalesOrderID)"),
            ("BT-19", "Kostenstelle / Buchungsreferenz",
             "string(//ram:ReceivableSpecifiedTradeAccountingAccount/ram:ID)",
             "string(//cbc:AccountingCost)"),
            ("BT-20", "Zahlungsbedingungen",
             "string(//ram:SpecifiedTradePaymentTerms/ram:Description)",
             "string(//cac:PaymentTerms/cbc:Note)"),
        ],
    },
    {
        "title": "Verkäufer",
        "fields": [
            ("BT-27", "Name",
             "string(//ram:SellerTradeParty/ram:Name)",
             "string(//cac:AccountingSupplierParty//cac:PartyName/cbc:Name)"),
            ("BT-28", "Handelsname",
             "string(//ram:SellerTradeParty/ram:SpecifiedLegalOrganization/ram:TradingBusinessName)",
             "string(//cac:AccountingSupplierParty//cac:PartyName/cbc:Name)"),
            ("BT-30", "Handelsregisternummer",
             "string(//ram:SellerTradeParty/ram:SpecifiedLegalOrganization/ram:ID)",
             "string(//cac:AccountingSupplierParty//cac:PartyLegalEntity/cbc:CompanyID)"),
            ("BT-31", "USt-IdNr.",
             "string(//ram:SellerTradeParty/ram:SpecifiedTaxRegistration[ram:ID/@schemeID='VA']/ram:ID)",
             "string(//cac:AccountingSupplierParty//cac:PartyTaxScheme[cac:TaxScheme/cbc:ID='VAT']/cbc:CompanyID)"),
            ("BT-32", "Steuernummer",
             "string(//ram:SellerTradeParty/ram:SpecifiedTaxRegistration[ram:ID/@schemeID='FC']/ram:ID)",
             "string(//cac:AccountingSupplierParty//cac:PartyTaxScheme[cac:TaxScheme/cbc:ID='FC']/cbc:CompanyID)"),
            ("BT-35", "Straße",
             "string(//ram:SellerTradeParty/ram:PostalTradeAddress/ram:LineOne)",
             "string(//cac:AccountingSupplierParty//cac:PostalAddress/cbc:StreetName)"),
            ("BT-36", "Adresszusatz",
             "string(//ram:SellerTradeParty/ram:PostalTradeAddress/ram:LineTwo)",
             "string(//cac:AccountingSupplierParty//cac:PostalAddress/cbc:AdditionalStreetName)"),
            ("BT-38", "Stadt",
             "string(//ram:SellerTradeParty/ram:PostalTradeAddress/ram:CityName)",
             "string(//cac:AccountingSupplierParty//cac:PostalAddress/cbc:CityName)"),
            ("BT-39", "PLZ",
             "string(//ram:SellerTradeParty/ram:PostalTradeAddress/ram:PostcodeCode)",
             "string(//cac:AccountingSupplierParty//cac:PostalAddress/cbc:PostalZone)"),
            ("BT-40", "Bundesland",
             "string(//ram:SellerTradeParty/ram:PostalTradeAddress/ram:CountrySubDivisionName)",
             "string(//cac:AccountingSupplierParty//cac:PostalAddress/cbc:CountrySubentity)"),
            ("BT-41", "Land",
             "string(//ram:SellerTradeParty/ram:PostalTradeAddress/ram:CountryID)",
             "string(//cac:AccountingSupplierParty//cac:PostalAddress/cac:Country/cbc:IdentificationCode)"),
            ("BT-42", "Ansprechpartner",
             "string(//ram:SellerTradeParty/ram:DefinedTradeContact/ram:PersonName)",
             "string(//cac:AccountingSupplierParty//cac:Contact/cbc:Name)"),
            ("BT-43", "Telefon",
             "string(//ram:SellerTradeParty/ram:DefinedTradeContact/ram:TelephoneUniversalCommunication/ram:CompleteNumber)",
             "string(//cac:AccountingSupplierParty//cac:Contact/cbc:Telephone)"),
            ("BT-44", "E-Mail",
             "string(//ram:SellerTradeParty/ram:DefinedTradeContact/ram:EmailURIUniversalCommunication/ram:URIID)",
             "string(//cac:AccountingSupplierParty//cac:Contact/cbc:ElectronicMail)"),
        ],
    },
    {
        "title": "Käufer",
        "fields": [
            ("BT-44", "Name",
             "string(//ram:BuyerTradeParty/ram:Name)",
             "string(//cac:AccountingCustomerParty//cac:PartyName/cbc:Name)"),
            ("BT-46", "Käufer-ID",
             "string(//ram:BuyerTradeParty/ram:ID)",
             "string(//cac:AccountingCustomerParty//cac:PartyIdentification/cbc:ID)"),
            ("BT-47", "Handelsregisternummer",
             "string(//ram:BuyerTradeParty/ram:SpecifiedLegalOrganization/ram:ID)",
             "string(//cac:AccountingCustomerParty//cac:PartyLegalEntity/cbc:CompanyID)"),
            ("BT-48", "USt-IdNr.",
             "string(//ram:BuyerTradeParty/ram:SpecifiedTaxRegistration[ram:ID/@schemeID='VA']/ram:ID)",
             "string(//cac:AccountingCustomerParty//cac:PartyTaxScheme[cac:TaxScheme/cbc:ID='VAT']/cbc:CompanyID)"),
            ("BT-50", "Straße",
             "string(//ram:BuyerTradeParty/ram:PostalTradeAddress/ram:LineOne)",
             "string(//cac:AccountingCustomerParty//cac:PostalAddress/cbc:StreetName)"),
            ("BT-51", "Adresszusatz",
             "string(//ram:BuyerTradeParty/ram:PostalTradeAddress/ram:LineTwo)",
             "string(//cac:AccountingCustomerParty//cac:PostalAddress/cbc:AdditionalStreetName)"),
            ("BT-52", "Stadt (Käufer)",
             "string(//ram:BuyerTradeParty/ram:PostalTradeAddress/ram:CityName)",
             "string(//cac:AccountingCustomerParty//cac:PostalAddress/cbc:CityName)"),
            ("BT-53", "PLZ (Käufer)",
             "string(//ram:BuyerTradeParty/ram:PostalTradeAddress/ram:PostcodeCode)",
             "string(//cac:AccountingCustomerParty//cac:PostalAddress/cbc:PostalZone)"),
            ("BT-55", "Land (Käufer)",
             "string(//ram:BuyerTradeParty/ram:PostalTradeAddress/ram:CountryID)",
             "string(//cac:AccountingCustomerParty//cac:PostalAddress/cac:Country/cbc:IdentificationCode)"),
        ],
    },
    {
        "title": "Zahlungsinformationen",
        "fields": [
            ("BT-81", "Zahlungsart (Code)",
             "string(//ram:SpecifiedTradeSettlementPaymentMeans/ram:TypeCode)",
             "string(//cac:PaymentMeans/cbc:PaymentMeansCode)"),
            ("BT-82", "Zahlungsart (Text)",
             "string(//ram:SpecifiedTradeSettlementPaymentMeans/ram:Information)",
             "string(//cac:PaymentMeans/cbc:InstructionNote)"),
            ("BT-83", "Verwendungszweck",
             "string(//ram:SpecifiedTradeSettlementPaymentMeans/ram:Information)",
             "string(//cac:PaymentMeans/cbc:PaymentID)"),
            ("BT-84", "IBAN",
             "string(//ram:PayeePartyCreditorFinancialAccount/ram:IBANID)",
             "string(//cac:PaymentMeans/cac:PayeeFinancialAccount/cbc:ID)"),
            ("BT-85", "Kontoname",
             "string(//ram:PayeePartyCreditorFinancialAccount/ram:AccountName)",
             "string(//cac:PaymentMeans/cac:PayeeFinancialAccount/cbc:Name)"),
            ("BT-86", "BIC",
             "string(//ram:PayeeSpecifiedCreditorFinancialInstitution/ram:BICID)",
             "string(//cac:PaymentMeans/cac:PayeeFinancialAccount/cac:FinancialInstitutionBranch/cbc:ID)"),
            ("BT-89", "Mandatsreferenz",
             "string(//ram:SpecifiedTradePaymentTerms/ram:DirectDebitMandateID)",
             "string(//cac:PaymentMeans/cac:PaymentMandate/cbc:ID)"),
            ("BT-90", "Gläubiger-ID",
             "string(//ram:CreditorReferenceID)",
             "string(//cac:PaymentMeans/cac:PaymentMandate/cac:PayerFinancialAccount/cbc:ID)"),
            ("BT-91", "Lastschrift-IBAN",
             "string(//ram:DebtorPartyDebtorFinancialAccount/ram:IBANID)",
             "string(//cac:PaymentMeans/cac:PaymentMandate/cac:PayerFinancialAccount/cbc:ID)"),
        ],
    },
    {
        "title": "Rechnungsbeträge",
        "fields": [
            ("BT-106", "Summe Nettopositionen",
             "string(//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:LineTotalAmount)",
             "string(//cac:LegalMonetaryTotal/cbc:LineExtensionAmount)"),
            ("BT-107", "Summe Abzüge",
             "string(//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:AllowanceTotalAmount)",
             "string(//cac:LegalMonetaryTotal/cbc:AllowanceTotalAmount)"),
            ("BT-108", "Summe Zuschläge",
             "string(//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:ChargeTotalAmount)",
             "string(//cac:LegalMonetaryTotal/cbc:ChargeTotalAmount)"),
            ("BT-109", "Nettobetrag (ohne USt)",
             "string(//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:TaxBasisTotalAmount)",
             "string(//cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount)"),
            ("BT-110", "Umsatzsteuerbetrag",
             "string(//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:TaxTotalAmount)",
             "string(//cac:TaxTotal/cbc:TaxAmount)"),
            ("BT-112", "Bruttobetrag (inkl. USt)",
             "string(//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:GrandTotalAmount)",
             "string(//cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount)"),
            ("BT-113", "Bereits bezahlt",
             "string(//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:TotalPrepaidAmount)",
             "string(//cac:LegalMonetaryTotal/cbc:PrepaidAmount)"),
            ("BT-114", "Rundungsbetrag",
             "string(//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:RoundingAmount)",
             "string(//cac:LegalMonetaryTotal/cbc:PayableRoundingAmount)"),
            ("BT-115", "Zahlbetrag",
             "string(//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:DuePayableAmount)",
             "string(//cac:LegalMonetaryTotal/cbc:PayableAmount)"),
        ],
    },
]

# Tax breakdown is handled separately (repeated elements)
_TAX_FIELDS_CII = [
    ("BT-116", "Bemessungsgrundlage", "ram:BasisAmount"),
    ("BT-117", "Steuerbetrag",        "ram:CalculatedAmount"),
    ("BT-118", "Steuerkategorie",     "ram:CategoryCode"),
    ("BT-119", "Steuersatz (%)",      "ram:RateApplicablePercent"),
    ("BT-120", "Befreiungsgrund",     "ram:ExemptionReason"),
]
_TAX_FIELDS_UBL = [
    ("BT-116", "Bemessungsgrundlage", "cac:TaxableAmount"),
    ("BT-117", "Steuerbetrag",        "cac:TaxAmount"),
    ("BT-118", "Steuerkategorie",     "cac:TaxCategory/cbc:ID"),
    ("BT-119", "Steuersatz (%)",      "cac:TaxCategory/cbc:Percent"),
    ("BT-120", "Befreiungsgrund",     "cac:TaxCategory/cbc:TaxExemptionReason"),
]


def _xval(tree, xpath: str, ns: dict) -> str:
    v = tree.xpath(xpath, namespaces=ns)
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, list) and v:
        el = v[0]
        return (el.text or "").strip() if hasattr(el, "text") else str(el).strip()
    return ""


def extract_bt_fields(xml_content: str) -> list[dict]:
    if not xml_content:
        return []

    try:
        tree = etree.parse(BytesIO(xml_content.encode("utf-8")))
    except etree.XMLSyntaxError:
        return []

    root_name = etree.QName(tree.getroot()).localname
    is_cii = root_name == "CrossIndustryInvoice"
    ns = CII_NS if is_cii else UBL_NS
    xpath_idx = 2 if is_cii else 3  # index into (bt, label, cii_xpath, ubl_xpath)

    result = []

    for category in _CATEGORIES:
        fields = []
        for entry in category["fields"]:
            bt, label, xpath_cii, xpath_ubl = entry
            xpath = xpath_cii if is_cii else xpath_ubl
            value = _xval(tree, xpath, ns)
            if value:
                fields.append({"bt": bt, "label": label, "value": value})
        if fields:
            result.append({"title": category["title"], "fields": fields})

    # Tax breakdown
    if is_cii:
        tax_nodes = tree.xpath("//ram:ApplicableTradeTax", namespaces=CII_NS)
        tax_fields_def = _TAX_FIELDS_CII
        tax_ns = CII_NS
    else:
        tax_nodes = tree.xpath("//cac:TaxTotal/cac:TaxSubtotal", namespaces=UBL_NS)
        tax_fields_def = _TAX_FIELDS_UBL
        tax_ns = UBL_NS

    if tax_nodes:
        tax_entries = []
        for idx, node in enumerate(tax_nodes, start=1):
            prefix = f"Steuerlinie {idx}: " if len(tax_nodes) > 1 else ""
            for bt, label, rel_xpath in tax_fields_def:
                value = node.xpath(f"string({rel_xpath})", namespaces=tax_ns).strip()
                if value:
                    tax_entries.append({
                        "bt": bt,
                        "label": f"{prefix}{label}",
                        "value": value,
                    })
        if tax_entries:
            result.append({"title": "Steuern", "fields": tax_entries})

    return result
