import { useRef, useState } from "react";

const ACCEPTED_TYPES = [
  "application/pdf",
  "application/xml",
  "text/xml",
];

const ACCEPTED_EXTENSIONS = [".pdf", ".xml"];

function isAcceptedFile(file) {
  if (!file) {
    return false;
  }

  const lowerName = file.name.toLowerCase();
  if (ACCEPTED_EXTENSIONS.some((ext) => lowerName.endsWith(ext))) {
    return true;
  }

  return ACCEPTED_TYPES.includes(file.type);
}

function formatFileSize(bytes) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function Dropzone({ file, onFileSelect, disabled }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  function openPicker() {
    if (!disabled) {
      inputRef.current?.click();
    }
  }

  function handleFiles(fileList) {
    const selected = fileList?.[0];
    if (!selected) {
      return;
    }

    if (!isAcceptedFile(selected)) {
      onFileSelect(null, "Bitte eine PDF- oder XML-Datei hochladen.");
      return;
    }

    onFileSelect(selected, "");
  }

  function handleInputChange(event) {
    handleFiles(event.target.files);
    event.target.value = "";
  }

  function handleDragOver(event) {
    event.preventDefault();
    if (!disabled) {
      setDragging(true);
    }
  }

  function handleDragLeave(event) {
    event.preventDefault();
    setDragging(false);
  }

  function handleDrop(event) {
    event.preventDefault();
    setDragging(false);
    if (!disabled) {
      handleFiles(event.dataTransfer.files);
    }
  }

  return (
    <div className="dropzone-wrap">
      <div
        className={[
          "dropzone",
          dragging ? "dropzone--dragging" : "",
          file ? "dropzone--has-file" : "",
          disabled ? "dropzone--disabled" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        onClick={openPicker}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            openPicker();
          }
        }}
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label="Datei per Drag and Drop ablegen oder zum Auswählen klicken"
      >
        <input
          ref={inputRef}
          type="file"
          accept=".xml,.pdf,application/pdf,application/xml,text/xml"
          className="dropzone-input"
          onChange={handleInputChange}
          disabled={disabled}
          tabIndex={-1}
        />

        <div className="dropzone-icon" aria-hidden="true">
          <svg viewBox="0 0 48 48" fill="none">
            <path
              d="M24 32V16M24 16L18 22M24 16L30 22"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M10 34C10 30.6863 12.6863 28 16 28H32C35.3137 28 38 30.6863 38 34V36C38 37.1046 37.1046 38 36 38H12C10.8954 38 10 37.1046 10 36V34Z"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
          </svg>
        </div>

        {file ? (
          <div className="dropzone-file">
            <span className="dropzone-file-name">{file.name}</span>
            <span className="dropzone-file-meta">{formatFileSize(file.size)}</span>
            <span className="dropzone-hint">Klicken oder ablegen, um die Datei zu ersetzen</span>
          </div>
        ) : (
          <div className="dropzone-copy">
            <strong>Datei hier ablegen</strong>
            <span>oder klicken zum Auswählen</span>
            <span className="dropzone-formats">
              XRechnung-XML · ZUGFeRD / Factur-X-PDF
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
