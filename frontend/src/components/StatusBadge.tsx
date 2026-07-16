import clsx from "clsx";
import type { DeviceStatus, AlertSeverity, RiskLevel } from "@/types";

const STATUS_STYLES: Record<string, string> = {
  Healthy: "bg-status-healthyBg text-status-healthy",
  Low: "bg-status-healthyBg text-status-healthy",
  Warning: "bg-status-warningBg text-status-warning",
  Medium: "bg-status-warningBg text-status-warning",
  Critical: "bg-status-criticalBg text-status-critical",
  High: "bg-status-criticalBg text-status-critical",
  Offline: "bg-status-offlineBg text-status-offline",
  "Under Maintenance": "bg-clinical-light text-clinical-dark",
  Info: "bg-clinical-light text-clinical-dark",
};

const DOT_STYLES: Record<string, string> = {
  Healthy: "bg-status-healthy",
  Low: "bg-status-healthy",
  Warning: "bg-status-warning",
  Medium: "bg-status-warning",
  Critical: "bg-status-critical",
  High: "bg-status-critical",
  Offline: "bg-status-offline",
  "Under Maintenance": "bg-clinical",
  Info: "bg-clinical",
};

export function StatusBadge({
  status,
  size = "md",
}: {
  status: DeviceStatus | AlertSeverity | RiskLevel | string;
  size?: "sm" | "md";
}) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full font-medium",
        size === "sm" ? "px-2 py-0.5 text-[11px]" : "px-2.5 py-1 text-xs",
        STATUS_STYLES[status] ?? "bg-ink-200/40 text-ink-600"
      )}
    >
      <span className={clsx("h-1.5 w-1.5 rounded-full", DOT_STYLES[status] ?? "bg-ink-400")} />
      {status}
    </span>
  );
}
