import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useAgents() {
  return useQuery({
    queryKey: ["agents"],
    queryFn: () => api.getAgents(),
  });
}

export function useExportReport() {
  return useMutation({
    mutationFn: ({ runId, format }: { runId: string; format: "json" | "markdown" }) =>
      api.exportReport(runId, format),
  });
}

export function useRunsList() {
  return useQuery({
    queryKey: ["runs-list"],
    queryFn: () => api.getRuns({ page_size: 100 }),
  });
}
