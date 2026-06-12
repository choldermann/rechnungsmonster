export default function InfoAccordions() {
  return (
    <section
      id="how-it-works"
      className="info-accordions"
      aria-label="Informationen zur Prüfung"
    >
      <details className="info-accordion" open>
        <summary className="info-accordion-summary">So funktioniert&apos;s</summary>
        <div className="info-accordion-body">
          <ol className="how-steps">
            <li>
              <strong>Datei hochladen</strong>
              <span>
                XRechnung-XML, reines EN-16931-XML oder PDF mit eingebetteter
                Rechnung (ZUGFeRD/Factur-X)
              </span>
            </li>
            <li>
              <strong>KoSIT-Validierung</strong>
              <span>
                Offizieller Standard für XRechnung 3.0 (XML-Schema, EN&nbsp;16931,
                XRechnung-Regeln)
              </span>
            </li>
            <li>
              <strong>Zusatzprüfungen</strong>
              <span>
                Erweitertes Verfahren: PDF/A-3, XMP-Metadaten, XML-Einbettung und
                ergänzende Geschäftsregeln
              </span>
            </li>
            <li>
              <strong>Ergebnis &amp; Bericht</strong>
              <span>
                Ampel, Detailbefunde und PDF-Prüfbericht – ohne Speicherung
              </span>
            </li>
          </ol>
          <p className="how-note">
            <strong>Wichtig:</strong> Das Gesamtergebnis richtet sich nach dem{" "}
            <strong>offiziellen KoSIT-Validator</strong>. Zusatzprüfungen zeigen
            Abweichungen, die strengere Tools oder Empfänger melden können – auch
            wenn KoSIT die XML-Datei als gültig einstuft.
          </p>
        </div>
      </details>

      <details className="info-accordion" id="formate">
        <summary className="info-accordion-summary">
          XRechnung, ZUGFeRD &amp; Factur-X – was ist was?
        </summary>
        <div className="info-accordion-body">
          <p className="format-intro">
            Alle genannten Formate basieren auf der europäischen Norm EN&nbsp;16931.
            Der Unterschied liegt vor allem darin, <em>wie</em> die Rechnung
            übermittelt wird – als reine XML-Datei oder als PDF mit eingebetteten
            Daten.
          </p>

          <div className="format-cards">
            <article className="format-card">
              <h3>XRechnung</h3>
              <p className="format-card-tag">Reines XML · B2G-Fokus</p>
              <p>
                XRechnung ist der deutsche Standard für elektronische Rechnungen
                an öffentliche Auftraggeber. Es handelt sich um eine{" "}
                <strong>reine XML-Datei</strong> (ohne PDF) – meist als CII- oder
                UBL-Profil mit deutschen XRechnung-Erweiterungen.
              </p>
              <p className="format-card-who">
                <strong>Typisch eingesetzt von:</strong> Unternehmen und
                Einrichtungen, die an Bund, Länder, Kommunen oder andere
                öffentliche Stellen fakturieren. Empfänger verlangen oft eine
                Leitweg-ID.
              </p>
            </article>

            <article className="format-card">
              <h3>ZUGFeRD</h3>
              <p className="format-card-tag">PDF + XML · B2B in Deutschland</p>
              <p>
                ZUGFeRD ist ein <strong>hybrides Format</strong>: eine für Menschen
                lesbare PDF-Rechnung mit eingebettetem maschinenlesbarem XML
                (PDF/A-3). In Deutschland sehr verbreitet im Geschäftsverkehr
                zwischen Unternehmen.
              </p>
              <p className="format-card-who">
                <strong>Typisch eingesetzt von:</strong> Mittelstand, Handel und
                Dienstleister im B2B, deren Partner weiterhin PDF sehen möchten,
                aber strukturierte Daten benötigen.
              </p>
            </article>

            <article className="format-card">
              <h3>Factur-X</h3>
              <p className="format-card-tag">PDF + XML · international (FR/EU)</p>
              <p>
                Factur-X ist der französische Name für dasselbe hybride Prinzip wie
                ZUGFeRD&nbsp;2.x – technisch eng verwandt, ebenfalls PDF/A-3 mit
                EN-16931-XML. In Frankreich und zunehmend EU-weit gebräuchlich.
              </p>
              <p className="format-card-who">
                <strong>Typisch eingesetzt von:</strong> Unternehmen mit
                internationalen Partnern, französischen Kunden oder ERP-Systemen,
                die „Factur-X“ ausliefern.
              </p>
            </article>
          </div>

          <p className="format-summary">
            <strong>Kurz gesagt:</strong> Behörden und öffentliche Auftraggeber in
            Deutschland erwarten meist <strong>XRechnung (XML)</strong>. Im
            Unternehmensverkehr sind <strong>ZUGFeRD/Factur-X (PDF mit XML)</strong>{" "}
            häufig – beides können Sie hier prüfen. Rechnungsmonster extrahiert bei
            PDFs automatisch das eingebettete XML und validiert es.
          </p>
        </div>
      </details>
    </section>
  );
}
