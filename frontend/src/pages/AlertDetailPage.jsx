import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchAlertDetail, fetchIncidentReport, resolveAlert } from "../api/client";

export default function AlertDetailPage() {
  const { id } = useParams();
  const [detail, setDetail] = useState(null);
  const [report, setReport] = useState("");

  const load = async () => {
    const [detailRes, reportRes] = await Promise.all([fetchAlertDetail(id), fetchIncidentReport(id)]);
    setDetail(detailRes);
    setReport(reportRes);
  };

  useEffect(() => {
    load();
  }, [id]);

  if (!detail) return <div className="card">Loading...</div>;

  return (
    <div className="stack">
      <section className="card">
        <h2>Alert #{detail.id}</h2>
        <p>
          {detail.event_type} from {detail.ip_address} ({detail.severity})
        </p>
        <button
          onClick={async () => {
            await resolveAlert(id);
            await load();
          }}
        >
          Mark Resolved
        </button>
      </section>

      <section className="card">
        <h3>Enrichment Data</h3>
        <ul>
          {detail.enrichments.map((item, idx) => (
            <li key={idx}>
              score={item.reputation_score}, country={item.country}, isp={item.isp}, source={item.source}
            </li>
          ))}
        </ul>
      </section>

      <section className="card">
        <h3>Decision Trace</h3>
        <ul>
          {detail.decisions.map((item, idx) => (
            <li key={idx}>
              {item.decision} ({item.confidence.toFixed(2)}): {item.reasons.join("; ")}
            </li>
          ))}
        </ul>
      </section>

      <section className="card">
        <h3>Lifecycle Timeline</h3>
        <ul>
          {detail.timeline.map((item, idx) => (
            <li key={idx}>
              {item.state} - {item.notes} ({new Date(item.created_at).toLocaleString()})
            </li>
          ))}
        </ul>
      </section>

      <section className="card">
        <h3>Related Alerts</h3>
        <ul>
          {detail.related_alerts.map((item, idx) => (
            <li key={idx}>
              Related alert #{item.related_alert_id}: {item.reason}
            </li>
          ))}
        </ul>
      </section>

      <section className="card">
        <h3>Incident Report</h3>
        <pre>{report}</pre>
      </section>
    </div>
  );
}
