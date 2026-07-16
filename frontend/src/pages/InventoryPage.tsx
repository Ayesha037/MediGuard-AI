import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Search } from "lucide-react";
import { Card } from "@/components/Card";
import { StatusBadge } from "@/components/StatusBadge";
import { api } from "@/api/client";
import type { DeviceSummary, DeviceType, DeviceStatus } from "@/types";

const DEVICE_TYPES: DeviceType[] = ["Ventilator", "MRI Scanner", "Infusion Pump", "Patient Monitor"];
const STATUSES: DeviceStatus[] = ["Healthy", "Warning", "Critical"];

export function InventoryPage() {
  const [devices, setDevices] = useState<DeviceSummary[]>([]);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.devices
      .list({
        device_type: typeFilter || undefined,
        status: statusFilter || undefined,
      })
      .then(setDevices)
      .finally(() => setLoading(false));
  }, [typeFilter, statusFilter]);

  const filtered = devices.filter((d) =>
    d.device_name.toLowerCase().includes(search.toLowerCase()) ||
    d.department.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-4">
      <Card padded={false}>
        <div className="flex flex-wrap items-center gap-3 border-b border-ink-200/60 px-5 py-4">
          <div className="relative flex-1 min-w-[200px]">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-400" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by device name or department..."
              className="w-full rounded-lg border border-ink-200/60 bg-canvas py-2 pl-9 pr-3 text-sm text-ink-900 placeholder:text-ink-400 focus:border-clinical focus:outline-none focus:ring-1 focus:ring-clinical"
            />
          </div>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="rounded-lg border border-ink-200/60 bg-canvas px-3 py-2 text-sm text-ink-900 focus:border-clinical focus:outline-none"
          >
            <option value="">All Device Types</option>
            {DEVICE_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-ink-200/60 bg-canvas px-3 py-2 text-sm text-ink-900 focus:border-clinical focus:outline-none"
          >
            <option value="">All Statuses</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-ink-200/60 text-xs uppercase tracking-wide text-ink-400">
              <th className="px-5 py-3 font-medium">Device</th>
              <th className="px-5 py-3 font-medium">Type</th>
              <th className="px-5 py-3 font-medium">Department</th>
              <th className="px-5 py-3 font-medium">Status</th>
              <th className="px-5 py-3 font-medium text-right">Failure Probability</th>
              <th className="px-5 py-3 font-medium text-right">Est. RUL</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-200/60">
            {!loading && filtered.map((device) => (
              <tr key={device.id} className="transition-colors hover:bg-canvas">
                <td className="px-5 py-3">
                  <Link to={`/devices/${device.id}`} className="font-medium text-ink-900 hover:text-clinical">
                    {device.device_name}
                  </Link>
                </td>
                <td className="px-5 py-3 text-ink-600">{device.device_type}</td>
                <td className="px-5 py-3 text-ink-600">{device.department}</td>
                <td className="px-5 py-3">
                  <StatusBadge status={device.status} size="sm" />
                </td>
                <td className="px-5 py-3 text-right font-mono tabular text-ink-900">
                  {(device.current_failure_probability * 100).toFixed(0)}%
                </td>
                <td className="px-5 py-3 text-right font-mono tabular text-ink-600">
                  {device.current_rul_days !== null ? `${device.current_rul_days.toFixed(0)}d` : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {loading && <p className="px-5 py-8 text-center text-sm text-ink-400">Loading inventory...</p>}
        {!loading && filtered.length === 0 && (
          <p className="px-5 py-8 text-center text-sm text-ink-400">No devices match your filters.</p>
        )}
      </Card>
      <p className="text-xs text-ink-400">{filtered.length} of {devices.length} devices shown</p>
    </div>
  );
}
