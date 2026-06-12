# Rechnungsmonster

Kostenloses Online-Prüftool für E-Rechnungen (XRechnung, UBL, CII, ZUGFeRD/Factur-X).

## Datenschutz

- Keine Anmeldung erforderlich
- Keine Speicherung von Rechnungsdaten
- Keine Datenbank
- Hochgeladene Dateien werden nach der Prüfung sofort gelöscht
- Der Prüfbericht wird nur im Browser angezeigt und kann als PDF heruntergeladen werden

## Features

- Upload von XML- und PDF-Rechnungen
- Erkennung von UBL und CII/XRechnung
- Extraktion eingebetteter XML-Daten aus ZUGFeRD/Factur-X-PDFs
- Validierung über den offiziellen KoSIT Validator (XRechnung 3.0.2)
- Ampel-Ansicht mit verständlichen Fehlermeldungen
- PDF-Prüfbericht zum Download

## Stack

- **Backend:** FastAPI, lxml, pikepdf, fpdf2
- **Frontend:** React + Vite
- **Validator:** `apps4everything/kosit-validator-xrechnung:3.0.2-1` (nur intern)

## Starten

```bash
docker compose up --build
```

| Dienst   | URL                   |
|----------|-----------------------|
| Frontend | http://localhost:5175 |
| Backend  | http://localhost:8020 |

Der Validator ist nur im Docker-Netzwerk erreichbar und nicht öffentlich exponiert.

## Lokale Entwicklung

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Schriftarten: sudo apt install fonts-dejavu-core
VALIDATOR_URL=http://localhost:8081 uvicorn main:app --reload --port 8020
```

Für lokale Entwicklung den Validator separat starten:

```bash
docker run -d -p 8081:8081 apps4everything/kosit-validator-xrechnung:3.0.2-1
```

### Frontend

```bash
cd frontend
npm install
VITE_API_URL=http://localhost:8020 npm run dev
```

## API

- `GET /` – Healthcheck
- `POST /api/upload` – Rechnung prüfen (multipart/form-data, Feld `file`)

Die Antwort enthält das Prüfergebnis und `report_pdf` (Base64-kodierter Prüfbericht).

## Hinweise

- PDFs ohne eingebettetes Rechnungs-XML werden erkannt, aber nicht validiert.
- Der KoSIT-Validator prüft nur XML-Inhalte (direkt oder aus PDF extrahiert).
