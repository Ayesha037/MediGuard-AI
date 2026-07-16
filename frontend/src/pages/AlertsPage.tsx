import { useEffect, useState } from "react";
import { CheckCircle2 } from "lucide-react";
import { Card } from "@/components/Card";
import { StatusBadge } from "@/components/StatusBadge";
import { api } from "@/api/client";
import type { AlertItem } from "@/types";

export function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [filter, setFilter] = useState<"all" | "open">("open");
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    api.alerts
      .list(filter === "open" ? { acknowledged: false } : undefined)
      .then(setAlerts)
      .finally(() => setLoading(false));
  }

  useEffect(load, [filter]);

  async function handleAcknowledge(id: number) {
    await api.alerts.acknowledge(id);
    load();
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <FilterTab label="Open" active={filter === "open"} onClick={() => setFilter("open")} />
        <FilterTab label="All" active={filter === "all"} onClick={() => setFilter("all")} />
      </div>

      <Card padded={false}>
        <div className="divide-y divide-ink-200/60">
          {loading && <p className="px-5 py-8 text-center text-sm text-ink-400">Loading alerts...</p>}
          {!loading && alerts.length === 0 && (
            <p className="px-5 py-12 text-center text-sm text-ink-400">No alerts to show. All clear.</p>
          )}
          {!loading && alerts.map((alert) => (
            <div key={alert.id} className="flex items-center justify-between px-5 py-4">
              <div className="flex items-start gap-3">
                <StatusBadge status={alert.severity} size="sm" />
                <div>
                  <p className="text-sm text-ink-900">{alert.message}</p>
                  <p className="mt-0.5 text-xs text-ink-400">
                    {alert.alert_type} · {new Date(alert.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
              {alert.acknowledged ? (
                <span className="flex items-center gap-1.5 text-xs text-ink-400">
                  <CheckCircle2 size={14} /> Acknowledged
                </span>
              ) : (
                <button
                  onClick={() => handleAcknowledge(alert.id)}
                  className="rounded-lg border border-clinical px-3 py-1.5 text-xs font-medium text-clinical transition-colors hover:bg-clinical-light"
                >
                  Acknowledge
                </button>
              )}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function FilterTab({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
        active ? "bg-clinical text-white" : "bg-surface text-ink-600 hover:bg-canvas"
      }`}
    >
      {label}
    </button>
  );
}
