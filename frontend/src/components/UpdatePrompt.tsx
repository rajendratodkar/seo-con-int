import { useEffect, useState } from "react";
import { checkUpdates, installUpdate, isDesktop } from "../services/desktop";
import { track } from "../services/telemetry";

/** Auto-update banner: checks the release endpoint on startup, prompts to restart. */
export function UpdatePrompt() {
  const [update, setUpdate] = useState<{ version: string; notes: string | null } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isDesktop()) return;
    checkUpdates().then((info) => {
      if (info?.available) setUpdate({ version: info.version ?? "new", notes: info.notes });
    });
  }, []);

  if (!update) return null;

  return (
    <div className="card" style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
      <span>
        🚀 Update <strong>v{update.version}</strong> is available{update.notes ? ` — ${update.notes}` : ""}.
      </span>
      <button
        disabled={busy}
        onClick={async () => {
          setBusy(true);
          setError(null);
          track("action", "install_update");
          try {
            await installUpdate();
          } catch (err) {
            setError(err instanceof Error ? err.message : String(err));
            setBusy(false);
          }
        }}
      >
        {busy ? "Installing…" : "Install & Restart"}
      </button>
      <button onClick={() => setUpdate(null)}>Later</button>
      {error && <span style={{ color: "#c0392b" }}>{error}</span>}
    </div>
  );
}
