import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "@/components/layout/Layout";
import DashboardPage from "@/routes/index";
import RunsPage from "@/routes/runs/index";
import RunDetailPage from "@/routes/runs/[id]";
import BenchmarkPage from "@/routes/benchmark/index";
import ReportsPage from "@/routes/reports/index";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="runs" element={<RunsPage />} />
          <Route path="runs/:id" element={<RunDetailPage />} />
          <Route path="benchmark" element={<BenchmarkPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
