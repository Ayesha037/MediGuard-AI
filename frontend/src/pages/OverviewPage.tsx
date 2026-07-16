import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { AlertTriangle, TrendingDown, Clock, Activity } from "lucide-react";
import { Card, MetricCard } from "@/components/Card";
import { StatusBadge } from "@/components/StatusBadge";
import { api } from "@/api/client";
import type { AnalyticsOverview, DeviceSummary, AlertItem } from "@/types";

export function OverviewPage() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [ranking, setRanking] = useState<DeviceSummary[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.analytics.overview(),
      api.devices.ranking("desc"),
      api.alerts.list({ acknowledged: false }),
    ])
      .then(([ov, rank, al]) => {
        setOverview(ov);
        setRanking(rank.slice(0, 8));
        setAlerts(al.slice(0, 5));
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState />;
  if (!overview) return null;

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4"
      >
        <MetricCard label="Total Devices" value={overview.total_devices} accent="clinical" />
        <MetricCard
          label="Critical Devices"
          value={overview.critical_devices}
          sublabel={`${overview.warning_devices} in warning`}
          accent="critical"
        />
        <MetricCard
          label="Avg. Failure Probability"
          value={`${(overview.average_failure_probability * 100).toFixed(1)}%`}
          accent="warning"
        />
        <MetricCard
          label="Downtime Saved"
          value={`${overview.estimated_downtime_saved_hours.toLocaleString()}h`}
          sublabel="Estimated, this period"
          accent="teal"
        />
      </motion.div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2" padded={false}>
          <div className="flex items-center justify-between border-b border-ink-200/60 px-5 py-4">
            <div className="flex items-center gap-2">
              <TrendingDown size={16} className="text-status-critical" />
              <h2 className="text-sm font-semibold text-ink-900">Equipment Ranking — Most Critical First</h2>
            </div>
            <Link to="/inventory" className="text-xs font-medium text-clinical hover:underline">
              View all devices
            </Link>
          </div>
          <div className="divide-y divide-ink-200/60">
            {ranking.map((device) => (
              <Link
                key={device.id}
                to={`/devices/${device.id}`}
                className="flex items-center justify-between px-5 py-3 transition-colors hover:bg-canvas"
              >
                <div>
                  <p className="text-sm font-medium text-ink-900">{device.device_name}</p>
                  <p className="text-xs text-ink-400">{device.department}</p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="font-mono text-sm font-semibold tabular text-ink-900">
                      {(device.current_failure_probability * 100).toFixed(0)}%
                    </p>
                    {device.current_rul_days !== null && (
                      <p className="text-[11px] text-ink-400">{device.current_rul_days.toFixed(0)}d RUL</p>
                    )}
                  </div>
                  <StatusBadge status={device.status} size="sm" />
                </div>
              </Link>
            ))}
          </div>
        </Card>

        <Card padded={false}>
          <div className="flex items-center gap-2 border-b border-ink-200/60 px-5 py-4">
            <AlertTriangle size={16} className="text-status-warning" />
            <h2 className="text-sm font-semibold text-ink-900">Unacknowledged Alerts</h2>
          </div>
          <div className="divide-y divide-ink-200/60">
            {alerts.length === 0 && (
              <p className="px-5 py-8 text-center text-sm text-ink-400">No open alerts. All clear.</p>
            )}
            {alerts.map((alert) => (
              <div key={alert.id} className="px-5 py-3">
                <div className="mb-1 flex items-center gap-2">
                  <StatusBadge status={alert.severity} size="sm" />
                  <span className="text-[11px] text-ink-400">
                    {new Date(alert.created_at).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-xs text-ink-600">{alert.message}</p>
              </div>
            ))}
          </div>
          <div className="border-t border-ink-200/60 px-5 py-3">
            <Link to="/alerts" className="text-xs font-medium text-clinical hover:underline">
              View all alerts
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="flex h-64 items-center justify-center text-ink-400">
      <Activity className="animate-pulse" size={20} />
      <span className="ml-2 text-sm">Loading hospital-wide analytics...</span>
    </div>
  );
}
