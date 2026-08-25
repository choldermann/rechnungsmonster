import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

const MONSTERSUITE_URL = "https://monstersuite.de";
const API_URL = import.meta.env.VITE_API_URL || "";

export default function SiteFooter({ activePage }) {
  const [versions, setVersions] = useState(null);

  useEffect(() => {
    fetch(`${API_URL}/api/version`)
      .then((r) => r.json())
      .then(setVersions)
      .catch(() => {});
  }, []);

  return (
    <footer className="site-footer">
      <div className="site-footer-left">
        <strong>Rechnungsmonster</strong> · part of monstersuite.de
        <br />
        © {new Date().getFullYear()} · made in Germany
        {versions && (
          <span className="site-footer-versions">
            KoSIT XRechnung {versions.kosit_xrechnung} · KoSIT Validator {versions.kosit_validator} · veraPDF {versions.verapdf}
          </span>
        )}
      </div>
      <div className="site-footer-right">
        <a href={MONSTERSUITE_URL} target="_blank" rel="noopener noreferrer">
          monstersuite.de
        </a>
        <Link
          to="/datenschutz"
          className={activePage === "datenschutz" ? "site-footer-link--active" : ""}
        >
          Datenschutz
        </Link>
        <Link
          to="/impressum"
          className={activePage === "impressum" ? "site-footer-link--active" : ""}
        >
          Impressum
        </Link>
      </div>
    </footer>
  );
}
