import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useTrace(runId: string) {
  return useQuery({
    queryKey: ["trace", runId],
    queryFn: () => api.getRun(runId),
    enabled: !!runId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "running" || status === "pending" ? 2000 : false;
    },
    select: (data) => data.steps || [],
  });
}
