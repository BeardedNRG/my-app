import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const api = axios.create({ baseURL: `${BACKEND_URL}/api` });

export const getStatus = () => api.get("/status").then((r) => r.data);
export const startIngest = (force = false) => api.post("/ingest", { force }).then((r) => r.data);
export const getIngestStatus = () => api.get("/ingest/status").then((r) => r.data);
export const getSources = (params = {}) => api.get("/sources", { params }).then((r) => r.data);
export const getSource = (id) => api.get(`/sources/${id}`).then((r) => r.data);
export const getContradictions = () => api.get("/contradictions").then((r) => r.data);
export const getPriority = () => api.get("/priority").then((r) => r.data);
export const getArtifacts = () => api.get("/artifacts").then((r) => r.data);
export const getArtifact = (name) => api.get(`/artifacts/${encodeURIComponent(name)}`).then((r) => r.data);
export const getReport = () => api.get("/report").then((r) => r.data);
export const operatorAccept = (operator, note) =>
  api.post("/operator/accept", { operator, note }).then((r) => r.data);
