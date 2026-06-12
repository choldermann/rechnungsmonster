import { Link } from "react-router-dom";

const MONSTERSUITE_URL = "https://monstersuite.de";

export default function SiteFooter({ activePage }) {
  return (
    <footer className="site-footer">
      <div className="site-footer-left">
        <strong>Rechnungsmonster</strong> · part of monstersuite.de
        <br />
        © {new Date().getFullYear()} · made in Germany
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
