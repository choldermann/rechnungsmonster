import { useEffect } from "react";
import { Link } from "react-router-dom";
import SiteHeader from "./SiteHeader";
import SiteFooter from "./SiteFooter";

export default function LegalLayout({ title, date, children, activePage }) {
  useEffect(() => {
    const previousTitle = document.title;
    document.title = `${title} — Rechnungsmonster`;
    return () => {
      document.title = previousTitle;
    };
  }, [title]);

  return (
    <>
      <SiteHeader />
      <div className="legal-wrap">
        <Link to="/" className="legal-back">
          ← Zurück zur Startseite
        </Link>
        <h1>{title}</h1>
        {date && <p className="legal-date">{date}</p>}
        <div className="legal-sections">{children}</div>
      </div>
      <SiteFooter activePage={activePage} />
    </>
  );
}
