import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { BenchmarkRequest } from "@/lib/types";

export function useBenchmarks() {
  return useQuery({
    queryKey: ["benchmarks"],
    queryFn: () => api.getBenchmarks(),
    refetchInterval: 3000,
  });
}

export function useBenchmark(id: string) {
  return useQuery({
    queryKey: ["benchmark", id],
    queryFn: () => api.getBenchmark(id),
    enabled: !!id,
  });
}

export function useCreateBenchmark() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: BenchmarkRequest) => api.createBenchmark(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["benchmarks"] }),
  });
}
