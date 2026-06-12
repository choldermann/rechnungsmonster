function TrafficLight({ status, size = "md" }) {
  return (
    <span
      className={`traffic-light traffic-light--${status} traffic-light--${size}`}
      aria-hidden="true"
    />
  );
}

function trafficLightForValidation(validation) {
  if (!validation) {
    return "gray";
  }
  if (!validation.available) {
    return "gray";
  }
  return validation.summary?.traffic_light || (validation.valid ? "green" : "red");
}

function trafficLabelForValidation(validation) {
  if (!validation) {
    return "Keine Validierung";
  }
  if (!validation.available) {
    return validation.error || "Validator nicht verfügbar";
  }
  return validation.summary?.traffic_label || (validation.valid ? "Gültig" : "Ungültig");
}

function statusLabel(status) {
  if (status === "green") {
    return "In Ordnung";
  }
  if (status === "yellow") {
    return "Hinweis";
  }
  if (status === "red") {
    return "Fehler";
  }
  return "Nicht geprüft";
}

function issueTrafficStatus(level) {
  if (level === "warning") {
    return "yellow";
  }
  if (level === "error" || level === "fatal") {
    return "red";
  }
  return "gray";
}

function ValidationIssueList({ issues }) {
  if (!issues.length) {
    return null;
  }

  return (
    <ul className="validation-issues">
      {issues.map((issue, index) => (
        <li
          key={`${issue.rule_code || issue.error_number || "issue"}-${index}`}
          className={`validation-issue validation-issue--${issue.level}`}
        >
          <TrafficLight status={issueTrafficStatus(issue.level)} />
          <div>
            {(issue.line_reference || issue.location) && (
              <div className="issue-location">
                {[issue.line_reference, issue.location].filter(Boolean).join(" · ")}
              </div>
            )}
            {issue.line_content && (
              <pre className="issue-line-content">{issue.line_content}</pre>
            )}
            <p className="issue-text">{issue.text}</p>
          </div>
        </li>
      ))}
    </ul>
  );
}

function ValidationCheckList({ checks }) {
  if (!checks.length) {
    return null;
  }

  return (
    <div className="validation-checks">
      {checks.map((check) => (
        <div key={check.id} className="validation-check">
          <TrafficLight status={check.status} />
          <span className="validation-check-label">{check.label}</span>
          <span className={`validation-check-state state-${check.status}`}>
            {statusLabel(check.status)}
          </span>
        </div>
      ))}
    </div>
  );
}

function ValidationSection({ section, variant }) {
  if (!section) {
    return null;
  }

  const status = section.traffic_light || "gray";
  const issues = section.issues || [];
  const checks = section.checks || [];

  return (
    <section className={`validation-section validation-section--${variant}`}>
      <div className="validation-section-header">
        <div>
          {variant === "kosit" && (
            <span className="validation-official-badge">Offiziell</span>
          )}
          <h4>{section.title}</h4>
          {section.subtitle && (
            <p className="validation-section-subtitle">{section.subtitle}</p>
          )}
          {section.scenario && (
            <p className="validation-scenario">Szenario: {section.scenario}</p>
          )}
        </div>
        <div className={`validation-section-status validation-section-status--${status}`}>
          <TrafficLight status={status} size="md" />
          <span>{section.traffic_label}</span>
        </div>
      </div>

      <ValidationCheckList checks={checks} />
      <ValidationIssueList issues={issues} />

      {issues.length === 0 && status === "green" && (
        <p className="validation-ok-hint">Keine Befunde in diesem Bereich.</p>
      )}
    </section>
  );
}

function buildLegacySections(summary) {
  const kositCheckIds = new Set([
    "val-xml",
    "val-xsd",
    "val-sch.1",
    "val-sch.2",
    "scenario",
  ]);

  const checks = summary.checks || [];
  const issues = summary.issues || [];

  return {
    kosit: {
      title: "KoSIT Validator",
      subtitle: "Offizielle XML-Validierung (XRechnung / EN 16931)",
      scenario: summary.scenario,
      traffic_light: summary.traffic_light,
      traffic_label: summary.traffic_label,
      checks: checks.filter((check) => kositCheckIds.has(check.id)),
      issues: issues.filter((issue) => issue.source === "kosit" || !issue.source),
    },
    extended: {
      title: "Zusatzprüfungen",
      subtitle: "PDF/A, XMP-Metadaten und ergänzende XML-Regeln – kein Ersatz für KoSIT",
      traffic_light: "gray",
      traffic_label: "Nicht getrennt verfügbar",
      checks: checks.filter((check) => !kositCheckIds.has(check.id)),
      issues: issues.filter((issue) => issue.source && issue.source !== "kosit"),
    },
  };
}

export default function ValidationPanel({ validation }) {
  if (!validation) {
    return null;
  }

  const summary = validation.summary || {};
  const overallStatus = trafficLightForValidation(validation);
  const sections = summary.kosit
    ? { kosit: summary.kosit, extended: summary.extended }
    : buildLegacySections(summary);

  return (
    <div className="validation-panel">
      <h3>Prüfergebnis</h3>

      <div className={`validation-summary validation-summary--${overallStatus}`}>
        <TrafficLight status={overallStatus} size="lg" />
        <div>
          <strong>Gesamtergebnis: {trafficLabelForValidation(validation)}</strong>
          <p className="validation-overall-note">
            {summary.overall_note ||
              "Maßgeblich ist das offizielle KoSIT-Ergebnis. Zusatzprüfungen ergänzen PDF/A, XMP und weitere XML-Regeln."}
          </p>
        </div>
      </div>

      <ValidationSection section={sections.kosit} variant="kosit" />
      <ValidationSection section={sections.extended} variant="extended" />
    </div>
  );
}

export { TrafficLight, trafficLightForValidation, trafficLabelForValidation };
