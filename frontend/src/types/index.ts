export type DeviceType = "Ventilator" | "MRI Scanner" | "Infusion Pump" | "Patient Monitor";
export type DeviceStatus = "Healthy" | "Warning" | "Critical" | "Offline" | "Under Maintenance";
export type RiskLevel = "Low" | "Medium" | "High";
export type AlertSeverity = "Info" | "Warning" | "Critical";

export interface DeviceSummary {
  id: string;
  device_name: string;
  device_type: DeviceType;
  department: string;
  status: DeviceStatus;
  current_failure_probability: number;
  current_rul_days: number | null;
}

export interface Device extends DeviceSummary {
  source_machine_id: number;
  manufacturer: string;
  model: string;
  location: string;
  purchase_date: string;
  warranty_expiry: string;
  expected_lifespan_years: number;
  age_years: number;
  last_maintenance_date: string | null;
  next_maintenance_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface TelemetryReading {
  id: number;
  device_id: string;
  recorded_at: string;
  voltage: number;
  fan_speed: number;
  power_consumption: number;
  vibration: number;
  temperature: number;
  cpu_utilization: number;
  battery_health: number;
  operating_hours: number;
  usage_count: number;
  network_status: boolean;
  calibration_status: boolean;
}

export interface ShapExplanation {
  feature: string;
  impact: number;
  explanation: string;
}

export interface Prediction {
  id: number;
  device_id: string;
  predicted_at: string;
  failure_probability: number;
  risk_level: RiskLevel;
  remaining_useful_life_days: number;
  prob_failure_7d: number;
  prob_failure_30d: number;
  prob_failure_90d: number;
  predicted_subsystem: string | null;
  model_version: string;
  shap_explanations: ShapExplanation[];
  recommendations: string[];
}

export interface AlertItem {
  id: number;
  device_id: string;
  alert_type: string;
  severity: AlertSeverity;
  message: string;
  created_at: string;
  acknowledged: boolean;
  acknowledged_by: string | null;
}

export interface ErrorLogItem {
  id: number;
  device_id: string;
  occurred_at: string;
  error_code: string;
  message: string;
}

export interface MaintenanceRecordItem {
  id: number;
  device_id: string;
  performed_at: string;
  subsystem: string;
  description: string;
  technician: string;
}

export interface FailureEventItem {
  id: number;
  device_id: string;
  occurred_at: string;
  subsystem: string;
  resolved: boolean;
}

export interface DigitalTwinResponse {
  device: Device;
  telemetry_trend: TelemetryReading[];
  prediction_history: Prediction[];
  error_logs: ErrorLogItem[];
  maintenance_history: MaintenanceRecordItem[];
  failure_history: FailureEventItem[];
}

export interface AnalyticsOverview {
  total_devices: number;
  healthy_devices: number;
  warning_devices: number;
  critical_devices: number;
  average_failure_probability: number;
  estimated_maintenance_cost_saved_usd: number;
  estimated_downtime_saved_hours: number;
  cost_model_note: string;
}

export interface FailureTrendPoint {
  month: string;
  failure_count: number;
}

export interface DepartmentHealth {
  department: string;
  total_devices: number;
  average_failure_probability: number;
  critical_count: number;
  warning_count: number;
  healthy_count: number;
}

export interface ManufacturerComparison {
  manufacturer: string;
  total_devices: number;
  average_failure_probability: number;
}

export interface LiveTelemetryTick {
  device_id: string;
  device_name: string;
  recorded_at: string;
  voltage: number;
  fan_speed: number;
  power_consumption: number;
  vibration: number;
  temperature: number;
  cpu_utilization: number;
  battery_health: number;
  network_status: boolean;
}
