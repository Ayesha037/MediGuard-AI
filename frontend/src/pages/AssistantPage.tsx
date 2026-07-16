import { useState, useRef, useEffect } from "react";
import { Send, Bot, User } from "lucide-react";
import { Card } from "@/components/Card";
import { api } from "@/api/client";

interface Message {
  role: "user" | "assistant";
  text: string;
}

const SUGGESTIONS = [
  "Which equipment requires maintenance this week?",
  "Show critical devices",
  "Explain today's alerts",
  "Which department has the most critical devices?",
];

/**
 * Rule-based assistant (spec feature #9): parses the question against
 * known intents and answers from live API data. This is intentionally
 * NOT a wrapper around a general LLM — every answer is grounded in an
 * actual API call, so it can't hallucinate a device that doesn't exist.
 * A future iteration could route unmatched questions to a real LLM with
 * these same API calls as tools.
 */
async function answerQuestion(question: string): Promise<string> {
  const q = question.toLowerCase();

  // "Why is <device> high risk / at risk?"
  if (q.includes("why") && (q.includes("risk") || q.includes("critical") || q.includes("fail"))) {
    const devices = await api.devices.list({});
    const match = devices.find((d) => q.includes(d.device_name.toLowerCase().split(" - ")[0].toLowerCase()));
    if (match) {
      const twin = await api.digitalTwin.get(match.id, 24);
      const latest = twin.prediction_history[twin.prediction_history.length - 1];
      if (!latest) return `${match.device_name} has no prediction history yet.`;
      const reasons = latest.shap_explanations.slice(0, 3).map((r) => `• ${r.explanation}`).join("\n");
      return `${match.device_name} is at ${latest.risk_level} risk (${(latest.failure_probability * 100).toFixed(0)}% failure probability). Top reasons:\n${reasons}`;
    }
    return "I couldn't match that to a specific device — try naming it like 'Ventilator - 023'.";
  }

  // "Which equipment requires maintenance this week?"
  if (q.includes("maintenance") && (q.includes("week") || q.includes("require") || q.includes("due"))) {
    const devices = await api.devices.list({});
    const critical = devices.filter((d) => d.status === "Critical" || d.status === "Warning").slice(0, 8);
    if (critical.length === 0) return "No equipment currently requires maintenance this week.";
    return `${critical.length} devices likely need attention this week:\n${critical
      .map((d) => `• ${d.device_name} (${d.department}) — ${(d.current_failure_probability * 100).toFixed(0)}% failure probability`)
      .join("\n")}`;
  }

  // "Show MRI machines with abnormal vibration" / general device-type + status queries
  if (q.includes("mri") || q.includes("ventilator") || q.includes("infusion") || q.includes("patient monitor")) {
    const typeMap: Record<string, string> = {
      mri: "MRI Scanner", ventilator: "Ventilator", infusion: "Infusion Pump", "patient monitor": "Patient Monitor",
    };
    const typeKey = Object.keys(typeMap).find((k) => q.includes(k));
    const deviceType = typeKey ? typeMap[typeKey] : undefined;
    const devices = await api.devices.list({ device_type: deviceType });
    const atRisk = devices.filter((d) => d.status !== "Healthy");
    if (atRisk.length === 0) return `All ${deviceType ?? "matching"} devices are currently healthy.`;
    return `${atRisk.length} ${deviceType ?? "matching"} device(s) showing issues:\n${atRisk
      .map((d) => `• ${d.device_name} — ${d.status} (${(d.current_failure_probability * 100).toFixed(0)}%)`)
      .join("\n")}`;
  }

  // "Explain today's alerts"
  if (q.includes("alert")) {
    const alerts = await api.alerts.list({ acknowledged: false });
    if (alerts.length === 0) return "No open alerts right now — all clear.";
    return `${alerts.length} open alert(s):\n${alerts
      .slice(0, 8)
      .map((a) => `• [${a.severity}] ${a.message}`)
      .join("\n")}`;
  }

  // "Which department has the most critical devices?"
  if (q.includes("department")) {
    const depts = await api.analytics.departmentHealth();
    const sorted = [...depts].sort((a, b) => b.critical_count - a.critical_count);
    const top = sorted[0];
    if (!top || top.critical_count === 0) return "No department currently has critical devices.";
    return `${top.department} has the most critical devices (${top.critical_count} critical, ${top.warning_count} warning, out of ${top.total_devices} total).`;
  }

  if (q.includes("critical")) {
    const devices = await api.devices.list({ status: "Critical" });
    if (devices.length === 0) return "No devices are currently in critical status.";
    return `${devices.length} critical device(s):\n${devices
      .map((d) => `• ${d.device_name} (${d.department}) — ${(d.current_failure_probability * 100).toFixed(0)}% failure probability`)
      .join("\n")}`;
  }

  return "I can answer questions about equipment risk, maintenance needs, alerts, and department health. Try one of the suggestions below, or ask about a specific device by name.";
}

export function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", text: "Ask me about equipment risk, maintenance needs, or today's alerts." },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function send(text: string) {
    if (!text.trim() || busy) return;
    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");
    setBusy(true);
    try {
      const answer = await answerQuestion(text);
      setMessages((m) => [...m, { role: "assistant", text: answer }]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", text: "Something went wrong fetching that data. Try again." }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-140px)] max-w-3xl flex-col">
      <Card className="flex flex-1 flex-col" padded={false}>
        <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto px-5 py-5">
          {messages.map((m, i) => (
            <div key={i} className={`flex gap-3 ${m.role === "user" ? "flex-row-reverse" : ""}`}>
              <div
                className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full ${
                  m.role === "user" ? "bg-clinical text-white" : "bg-teal-light text-clinical-dark"
                }`}
              >
                {m.role === "user" ? <User size={15} /> : <Bot size={15} />}
              </div>
              <div
                className={`max-w-[75%] whitespace-pre-line rounded-2xl px-4 py-2.5 text-sm ${
                  m.role === "user" ? "bg-clinical text-white" : "bg-canvas text-ink-900"
                }`}
              >
                {m.text}
              </div>
            </div>
          ))}
          {busy && <p className="text-xs text-ink-400">Thinking...</p>}
        </div>

        <div className="border-t border-ink-200/60 px-5 py-3">
          <div className="mb-2 flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => send(s)}
                className="rounded-full border border-ink-200/60 px-3 py-1 text-xs text-ink-600 hover:border-clinical hover:text-clinical"
              >
                {s}
              </button>
            ))}
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              send(input);
            }}
            className="flex gap-2"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about equipment risk, maintenance, or alerts..."
              className="flex-1 rounded-lg border border-ink-200/60 bg-canvas px-3 py-2 text-sm focus:border-clinical focus:outline-none focus:ring-1 focus:ring-clinical"
            />
            <button
              type="submit"
              className="flex items-center justify-center rounded-lg bg-clinical px-4 py-2 text-white transition-colors hover:bg-clinical-dark"
            >
              <Send size={16} />
            </button>
          </form>
        </div>
      </Card>
    </div>
  );
}
