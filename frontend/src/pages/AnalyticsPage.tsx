import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend,
} from "recharts";
import { Card } from "@/components/Card";
import { api } from "@/api/client";
import type { FailureTrendPoint, DepartmentHealth, ManufacturerComparison } from "@/types";

export function AnalyticsPage() {
  const [trends, setTrends] = useState<FailureTrendPoint[]>([]);
  const [departments, setDepartments] = useState<DepartmentHealth[]>([]);
  const [manufacturers, setManufacturers] = useState<ManufacturerComparison[]>([]);

  useEffect(() => {
    api.analytics.failureTrends().then(setTrends);
    api.analytics.departmentHealth().then(setDepartments);
    api.analytics.manufacturerComparison().then(setManufacturers);
  }, []);

  return (
    <div className="space-y-6">
      <Card>
        <h2 className="mb-4 text-sm font-semibold text-ink-900">Monthly Failure Trends</h2>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={trends}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
            <XAxis dataKey="month" tick={{ fontSize: 11, fill: "#64748B" }} />
            <YAxis tick={{ fontSize: 11, fill: "#64748B" }} />
            <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #E2E8F0" }} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line type="monotone" dataKey="failure_count" stroke="#DC2626" strokeWidth={2} name="Failures" dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <h2 className="mb-4 text-sm font-semibold text-ink-900">Department-Wise Device Health</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={departments} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis type="number" tick={{ fontSize: 11, fill: "#64748B" }} />
              <YAxis type="category" dataKey="department" width={100} tick={{ fontSize: 11, fill: "#64748B" }} />
              <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #E2E8F0" }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="healthy_count" stackId="a" fill="#059669" name="Healthy" />
              <Bar dataKey="warning_count" stackId="a" fill="#D97706" name="Warning" />
              <Bar dataKey="critical_count" stackId="a" fill="#DC2626" name="Critical" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h2 className="mb-4 text-sm font-semibold text-ink-900">Manufacturer Comparison</h2>
          <p className="mb-2 text-xs text-ink-400">Average failure probability, by manufacturer</p>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={manufacturers} margin={{ bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="manufacturer" angle={-30} textAnchor="end" interval={0} tick={{ fontSize: 10, fill: "#64748B" }} />
              <YAxis tick={{ fontSize: 11, fill: "#64748B" }} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
              <Tooltip
                contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #E2E8F0" }}
                formatter={(v: number) => `${(v * 100).toFixed(1)}%`}
              />
              <Bar dataKey="average_failure_probability" fill="#0A5C7A" radius={[4, 4, 0, 0]} name="Avg. Failure Probability" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </div>
  );
}
