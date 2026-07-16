import axios from "axios";
import type {
  DeviceSummary, Device, TelemetryReading, AlertItem, DigitalTwinResponse,
  AnalyticsOverview, FailureTrendPoint, DepartmentHealth, ManufacturerComparison,
} from "@/types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const client = axios.create({ baseURL: BASE_URL });

export const api = {
  devices: {
    list: (params?: { department?: string; device_type?: string; status?: string }) =>
      client.get<DeviceSummary[]>("/devices", { params }).then((r) => r.data),
    ranking: (order: "asc" | "desc" = "desc") =>
      client.get<DeviceSummary[]>("/devices/ranking", { params: { order } }).then((r) => r.data),
    get: (id: string) => client.get<Device>(`/devices/${id}`).then((r) => r.data),
  },
  telemetry: {
    history: (deviceId: string, hours = 24) =>
      client.get<TelemetryReading[]>(`/telemetry/${deviceId}`, { params: { hours } }).then((r) => r.data),
    latest: (deviceId: string) =>
      client.get<TelemetryReading>(`/telemetry/${deviceId}/latest`).then((r) => r.data),
  },
  alerts: {
    list: (params?: { severity?: string; acknowledged?: boolean; device_id?: string }) =>
      client.get<AlertItem[]>("/alerts", { params }).then((r) => r.data),
    acknowledge: (id: number, acknowledgedBy = "Biomedical Engineer") =>
      client.post<AlertItem>(`/alerts/${id}/acknowledge`, null, { params: { acknowledged_by: acknowledgedBy } }).then((r) => r.data),
  },
  digitalTwin: {
    get: (deviceId: string, telemetryHours = 168) =>
      client.get<DigitalTwinResponse>(`/digital-twin/${deviceId}`, { params: { telemetry_hours: telemetryHours } }).then((r) => r.data),
  },
  analytics: {
    overview: () => client.get<AnalyticsOverview>("/analytics/overview").then((r) => r.data),
    failureTrends: () => client.get<FailureTrendPoint[]>("/analytics/failure-trends").then((r) => r.data),
    departmentHealth: () => client.get<DepartmentHealth[]>("/analytics/department-health").then((r) => r.data),
    manufacturerComparison: () => client.get<ManufacturerComparison[]>("/analytics/manufacturer-comparison").then((r) => r.data),
  },
};

export const WS_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1")
  .replace("http", "ws")
  .replace("/api/v1", "/api/v1/telemetry/ws/live");
