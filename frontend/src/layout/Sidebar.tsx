import { NavLink } from "react-router-dom";
import clsx from "clsx";
import {
  LayoutDashboard, HardDrive, Activity, BarChart3, Bell, MessageSquare, ShieldCheck,
} from "lucide-react";

const NAV_ITEMS = [
  { to: "/", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/inventory", label: "Equipment Inventory", icon: HardDrive },
  { to: "/monitoring", label: "Live Monitoring", icon: Activity },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/alerts", label: "Alerts", icon: Bell },
  { to: "/assistant", label: "AI Assistant", icon: MessageSquare },
];

export function Sidebar() {
  return (
    <aside className="flex h-screen w-64 flex-col border-r border-ink-200/60 bg-surface">
      <div className="flex items-center gap-2.5 px-5 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-clinical text-white">
          <ShieldCheck size={20} strokeWidth={2.2} />
        </div>
        <div>
          <p className="text-sm font-bold leading-tight text-ink-900">MediGuard AI</p>
          <p className="text-[11px] leading-tight text-ink-400">Predictive Maintenance</p>
        </div>
      </div>

      <nav className="flex-1 space-y-0.5 px-3 py-2">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-clinical-light text-clinical-dark"
                  : "text-ink-600 hover:bg-canvas hover:text-ink-900"
              )
            }
          >
            <Icon size={18} strokeWidth={2} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-ink-200/60 px-5 py-4">
        <p className="text-[11px] font-medium text-ink-400">Signed in as</p>
        <p className="text-sm font-medium text-ink-900">Biomedical Engineering</p>
      </div>
    </aside>
  );
}
