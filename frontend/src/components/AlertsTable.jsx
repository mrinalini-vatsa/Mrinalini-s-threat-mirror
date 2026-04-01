import { Link } from "react-router-dom";

const severityClass = {
  CRITICAL: "sev-critical",
  HIGH: "sev-high",
  MEDIUM: "sev-medium",
  LOW: "sev-low",
};

const countryFlag = () => "🌐";

export default function AlertsTable({ alerts, newAlertIds }) {
  const isNew = (createdAt) => Date.now() - new Date(createdAt).getTime() < 30000;
  return (
    <section className="panel-card">
      <h2>Live Alert Feed</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>IP</th>
            <th>User</th>
            <th>Event</th>
            <th>Severity</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {alerts.map((alert) => (
            <tr
              key={alert.id}
              className={`${severityClass[alert.severity] || "sev-low"} ${
                newAlertIds.has(alert.id) ? "row-slide-in" : ""
              }`}
            >
              <td>
                <Link to={`/alerts/${alert.id}`}>{alert.id}</Link>
              </td>
              <td className="ip-cell">
                {countryFlag(alert.ip_address)} <code>{alert.ip_address}</code>
              </td>
              <td>{alert.user_id}</td>
              <td>
                <span className="chip">{alert.event_type}</span>
              </td>
              <td>
                <span className={`badge ${severityClass[alert.severity] || "sev-low"}`}>{alert.severity}</span>
                {isNew(alert.created_at) && <span className="new-badge">NEW</span>}
              </td>
              <td>{new Date(alert.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
