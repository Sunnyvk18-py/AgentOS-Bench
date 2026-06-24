import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { EvalRunCreate } from "@/lib/types";

export function useRuns(params?: { page?: number; page_size?: number; status?: string }) {
  return useQuery({
    queryKey: ["runs", params],
    queryFn: () => api.getRuns(params),
    refetchInterval: (query) => {
      const items = query.state.data?.items || [];
      const hasRunning = items.some((r) => r.status === "running" || r.status === "pending");
      return hasRunning ? 2000 : false;
    },
  });
}

export function useRun(id: string) {
  return useQuery({
    queryKey: ["run", id],
    queryFn: () => api.getRun(id),
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "running" || status === "pending" ? 2000 : false;
    },
  });
}

export function useCreateRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: EvalRunCreate) => api.createRun(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["runs"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
  });
}

export function useDeleteRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteRun(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["runs"] }),
  });
}

export function useStats() {
  return useQuery({
    queryKey: ["stats"],
    queryFn: () => api.getStats(),
    refetchInterval: 5000,
  });
}
