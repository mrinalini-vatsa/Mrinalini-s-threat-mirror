import { useEffect, useRef, useState } from "react";
import AlertsTable from "../components/AlertsTable";
import MetricsPanel from "../components/MetricsPanel";
import { fetchAlertDetail, fetchAlerts, fetchMetrics } from "../api/client";

export default function DashboardPage() {
  const [alerts, setAlerts] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [clock, setClock] = useState(new Date());
  const [newAlertIds, setNewAlertIds] = useState(new Set());
  const [animatedTotal, setAnimatedTotal] = useState(0);
  const [avgHistory, setAvgHistory] = useState([]);
  const [tickerItems, setTickerItems] = useState([]);
  const previousIdsRef = useRef(new Set());

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      const [alertsRes, metricsRes] = await Promise.all([fetchAlerts(), fetchMetrics()]);
      if (!mounted) return;
      const incomingNew = alertsRes
        .filter((a) => !previousIdsRef.current.has(a.id))
        .map((a) => a.id);
      if (incomingNew.length > 0) {
        setNewAlertIds(new Set(incomingNew));
        setTimeout(() => setNewAlertIds(new Set()), 1200);
      }
      previousIdsRef.current = new Set(alertsRes.map((a) => a.id));
      setAlerts(alertsRes);
      setMetrics(metricsRes);
      setAvgHistory((prev) => [...prev.slice(-11), Number(metricsRes.avg_processing_time_ms.toFixed(2))]);

      const topFive = alertsRes.slice(0, 5);
      const details = await Promise.all(topFive.map((a) => fetchAlertDetail(a.id)));
      const feed = details.map((d) => {
        const latest = d.decisions[d.decisions.length - 1];
        const decision = latest?.decision || "PENDING";
        const confidence = latest ? `${Math.round(latest.confidence * 100)}%` : "--";
        return `\u2192 ${d.ip_address} | ${d.event_type} | Decision: ${decision} | Confidence: ${confidence}`;
      });
      setTickerItems(feed);
    };
    load();
    const timer = setInterval(load, 10000);
    const clockTimer = setInterval(() => setClock(new Date()), 1000);
    return () => {
      mounted = false;
      clearInterval(timer);
      clearInterval(clockTimer);
    };
  }, []);

  useEffect(() => {
    if (!metrics) return;
    const target = metrics.total_alerts;
    const interval = setInterval(() => {
      setAnimatedTotal((count) => (count < target ? count + 1 : count > target ? target : count));
    }, 35);
    return () => clearInterval(interval);
  }, [metrics]);

  const hasCritical = alerts.some((a) => a.severity === "CRITICAL");
  const activeThreats = alerts.filter((a) => a.severity === "HIGH" || a.severity === "CRITICAL").length;
  const systemStatus = hasCritical ? "INCIDENT ACTIVE" : "SYSTEM OPERATIONAL";

  return (
    <div className="stack">
      <header className="soc-header panel-card">
        <h1 className="logo">
          THREATMIRROR<span className="cursor">_</span>
        </h1>
        <div className="clock">{clock.toLocaleTimeString()}</div>
        <div className={`status-pill ${hasCritical ? "critical" : ""}`}>{systemStatus}</div>
      </header>

      <MetricsPanel
        metrics={metrics}
        hasCritical={hasCritical}
        activeThreats={activeThreats}
        animatedTotal={animatedTotal}
        avgHistory={avgHistory}
      />
      <AlertsTable alerts={alerts} newAlertIds={newAlertIds} />

      <footer className="ticker panel-card">
        <div className="ticker-track">
          {(tickerItems.length ? tickerItems : ["\u2192 Waiting for playbook decisions..."])
            .concat(tickerItems.length ? tickerItems : [])
            .map((item, idx) => (
              <span key={`${idx}-${item}`}>{item}</span>
            ))}
        </div>
      </footer>
    </div>
  );
}
