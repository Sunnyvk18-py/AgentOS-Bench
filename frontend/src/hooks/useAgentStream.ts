import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { AgentInfo } from "@/lib/types";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function useAgentsLive() {
  const queryClient = useQueryClient();
  const [newAgents, setNewAgents] = useState<Set<string>>(new Set());

  const query = useQuery({
    queryKey: ["agents"],
    queryFn: () => api.getAgents(),
  });

  useEffect(() => {
    const source = new EventSource(`${API_BASE}/api/agents/stream`);

    source.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as {
          event: string;
          payload: { agents?: AgentInfo[]; name?: string };
        };

        if (data.event === "snapshot" && data.payload.agents) {
          queryClient.setQueryData(["agents"], data.payload.agents);
          return;
        }

        if (data.event === "agent_registered" && data.payload.name) {
          setNewAgents((prev) => new Set(prev).add(data.payload.name!));
          setTimeout(() => {
            setNewAgents((prev) => {
              const next = new Set(prev);
              next.delete(data.payload.name!);
              return next;
            });
          }, 3000);
          void queryClient.invalidateQueries({ queryKey: ["agents"] });
        }

        if (data.event === "agent_removed") {
          void queryClient.invalidateQueries({ queryKey: ["agents"] });
        }
      } catch {
        // ignore malformed SSE payloads
      }
    };

    return () => {
      source.close();
    };
  }, [queryClient]);

  return { ...query, newAgents };
}
