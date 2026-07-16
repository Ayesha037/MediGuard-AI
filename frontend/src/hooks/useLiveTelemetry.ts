import { useEffect, useRef, useState } from "react";
import { WS_URL } from "@/api/client";
import type { LiveTelemetryTick } from "@/types";

/**
 * Subscribes to the backend's live telemetry WebSocket and keeps the most
 * recent tick per device in memory. Reconnects automatically with backoff
 * if the connection drops — dashboards shouldn't need a page refresh to
 * recover from a blip.
 */
export function useLiveTelemetry() {
  const [latestByDevice, setLatestByDevice] = useState<Record<string, LiveTelemetryTick>>({});
  const [connected, setConnected] = useState(false);
  const retryDelay = useRef(1000);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let closedByUs = false;
    let retryTimeout: ReturnType<typeof setTimeout>;

    function connect() {
      ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        setConnected(true);
        retryDelay.current = 1000;
      };

      ws.onmessage = (event) => {
        try {
          const tick: LiveTelemetryTick = JSON.parse(event.data);
          setLatestByDevice((prev) => ({ ...prev, [tick.device_id]: tick }));
        } catch {
          // ignore malformed frames
        }
      };

      ws.onclose = () => {
        setConnected(false);
        if (!closedByUs) {
          retryTimeout = setTimeout(connect, retryDelay.current);
          retryDelay.current = Math.min(retryDelay.current * 1.5, 15000);
        }
      };

      ws.onerror = () => {
        ws?.close();
      };
    }

    connect();

    return () => {
      closedByUs = true;
      clearTimeout(retryTimeout);
      ws?.close();
    };
  }, []);

  return { latestByDevice, connected };
}
