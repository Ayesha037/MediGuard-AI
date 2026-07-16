import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { Sidebar } from "@/layout/Sidebar";
import { Topbar } from "@/layout/Topbar";
import { OverviewPage } from "@/pages/OverviewPage";
import { InventoryPage } from "@/pages/InventoryPage";
import { DigitalTwinPage } from "@/pages/DigitalTwinPage";
import { MonitoringPage } from "@/pages/MonitoringPage";
import { AnalyticsPage } from "@/pages/AnalyticsPage";
import { AlertsPage } from "@/pages/AlertsPage";
import { AssistantPage } from "@/pages/AssistantPage";

const PAGE_TITLES: Record<string, { title: string; subtitle?: string }> = {
  "/": { title: "Overview", subtitle: "Hospital-wide equipment health at a glance" },
  "/inventory": { title: "Equipment Inventory", subtitle: "All registered medical devices" },
  "/monitoring": { title: "Live Monitoring", subtitle: "Real-time sensor telemetry" },
  "/analytics": { title: "Analytics", subtitle: "Trends across departments and manufacturers" },
  "/alerts": { title: "Alerts", subtitle: "Smart alerts requiring attention" },
  "/assistant": { title: "AI Assistant", subtitle: "Ask questions about your equipment" },
};

function AppShell() {
  const location = useLocation();
  const isDeviceDetail = location.pathname.startsWith("/devices/");
  const meta = PAGE_TITLES[location.pathname] ?? { title: "Digital Twin" };

  return (
    <div className="flex h-screen bg-canvas">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        {!isDeviceDetail && <Topbar title={meta.title} subtitle={meta.subtitle} />}
        <main className="flex-1 overflow-y-auto px-8 py-6">
          <Routes>
            <Route path="/" element={<OverviewPage />} />
            <Route path="/inventory" element={<InventoryPage />} />
            <Route path="/devices/:deviceId" element={<DigitalTwinPage />} />
            <Route path="/monitoring" element={<MonitoringPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/alerts" element={<AlertsPage />} />
            <Route path="/assistant" element={<AssistantPage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  );
}
