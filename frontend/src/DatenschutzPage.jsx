import LegalLayout from "./LegalLayout";

export default function DatenschutzPage() {
  return (
    <LegalLayout title="Datenschutzerklärung" date="Stand: Juni 2026" activePage="datenschutz">
      <section>
        <h2>1. Verantwortlicher</h2>
        <p>
          Verantwortlicher im Sinne der DSGVO ist:
          <br />
          Christof Holdermann, Holdermann IT
          <br />
          Am Bungert 2, 77880 Sasbach
          <br />
          Telefon: +49 7841 8329775
          <br />
          E-Mail: christof@holdermann.me
        </p>
      </section>

      <section>
        <h2>2. Serverstandort &amp; Hosting</h2>
        <p>
          Diese Website wird auf einem Server in Deutschland gehostet (Hetzner Online
          GmbH, Gunzenhausen). Beim Aufruf der Website werden automatisch
          Server-Logfiles erstellt, die technisch notwendige Informationen wie
          IP-Adresse, Zeitpunkt des Zugriffs und aufgerufene Seite enthalten. Diese
          Logs werden nach spätestens 7 Tagen gelöscht und nicht an Dritte
          weitergegeben. Mit Hetzner besteht ein Auftragsverarbeitungsvertrag gemäß
          Art. 28 DSGVO. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO
          (berechtigtes Interesse am sicheren Betrieb).
        </p>
      </section>

      <section>
        <h2>3. Rechnungsprüfung (Datei-Upload)</h2>
        <p>
          Rechnungsmonster ist ein kostenloser Online-Dienst zur Prüfung von
          E-Rechnungen (XML, ZUGFeRD/Factur-X-PDF). Wenn Sie eine Datei hochladen,
          wird diese <strong>ausschließlich zur Durchführung der Validierung</strong>{" "}
          verarbeitet.
        </p>
        <p>
          Die hochgeladene Datei wird in einem temporären Speicherbereich verarbeitet
          und <strong>nach Abschluss der Prüfung unverzüglich gelöscht</strong>. Es
          werden keine Rechnungsdaten dauerhaft gespeichert, kein Nutzerkonto
          angelegt und keine Prüfhistorie geführt. Der erzeugte Prüfbericht wird
          Ihnen im Browser angezeigt bzw. zum Download bereitgestellt – eine
          Speicherung auf unseren Servern erfolgt nicht.
        </p>
        <p>
          Rechtsgrundlage ist Art. 6 Abs. 1 lit. b DSGVO (Durchführung des von Ihnen
          angefragten Dienstes) sowie Art. 6 Abs. 1 lit. f DSGVO (berechtigtes
          Interesse am Betrieb eines sicheren, datensparsamen Prüfdienstes).
        </p>
      </section>

      <section>
        <h2>4. Cookies</h2>
        <p>
          Diese Website verwendet keine Cookies. Es werden keine Tracking- oder
          Marketing-Cookies eingesetzt.
        </p>
      </section>

      <section>
        <h2>5. Schriftarten (Web Fonts)</h2>
        <p>
          Diese Website verwendet die Schriftart <em>Geist</em> (Vercel, Inc.).
          Die Schriftartdateien werden ausschließlich von unserem eigenen Server in
          Deutschland ausgeliefert (Hetzner Online GmbH, Gunzenhausen). Es wird{" "}
          <strong>keine Verbindung zu Google-Servern (Google Fonts) oder sonstigen
          externen Schriftarten-Diensten</strong> hergestellt. Es werden dabei keine
          personenbezogenen Daten an Dritte übermittelt.
        </p>
      </section>

      <section>
        <h2>6. Webanalyse</h2>
        <p>
          Derzeit wird auf dieser Website <strong>keine Webanalyse</strong>{" "}
          eingesetzt. Es werden keine Analyse-Cookies gesetzt und keine
          Nutzungsprofile erstellt.
        </p>
      </section>

      <section>
        <h2>7. Ihre Rechte</h2>
        <p>
          Sie haben das Recht auf Auskunft (Art. 15 DSGVO), Berichtigung (Art. 16
          DSGVO), Löschung (Art. 17 DSGVO), Einschränkung der Verarbeitung (Art. 18
          DSGVO), Datenübertragbarkeit (Art. 20 DSGVO) sowie Widerspruch (Art. 21
          DSGVO).
          <br />
          <br />
          Zur Geltendmachung Ihrer Rechte wenden Sie sich an: christof@holdermann.me
          <br />
          <br />
          Sie haben zudem das Recht, sich bei der zuständigen
          Datenschutz-Aufsichtsbehörde zu beschweren:
          <br />
          <strong>
            Landesbeauftragter für den Datenschutz und die Informationsfreiheit
            Baden-Württemberg (LfDI BW)
          </strong>
          <br />
          Königstraße 10a, 70173 Stuttgart
          <br />
          poststelle@lfdi.bwl.de
        </p>
      </section>

      <section>
        <h2>8. Datenlöschung</h2>
        <p>
          Server-Logfiles werden automatisch nach spätestens 7 Tagen gelöscht.
          Hochgeladene Rechnungsdateien werden nach der Prüfung sofort gelöscht und
          nicht archiviert. Da auf dieser Website keine Nutzerkonten existieren,
          fallen keine weiteren personenbezogenen Daten zur dauerhaften Speicherung
          an.
        </p>
      </section>
    </LegalLayout>
  );
}
