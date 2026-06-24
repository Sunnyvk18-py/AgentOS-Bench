import { NavLink } from "react-router-dom";
import { Activity, BarChart3, Cpu, FileText, Github } from "lucide-react";
import { cn } from "@/lib/utils";

const links = [
  { to: "/", label: "Dashboard", icon: Activity },
  { to: "/runs", label: "Eval Runs", icon: Cpu },
  { to: "/benchmark", label: "Benchmark", icon: BarChart3 },
  { to: "/reports", label: "Reports", icon: FileText },
];

export function Sidebar() {
  return (
    <aside className="flex h-screen w-64 flex-col border-r border-border bg-card">
      <div className="flex items-center gap-2 border-b border-border px-6 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/20 text-primary">
          <Cpu className="h-5 w-5" />
        </div>
        <div>
          <p className="text-sm font-semibold">AgentOS Bench</p>
          <p className="text-xs text-foreground/60">Eval & Observability</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 p-4">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all duration-200 ease-in-out",
                isActive
                  ? "bg-primary/15 text-primary"
                  : "text-foreground/70 hover:bg-border/50 hover:text-foreground"
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-border p-4">
        <a
          href="https://github.com/Sunnyvk18-py/AgentOS-Bench"
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-2 text-sm text-foreground/60 transition-all duration-200 hover:text-primary"
        >
          <Github className="h-4 w-4" />
          GitHub
        </a>
        <span className="mt-2 inline-block rounded-full bg-primary/15 px-2 py-0.5 text-xs font-mono text-primary">
          v1.0.0
        </span>
      </div>
    </aside>
  );
}
