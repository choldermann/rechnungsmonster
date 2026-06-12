import { useState } from "react";
import axios from "axios";
import Dropzone from "./Dropzone";
import InfoAccordions from "./InfoAccordions";
import SiteHeader from "./SiteHeader";
import SiteFooter from "./SiteFooter";
import ValidationPanel from "./ValidationPanel";
import ReportPanel from "./ReportPanel";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "";

function App() {
  const [file, setFile] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);

  function handleFileSelect(selectedFile, message) {
    setFile(selectedFile);
    setError(message);
    if (selectedFile) {
      setUploadResult(null);
    }
  }

  function handleReset() {
    setFile(null);
    setUploadResult(null);
    setError("");
  }

  async function handleUpload() {
    if (!file) {
      setError("Bitte zuerst eine Datei auswählen.");
      return;
    }

    setError("");
    setUploadResult(null);
    setUploading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(`${API_URL}/api/upload`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setUploadResult(response.data);
    } catch (err) {
      setError("Prüfung fehlgeschlagen. Bitte später erneut versuchen.");
      console.error(err);
    } finally {
      setUploading(false);
    }
  }

  return (
    <>
      <SiteHeader />
      <div className={`page${uploadResult ? " page--results" : ""}`}>
        <div className="card">
          <header className="hero">
            <div className="hero-badge">Kostenlos · Anonym · Keine Speicherung</div>
            <h1>
              E-Rechnungen prüfen –{" "}
              <em>schnell und ohne Anmeldung.</em>
            </h1>
            <p className="subtitle">
              XRechnung, UBL, CII und ZUGFeRD/Factur-X – mit offiziellem KoSIT-Validator
              und erweiterten Zusatzprüfungen.
            </p>
          <div className="format-tags" aria-label="Unterstützte Formate">
            <span className="format-tag">XRechnung</span>
            <span className="format-tag">ZUGFeRD</span>
            <span className="format-tag">Factur-X</span>
            <span className="format-tag">PDF &amp; XML</span>
          </div>
        </header>

        <div className="privacy-note">
          Ihre Datei wird nur zur Prüfung verarbeitet und danach sofort gelöscht.
          Es werden keine Rechnungsdaten gespeichert.
        </div>

        {!uploadResult && <InfoAccordions />}

        <section id="upload" className="upload-section" aria-label="Datei hochladen">
          <Dropzone
            file={file}
            onFileSelect={handleFileSelect}
            disabled={uploading}
          />

          <button
            className="upload-btn"
            onClick={handleUpload}
            disabled={uploading || !file}
          >
            {uploading ? (
              <>
                <span className="upload-btn-spinner" aria-hidden="true" />
                Wird geprüft…
              </>
            ) : (
              "Rechnung prüfen"
            )}
          </button>
        </section>

        {error && <div className="error">{error}</div>}

        {uploadResult && (
          <div className="result">
            <div className="result-header">
              <h2>Prüfung abgeschlossen</h2>
              <button className="reset-btn" onClick={handleReset}>
                Neue Prüfung
              </button>
            </div>

            <p>
              <strong>Dateiname:</strong> {uploadResult.original_filename}
            </p>

            {uploadResult.detected && (
              <>
                <h3>Erkanntes Format</h3>

                <p>
                  <strong>Dateityp:</strong> {uploadResult.detected.file_type}
                </p>

                <p>
                  <strong>Format:</strong> {uploadResult.detected.format}
                </p>

                <p>
                  <strong>Status:</strong> {uploadResult.detected.parser_status}
                </p>

                {uploadResult.detected.embedded_attachment && (
                  <p>
                    <strong>PDF-Anhang:</strong>{" "}
                    {uploadResult.detected.embedded_attachment}
                  </p>
                )}
              </>
            )}

            {uploadResult.validation && (
              <ValidationPanel validation={uploadResult.validation} />
            )}

            <ReportPanel uploadResult={uploadResult} />

            {uploadResult.invoice &&
              Object.keys(uploadResult.invoice).length > 0 && (
                <>
                  <h3>Rechnungsdaten</h3>

                  <p>
                    <strong>Rechnungsnummer:</strong>{" "}
                    {uploadResult.invoice.invoice_number || "-"}
                  </p>

                  <p>
                    <strong>Datum:</strong>{" "}
                    {uploadResult.invoice.invoice_date || "-"}
                  </p>

                  <p>
                    <strong>Währung:</strong>{" "}
                    {uploadResult.invoice.currency || "-"}
                  </p>

                  <p>
                    <strong>Lieferant:</strong>{" "}
                    {uploadResult.invoice.supplier || "-"}
                  </p>

                  <p>
                    <strong>Kunde:</strong>{" "}
                    {uploadResult.invoice.customer || "-"}
                  </p>

                  <p>
                    <strong>Netto:</strong>{" "}
                    {uploadResult.invoice.net_amount || "-"}
                  </p>

                  <p>
                    <strong>Brutto:</strong>{" "}
                    {uploadResult.invoice.gross_amount || "-"}
                  </p>

                  <p>
                    <strong>Zahlbetrag:</strong>{" "}
                    {uploadResult.invoice.payable_amount || "-"}
                  </p>
                </>
              )}

            {uploadResult.lines && uploadResult.lines.length > 0 && (
              <>
                <h3>Positionen</h3>

                <table className="lines-table">
                  <thead>
                    <tr>
                      <th>Beschreibung</th>
                      <th>Menge</th>
                      <th>Einzelpreis</th>
                      <th>Gesamt</th>
                    </tr>
                  </thead>

                  <tbody>
                    {uploadResult.lines.map((line, index) => (
                      <tr key={index}>
                        <td>{line.description || "-"}</td>
                        <td>{line.quantity || "-"}</td>
                        <td>{line.unit_price || "-"}</td>
                        <td>{line.line_total || "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}
          </div>
        )}
        </div>
      </div>
      <SiteFooter />
    </>
  );
}

export default App;
