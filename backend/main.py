import base64
import os
import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from app.extended_validation import merge_validation
from app.parser import process_invoice_file
from app.report_pdf import generate_report_pdf
from app.validator import validate_invoice_xml

app = FastAPI(title="Rechnungsmonster API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def sanitize_validation(validation: dict | None) -> dict | None:
    if not validation:
        return None

    return {
        "available": validation.get("available"),
        "valid": validation.get("valid"),
        "summary": validation.get("summary"),
        "error": validation.get("error"),
    }


@app.get("/")
def root():
    return {"app": "Rechnungsmonster", "status": "running", "storage": "none"}


@app.get("/api/version")
def version():
    return {
        "kosit_xrechnung": os.getenv("KOSIT_XRECHNUNG_VERSION", "3.0.2"),
        "kosit_validator": os.getenv("KOSIT_VALIDATOR_VERSION", "1.6.2"),
        "verapdf": os.getenv("VERAPDF_VERSION", "1.30.2"),
    }


@app.post("/api/upload")
async def upload_invoice(file: UploadFile = File(...)):
    original_filename = Path(file.filename or "upload").name

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / original_filename

        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        parsed = process_invoice_file(str(filepath))
        validation = None
        if parsed["xml_content"]:
            validation = validate_invoice_xml(
                parsed["xml_content"],
                filename=f"{original_filename}.xml",
            )
            validation = merge_validation(
                validation,
                xml_content=parsed["xml_content"],
                filepath=str(filepath),
                is_pdf=parsed["detected"].get("file_type") == "pdf",
            )

        report_pdf = generate_report_pdf(
            original_filename=original_filename,
            detected=parsed["detected"],
            invoice=parsed["invoice"],
            lines=parsed["lines"],
            validation=validation,
            xml_content=parsed.get("xml_content"),
        )

    return {
        "original_filename": original_filename,
        "content_type": file.content_type,
        "status": "checked",
        "detected": parsed["detected"],
        "invoice": parsed["invoice"],
        "lines": parsed["lines"],
        "validation": sanitize_validation(validation),
        "report_pdf": base64.b64encode(report_pdf).decode("ascii"),
    }
