import axios from "axios";

const API_URL = import.meta.env.VITE_API_BASE_URL;

const api = axios.create({
  baseURL: `${API_URL}/api`,
  timeout: 10000,
});

export async function fetchAlerts() {
  const { data } = await api.get("/alerts");
  return data;
}

export async function fetchMetrics() {
  const { data } = await api.get("/metrics");
  return data;
}

export async function fetchAlertDetail(id) {
  const { data } = await api.get(`/alerts/${id}`);
  return data;
}

export async function fetchIncidentReport(id) {
  const { data } = await api.get(`/alerts/${id}/report`);
  return data.report;
}

export async function resolveAlert(id) {
  const { data } = await api.post(`/alerts/${id}/resolve`);
  return data;
}
