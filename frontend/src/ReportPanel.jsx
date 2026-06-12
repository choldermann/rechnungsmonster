import { useEffect, useState } from "react";
import { downloadReportPdf, reportPdfUrl } from "./report";

export default function ReportPanel({ uploadResult }) {
  const [previewUrl, setPreviewUrl] = useState(null);

  useEffect(() => {
    if (!uploadResult?.report_pdf) {
      setPreviewUrl(null);
      return undefined;
    }

    const url = reportPdfUrl(uploadResult.report_pdf);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [uploadResult?.report_pdf]);

  if (!uploadResult?.report_pdf) {
    return null;
  }

  const reportName = `Pruefbericht_${uploadResult.original_filename || "rechnung"}.pdf`
    .replace(/\.[^.]+$/, "")
    .concat(".pdf");

  return (
    <div className="report-panel">
      <div className="report-panel-header">
        <h3>Prüfbericht</h3>
        <button
          type="button"
          className="report-download-btn"
          onClick={() => downloadReportPdf(uploadResult.report_pdf, reportName)}
        >
          PDF herunterladen
        </button>
      </div>

      {previewUrl && (
        <iframe
          className="report-preview"
          src={previewUrl}
          title="Prüfbericht Vorschau"
        />
      )}
    </div>
  );
}
