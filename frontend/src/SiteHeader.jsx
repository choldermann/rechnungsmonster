import { useState } from "react";
import { Link } from "react-router-dom";

const MONSTERSUITE_URL = "https://monstersuite.de";

export default function SiteHeader() {
  const [navOpen, setNavOpen] = useState(false);

  function closeNav() {
    setNavOpen(false);
  }

  return (
    <header className="site-header">
      <div className="brand">
        <img
          src="/rechnungsmonster.svg"
          alt="Rechnungsmonster"
          className="brand-logo"
        />
        <span className="brand-text">
          <Link to="/" className="brand-title" aria-label="Rechnungsmonster Startseite">
            <strong>
              <span className="brand-sig">Rechnungs</span>
              <span className="brand-mon">monster</span>
            </strong>
          </Link>
          <a
            href={MONSTERSUITE_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="brand-suite"
          >
            part of monstersuite.de
          </a>
        </span>
      </div>

      <nav className={`nav${navOpen ? " nav--open" : ""}`} aria-label="Hauptnavigation">
        <Link to="/#how-it-works" onClick={closeNav}>
          So funktioniert&apos;s
        </Link>
        <Link to="/#formate" onClick={closeNav}>
          Formate
        </Link>
        <Link to="/#upload" onClick={closeNav}>
          Prüfen
        </Link>
        <a
          href={MONSTERSUITE_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="nav-monster"
          onClick={closeNav}
        >
          MonsterSuite ↗
        </a>
      </nav>

      <button
        type="button"
        className="menu-btn"
        aria-label="Menü öffnen"
        aria-expanded={navOpen}
        onClick={() => setNavOpen((open) => !open)}
      >
        <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <line x1="3" y1="6" x2="17" y2="6" />
          <line x1="3" y1="11" x2="17" y2="11" />
          <line x1="3" y1="16" x2="17" y2="16" />
        </svg>
      </button>
    </header>
  );
}
