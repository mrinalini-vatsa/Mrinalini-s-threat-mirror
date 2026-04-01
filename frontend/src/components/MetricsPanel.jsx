function Sparkline({ values = [] }) {
  const safe = values.length > 1 ? values : [0, 0];
  const max = Math.max(...safe, 1);
  const points = safe
    .map((v, i) => `${(i / (safe.length - 1)) * 100},${34 - (v / max) * 30}`)
    .join(" ");
  return (
    <svg className="sparkline" viewBox="0 0 100 36" preserveAspectRatio="none">
      <polyline fill="none" stroke="#00ff88" strokeWidth="2" points={points} />
    </svg>
  );
}

export default function MetricsPanel({ metrics, hasCritical, activeThreats, animatedTotal, avgHistory }) {
  if (!metrics) return null;
  const statusText = metrics.failures > 0 ? `${metrics.failures} FAILURE(S)` : "ALL SYSTEMS GO";
  return (
    <>
      <section className="metrics-grid">
        <div className={`metric-card ${hasCritical ? "critical" : ""}`}>
          <p className="metric-label">Total Alerts</p>
          <strong className="metric-value">{animatedTotal}</strong>
        </div>
        <div className={`metric-card ${hasCritical ? "critical" : ""}`}>
          <p className="metric-label">Active Threats</p>
          <strong className="metric-value">{activeThreats}</strong>
        </div>
        <div className={`metric-card ${hasCritical ? "critical" : ""}`}>
          <p className="metric-label">Avg Response Time</p>
          <strong className="metric-value">{metrics.avg_processing_time_ms.toFixed(2)} ms</strong>
          <Sparkline values={avgHistory} />
        </div>
        <div className={`metric-card ${metrics.failures > 0 ? "critical" : ""}`}>
          <p className="metric-label">Pipeline Status</p>
          <strong className="metric-value">{statusText}</strong>
        </div>
      </section>

      <section className="panel-card">
        <h3>Severity Distribution</h3>
        <div className="bars">
          {Object.entries(metrics.severity_distribution).map(([key, val]) => {
            const total = Math.max(metrics.total_alerts, 1);
            const pct = Math.max((val / total) * 100, val > 0 ? 2 : 0);
            return (
              <div className="bar-row" key={key}>
                <span className={`sev-label sev-${key.toLowerCase()}`}>{key}</span>
                <div className="bar-track">
                  <div className={`bar-fill sev-${key.toLowerCase()}`} style={{ width: `${pct}%` }} />
                </div>
                <span className="bar-value">{val}</span>
              </div>
            );
          })}
        </div>
      </section>
    </>
  );
}
