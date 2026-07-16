import clsx from "clsx";
import type { ReactNode } from "react";

export function Card({
  children,
  className,
  padded = true,
}: {
  children: ReactNode;
  className?: string;
  padded?: boolean;
}) {
  return (
    <div
      className={clsx(
        "rounded-card border border-ink-200/60 bg-surface shadow-card",
        padded && "p-5",
        className
      )}
    >
      {children}
    </div>
  );
}

export function MetricCard({
  label,
  value,
  sublabel,
  accent = "clinical",
}: {
  label: string;
  value: ReactNode;
  sublabel?: string;
  accent?: "clinical" | "teal" | "healthy" | "warning" | "critical";
}) {
  const accentColor = {
    clinical: "text-clinical",
    teal: "text-teal",
    healthy: "text-status-healthy",
    warning: "text-status-warning",
    critical: "text-status-critical",
  }[accent];

  return (
    <Card>
      <p className="text-xs font-medium uppercase tracking-wide text-ink-400">{label}</p>
      <p className={clsx("mt-2 font-mono text-3xl font-semibold tabular", accentColor)}>{value}</p>
      {sublabel && <p className="mt-1 text-xs text-ink-400">{sublabel}</p>}
    </Card>
  );
}
