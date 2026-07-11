import { useEffect, useRef, useState } from 'react';

interface SSEEventData {
  node_start: { node_id: string; node_type: string };
  node_done: { node_id: string; output: unknown };
  node_error: { node_id: string; error: string };
  workflow_done: { output: unknown };
}

export interface SSECallbacks {
  node_start?: (data: SSEEventData['node_start']) => void;
  node_done?: (data: SSEEventData['node_done']) => void;
  node_error?: (data: SSEEventData['node_error']) => void;
  workflow_done?: (data: SSEEventData['workflow_done']) => void;
}

/**
 * SSE (Server-Sent Events) hook for real-time workflow execution monitoring.
 *
 * Connects to /api/workflows/:workflowId/run/sse when workflowId is set and enabled.
 * Supports four event types: node_start, node_done, node_error, workflow_done.
 */
export function useSSE(
  workflowId: string | null,
  options?: { enabled?: boolean; onEvent?: SSECallbacks }
) {
  const { enabled = true, onEvent } = options || {};
  const esRef = useRef<EventSource | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<{
    type: string;
    data: unknown;
  } | null>(null);

  // Keep callback ref to avoid reconnecting on callback identity change
  const cbRef = useRef(onEvent);
  cbRef.current = onEvent;

  useEffect(() => {
    if (!workflowId || !enabled) return;

    const es = new EventSource(`/api/workflows/${workflowId}/run/sse`);
    esRef.current = es;

    es.onopen = () => {
      setIsConnected(true);
    };

    es.addEventListener('node_start', (e: MessageEvent) => {
      const data = JSON.parse(e.data) as SSEEventData['node_start'];
      setLastEvent({ type: 'node_start', data });
      cbRef.current?.node_start?.(data);
    });

    es.addEventListener('node_done', (e: MessageEvent) => {
      const data = JSON.parse(e.data) as SSEEventData['node_done'];
      setLastEvent({ type: 'node_done', data });
      cbRef.current?.node_done?.(data);
    });

    es.addEventListener('node_error', (e: MessageEvent) => {
      const data = JSON.parse(e.data) as SSEEventData['node_error'];
      setLastEvent({ type: 'node_error', data });
      cbRef.current?.node_error?.(data);
    });

    es.addEventListener('workflow_done', (e: MessageEvent) => {
      const data = JSON.parse(e.data) as SSEEventData['workflow_done'];
      setLastEvent({ type: 'workflow_done', data });
      cbRef.current?.workflow_done?.(data);
    });

    es.onerror = () => {
      setIsConnected(false);
    };

    return () => {
      es.close();
      esRef.current = null;
      setIsConnected(false);
    };
  }, [workflowId, enabled]);

  return { isConnected, lastEvent };
}
