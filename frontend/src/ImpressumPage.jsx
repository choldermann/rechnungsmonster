import LegalLayout from "./LegalLayout";

export default function ImpressumPage() {
  return (
    <LegalLayout title="Impressum" activePage="impressum">
      <section>
        <h2>Angaben gemäß § 5 TMG</h2>
        <p>
          Christof Holdermann
          <br />
          Holdermann IT
          <br />
          Am Bungert 2
          <br />
          77880 Sasbach
        </p>
      </section>

      <section>
        <h2>Kontakt</h2>
        <p>
          Telefon: +49 7841 8329775
          <br />
          E-Mail: christof@holdermann.me
        </p>
      </section>

      <section>
        <h2>Umsatzsteuer-ID</h2>
        <p>
          Umsatzsteuer-Identifikationsnummer gemäß § 27 a Umsatzsteuergesetz:
          <br />
          DE237464826
        </p>
      </section>

      <section>
        <h2>Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV</h2>
        <p>
          Christof Holdermann
          <br />
          Am Bungert 2
          <br />
          77880 Sasbach
        </p>
      </section>

      <section>
        <h2>Haftung für Inhalte</h2>
        <p>
          Als Diensteanbieter sind wir gemäß § 7 Abs. 1 TMG für eigene Inhalte auf
          diesen Seiten nach den allgemeinen Gesetzen verantwortlich. Nach §§ 8 bis
          10 TMG sind wir als Diensteanbieter jedoch nicht verpflichtet,
          übermittelte oder gespeicherte fremde Informationen zu überwachen oder
          nach Umständen zu forschen, die auf eine rechtswidrige Tätigkeit
          hinweisen.
        </p>
      </section>

      <section>
        <h2>Haftungsausschluss für Validierungsergebnisse</h2>
        <p>
          Die von Rechnungsmonster bereitgestellten Validierungsergebnisse, Hinweise
          und Empfehlungen dienen ausschließlich der technischen Prüfung
          elektronischer Rechnungen und stellen keine Rechts-, Steuer- oder
          Unternehmensberatung dar.
        </p>
        <p>
          Die Validierung erfolgt auf Basis der jeweils unterstützten Standards und
          Regelwerke. Trotz sorgfältiger Entwicklung übernimmt Rechnungsmonster keine
          Gewähr für die Richtigkeit, Vollständigkeit oder Aktualität der
          bereitgestellten Informationen und Prüfergebnisse.
        </p>
        <p>
          Die Nutzung der Ergebnisse erfolgt auf eigenes Risiko. Für Entscheidungen
          oder Maßnahmen, die auf Grundlage der bereitgestellten Informationen
          getroffen werden, wird keine Haftung übernommen. Im Zweifel sollte
          fachkundiger Rat eingeholt werden.
        </p>
        <p>
          <strong>Hinweis:</strong> Ein erfolgreiches Validierungsergebnis bedeutet
          nicht automatisch, dass eine Rechnung steuerlich, rechtlich oder
          buchhalterisch korrekt ist.
        </p>
      </section>

      <section>
        <h2>Haftung für Links</h2>
        <p>
          Unser Angebot enthält Links zu externen Websites Dritter, auf deren Inhalte
          wir keinen Einfluss haben. Deshalb können wir für diese fremden Inhalte
          auch keine Gewähr übernehmen. Für die Inhalte der verlinkten Seiten ist
          stets der jeweilige Anbieter oder Betreiber der Seiten verantwortlich.
        </p>
      </section>
    </LegalLayout>
  );
}
