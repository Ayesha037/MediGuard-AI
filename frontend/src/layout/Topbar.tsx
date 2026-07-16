import { Wifi, WifiOff } from "lucide-react";

export function Topbar({ title, subtitle, connected }: { title: string; subtitle?: string; connected?: boolean }) {
  return (
    <header className="flex items-center justify-between border-b border-ink-200/60 bg-surface px-8 py-5">
      <div>
        <h1 className="text-xl font-semibold text-ink-900">{title}</h1>
        {subtitle && <p className="mt-0.5 text-sm text-ink-400">{subtitle}</p>}
      </div>
      {connected !== undefined && (
        <div
          className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium ${
            connected ? "bg-status-healthyBg text-status-healthy" : "bg-status-offlineBg text-status-offline"
          }`}
        >
          {connected ? <Wifi size={14} /> : <WifiOff size={14} />}
          {connected ? "Live feed connected" : "Reconnecting..."}
        </div>
      )}
    </header>
  );
}
