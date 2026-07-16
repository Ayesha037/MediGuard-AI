import { useEffect, useState } from "react";
import clsx from "clsx";
import { Thermometer, Wind, Battery, Zap, Wifi, WifiOff } from "lucide-react";
import { useLiveTelemetry } from "@/hooks/useLiveTelemetry";
import { api } from "@/api/client";
import type { DeviceSummary } from "@/types";
import { Card } from "@/components/Card";

/**
 * Signature element: sensor values rendered as an instrument-panel readout
 * (dark panel, monospace glowing digits) — visually distinct from the rest
 * of the clean enterprise dashboard, echoing an actual medical monitor.
 */
function ReadoutPanel({
  deviceName,
  connected,
  tick,
}: {
  deviceName: string;
  connected: boolean;
  tick?: {
    temperature: number; vibration: number; battery_health: number;
    voltage: number; recorded_at: string; network_status: boolean;
  };
}) {
  const stale = !tick;
  return (
    <div className="overflow-hidden rounded-card bg-ink-900 shadow-elevated">
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-2.5">
        <p className="truncate text-sm font-medium text-white/90">{deviceName}</p>
        {tick?.network_status === false ? (
          <WifiOff size={13} className="text-status-critical" />
        ) : (
          <Wifi size={13} className={connected ? "text-status-healthy" : "text-white/30"} />
        )}
      </div>
      <div className="grid grid-cols-2 gap-px bg-white/10">
        <Readout icon={Thermometer} label="TEMP °C" value={tick?.temperature} stale={stale} warn={tick && tick.temperature > 42} />
        <Readout icon={Wind} label="VIBRATION" value={tick?.vibration} stale={stale} warn={tick && tick.vibration > 55} />
        <Readout icon={Battery} label="BATTERY %" value={tick?.battery_health} stale={stale} warn={tick && tick.battery_health < 25} />
        <Readout icon={Zap} label="VOLTAGE" value={tick?.voltage} stale={stale} />
      </div>
    </div>
  );
}

function Readout({
  icon: Icon, label, value, stale, warn,
}: {
  icon: typeof Thermometer; label: string; value?: number; stale?: boolean; warn?: boolean;
}) {
  return (
    <div className="bg-ink-900 px-4 py-3">
      <div className="mb-1 flex items-center gap-1.5 text-[10px] font-medium tracking-wide text-white/40">
        <Icon size={11} /> {label}
      </div>
      <p
        className={clsx(
          "font-mono text-xl font-semibold tabular",
          stale ? "text-white/20" : warn ? "text-status-critical" : "text-status-healthy"
        )}
      >
        {stale ? "—.—" : value?.toFixed(1)}
      </p>
    </div>
  );
}

export function MonitoringPage() {
  const { latestByDevice, connected } = useLiveTelemetry();
  const [devices, setDevices] = useState<DeviceSummary[]>([]);

  useEffect(() => {
    api.devices.list({}).then((all) => setDevices(all.slice(0, 12)));
  }, []);

  return (
    <div className="space-y-4">
      <Card className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-ink-900">Real-Time IoT Feed</p>
          <p className="text-xs text-ink-400">
            Streaming from {Object.keys(latestByDevice).length} devices · updates every few seconds
          </p>
        </div>
        <div
          className={clsx(
            "flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium",
            connected ? "bg-status-healthyBg text-status-healthy" : "bg-status-offlineBg text-status-offline"
          )}
        >
          {connected ? <Wifi size={14} /> : <WifiOff size={14} />}
          {connected ? "Connected" : "Reconnecting..."}
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {devices.map((device) => (
          <ReadoutPanel
            key={device.id}
            deviceName={device.device_name}
            connected={connected}
            tick={latestByDevice[device.id]}
          />
        ))}
      </div>
    </div>
  );
}
