from pathlib import Path

import pikepdf

XML_HINTS = ("factur", "zugferd", "xrechnung", "order-xrechnung", "cii", "invoice")


def _looks_like_invoice_xml(data: bytes) -> bool:
    sample = data[:8192].lower()
    if b"<?xml" not in sample and not sample.lstrip().startswith(b"<"):
        return False

    markers = (
        b"crossindustryinvoice",
        b"ubl:invoice",
        b"<invoice ",
        b"urn:cen.eu:en16931",
        b"xeinkauf.de:kosit:xrechnung",
        b":invoice>",
    )
    return any(marker in sample for marker in markers)


def _decode_xml(data: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _read_stream_bytes(stream) -> bytes | None:
    if stream is None:
        return None
    try:
        return stream.read_bytes()
    except AttributeError:
        try:
            return bytes(stream.get_buffer())
        except Exception:
            return None


def _read_embedded_stream(filespec) -> bytes | None:
    try:
        embedded = filespec["/EF"]["/F"]
    except (KeyError, TypeError, AttributeError):
        return None
    return _read_stream_bytes(embedded)


def _candidate_names(*values) -> list[str]:
    names = []
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            names.append(text)
    return names


def _name_matches_invoice_xml(names: list[str]) -> bool:
    for name in names:
        lower = name.lower()
        if lower.endswith(".xml"):
            return True
        if any(hint in lower for hint in XML_HINTS):
            return True
    return False


def _try_extract(data: bytes | None, names: list[str]) -> tuple[str, str] | None:
    if not data:
        return None
    if not _looks_like_invoice_xml(data):
        return None
    label = next((name for name in names if name), "embedded.xml")
    return _decode_xml(data), label


def extract_xml_from_pdf(filepath: str) -> tuple[str | None, str | None]:
    path = Path(filepath)

    with pikepdf.open(path) as pdf:
        for name, spec in pdf.attachments.items():
            names = _candidate_names(name, getattr(spec, "filename", None))
            try:
                data = spec.get_file().read_bytes()
            except Exception:
                data = None
            result = _try_extract(data, names)
            if result:
                return result

        if "/AF" in pdf.Root:
            for filespec in pdf.Root.AF:
                names = _candidate_names(
                    filespec.get("/UF"),
                    filespec.get("/F"),
                    filespec.get("/Desc"),
                )
                if names and not _name_matches_invoice_xml(names):
                    subtype = None
                    try:
                        subtype = str(filespec["/EF"]["/F"]["/Subtype"])
                    except Exception:
                        subtype = None
                    if subtype and "xml" not in subtype.lower():
                        continue

                result = _try_extract(_read_embedded_stream(filespec), names)
                if result:
                    return result

        if "/Names" in pdf.Root and "/EmbeddedFiles" in pdf.Root.Names:
            names_array = pdf.Root.Names.EmbeddedFiles.get("/Names")
            if names_array:
                for index in range(0, len(names_array), 2):
                    label = str(names_array[index])
                    filespec = names_array[index + 1]
                    names = _candidate_names(
                        label,
                        filespec.get("/UF"),
                        filespec.get("/F"),
                    )
                    if names and not _name_matches_invoice_xml(names):
                        continue
                    result = _try_extract(_read_embedded_stream(filespec), names)
                    if result:
                        return result

    return None, None
