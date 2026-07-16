import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Lightbulb, Wrench, History } from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { Card, MetricCard } from "@/components/Card";
import { StatusBadge } from "@/components/StatusBadge";
import { api } from "@/api/client";
import type { DigitalTwinResponse } from "@/types";

export function DigitalTwinPage() {
  const { deviceId } = useParams<{ deviceId: string }>();
  const [data, setData] = useState<DigitalTwinResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!deviceId) return;
    setLoading(true);
    api.digitalTwin
      .get(deviceId, 168)
      .then(setData)
      .finally(() => setLoading(false));
  }, [deviceId]);

  if (loading) return <p className="p-8 text-sm text-ink-400">Loading digital twin...</p>;
  if (!data) return <p className="p-8 text-sm text-ink-400">Device not found.</p>;

  const { device, telemetry_trend, prediction_history, error_logs, maintenance_history, failure_history } = data;
  const latestPrediction = prediction_history[prediction_history.length - 1];

  const chartData = telemetry_trend.map((t) => ({
    time: new Date(t.recorded_at).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
    temperature: t.temperature,
    vibration: t.vibration,
    battery_health: t.battery_health,
  }));

  const riskTrendData = prediction_history.map((p) => ({
    date: new Date(p.predicted_at).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
    probability: Math.round(p.failure_probability * 100),
  }));

  return (
    <div className="space-y-6">
      <Link to="/inventory" className="inline-flex items-center gap-1.5 text-sm text-ink-400 hover:text-clinical">
        <ArrowLeft size={14} /> Back to inventory
      </Link>

      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold text-ink-900">{device.device_name}</h1>
            <StatusBadge status={device.status} />
          </div>
          <p className="mt-1 text-sm text-ink-400">
            {device.manufacturer} · {device.department} · {device.location}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Failure Probability"
          value={`${(device.current_failure_probability * 100).toFixed(0)}%`}
          accent={device.current_failure_probability > 0.7 ? "critical" : device.current_failure_probability > 0.35 ? "warning" : "healthy"}
        />
        <MetricCard label="Remaining Useful Life" value={device.current_rul_days ? `${device.current_rul_days.toFixed(0)}d` : "—"} accent="teal" />
        {latestPrediction && (
          <>
            <MetricCard label="30-Day Failure Risk" value={`${(latestPrediction.prob_failure_30d * 100).toFixed(0)}%`} accent="clinical" />
            <MetricCard label="Predicted Subsystem" value={<span className="text-lg">{latestPrediction.predicted_subsystem ?? "—"}</span>} accent="clinical" />
          </>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <h2 className="mb-4 text-sm font-semibold text-ink-900">Sensor Trends (7-day window)</h2>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="time" tick={{ fontSize: 11, fill: "#64748B" }} />
              <YAxis tick={{ fontSize: 11, fill: "#64748B" }} />
              <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #E2E8F0" }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line type="monotone" dataKey="temperature" stroke="#DC2626" dot={false} strokeWidth={2} name="Temp (°C)" />
              <Line type="monotone" dataKey="vibration" stroke="#0A5C7A" dot={false} strokeWidth={2} name="Vibration" />
              <Line type="monotone" dataKey="battery_health" stroke="#0D9488" dot={false} strokeWidth={2} name="Battery %" />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h2 className="mb-4 text-sm font-semibold text-ink-900">Risk Trend (Failure Probability History)</h2>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={riskTrendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#64748B" }} />
              <YAxis tick={{ fontSize: 11, fill: "#64748B" }} unit="%" />
              <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #E2E8F0" }} />
              <Line type="monotone" dataKey="probability" stroke="#D97706" dot={{ r: 3 }} strokeWidth={2} name="Failure Probability %" />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {latestPrediction && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card>
            <div className="mb-3 flex items-center gap-2">
              <Lightbulb size={16} className="text-status-warning" />
              <h2 className="text-sm font-semibold text-ink-900">Top Reasons (Explainable AI)</h2>
            </div>
            <ul className="space-y-2.5">
              {latestPrediction.shap_explanations.map((reason, i) => (
                <li key={i} className="flex items-start gap-2.5 text-sm text-ink-600">
                  <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-clinical" />
                  {reason.explanation}
                </li>
              ))}
            </ul>
          </Card>

          <Card>
            <div className="mb-3 flex items-center gap-2">
              <Wrench size={16} className="text-teal" />
              <h2 className="text-sm font-semibold text-ink-900">Recommended Actions</h2>
            </div>
            <ul className="space-y-2.5">
              {latestPrediction.recommendations.map((rec, i) => (
                <li key={i} className="flex items-start gap-2.5 text-sm text-ink-600">
                  <span className="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-teal-light text-[10px] font-bold text-clinical-dark">
                    {i + 1}
                  </span>
                  {rec}
                </li>
              ))}
            </ul>
          </Card>
        </div>
      )}

      <Card padded={false}>
        <div className="flex items-center gap-2 border-b border-ink-200/60 px-5 py-4">
          <History size={16} className="text-ink-400" />
          <h2 className="text-sm font-semibold text-ink-900">Maintenance &amp; Failure History</h2>
        </div>
        <div className="grid grid-cols-1 divide-y divide-ink-200/60 lg:grid-cols-2 lg:divide-x lg:divide-y-0">
          <div>
            <p className="px-5 pt-4 text-xs font-medium uppercase tracking-wide text-ink-400">Maintenance Records</p>
            <div className="max-h-64 overflow-y-auto px-5 py-3">
              {maintenance_history.length === 0 && <p className="text-sm text-ink-400">No maintenance recorded.</p>}
              {maintenance_history.slice(0, 15).map((m) => (
                <div key={m.id} className="border-b border-ink-200/40 py-2 last:border-0">
                  <p className="text-sm text-ink-900">{m.subsystem}</p>
                  <p className="text-xs text-ink-400">{new Date(m.performed_at).toLocaleDateString()} · {m.technician}</p>
                </div>
              ))}
            </div>
          </div>
          <div>
            <p className="px-5 pt-4 text-xs font-medium uppercase tracking-wide text-ink-400">Failure Events</p>
            <div className="max-h-64 overflow-y-auto px-5 py-3">
              {failure_history.length === 0 && <p className="text-sm text-ink-400">No failures recorded.</p>}
              {failure_history.slice(0, 15).map((f) => (
                <div key={f.id} className="border-b border-ink-200/40 py-2 last:border-0">
                  <p className="text-sm text-ink-900">{f.subsystem}</p>
                  <p className="text-xs text-ink-400">{new Date(f.occurred_at).toLocaleDateString()} · {f.resolved ? "Resolved" : "Unresolved"}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
