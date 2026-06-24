import { useCallback, useState } from "react";
import { AgentCard } from "@/components/agents/AgentCard";
import { api } from "@/lib/api";
import type { AgentValidateResult } from "@/lib/types";
import { Upload, X } from "lucide-react";

interface AgentUploadModalProps {
  open: boolean;
  onClose: () => void;
  onRegistered?: () => void;
}

export function AgentUploadModal({ open, onClose, onRegistered }: AgentUploadModalProps) {
  const [fileName, setFileName] = useState("");
  const [content, setContent] = useState("");
  const [validation, setValidation] = useState<AgentValidateResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reset = () => {
    setFileName("");
    setContent("");
    setValidation(null);
    setError(null);
    setToast(null);
  };

  const handleFile = useCallback(async (file: File) => {
    if (!file.name.endsWith(".py")) {
      setError("Only .py files are accepted.");
      return;
    }
    setFileName(file.name);
    setError(null);
    const text = await file.text();
    setContent(text);
    setLoading(true);
    try {
      const result = await api.validateAgent(text);
      setValidation(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Validation request failed");
      setValidation(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleRegister = async () => {
    if (!validation?.valid || !content || !fileName) return;
    setLoading(true);
    setError(null);
    try {
      await api.registerAgent(fileName, content);
      setToast("Agent registered successfully");
      onRegistered?.();
      setTimeout(() => {
        reset();
        onClose();
      }, 800);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-glow">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Upload Agent</h2>
          <button
            onClick={() => {
              reset();
              onClose();
            }}
            className="text-foreground/60 hover:text-foreground"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <label className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-border bg-background/50 px-6 py-10 transition-all duration-200 hover:border-primary/50">
          <Upload className="mb-2 h-8 w-8 text-primary" />
          <span className="text-sm text-foreground/70">Drag & drop a .py file or click to browse</span>
          <input
            type="file"
            accept=".py"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void handleFile(file);
            }}
          />
        </label>

        {fileName && <p className="mt-3 text-sm text-foreground/60">File: {fileName}</p>}

        {loading && <p className="mt-3 text-sm text-primary">Validating...</p>}

        {validation && (
          <div className="mt-4 space-y-3">
            {validation.valid ? (
              <>
                <p className="text-success">Valid agent plugin detected</p>
                {validation.agent_name && (
                  <AgentCard
                    name={validation.agent_name}
                    description={validation.description || ""}
                    configSchema={{}}
                    isBuiltIn={false}
                  />
                )}
                <button
                  onClick={handleRegister}
                  disabled={loading}
                  className="w-full rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:opacity-50"
                >
                  Add Agent
                </button>
              </>
            ) : (
              <div className="rounded-lg border border-error/40 bg-error/10 p-3 text-error">
                <p className="mb-2 font-medium">Validation errors:</p>
                <ul className="list-inside list-disc text-sm">
                  {validation.errors.map((err) => (
                    <li key={err}>{err}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {error && <p className="mt-3 text-sm text-error">{error}</p>}
        {toast && <p className="mt-3 text-sm text-success">{toast}</p>}

        <p className="mt-4 text-xs text-foreground/50">
          Your agent will be auto-discovered. No restart needed.
        </p>
      </div>
    </div>
  );
}
