import { useCallback, useState } from "react";
import { contentRefresh as api } from "../services/backend";
import { useWebsiteStore } from "../stores/websiteStore";
import { Badge, Empty, ErrorBox, Loading } from "../components/common";
import { useAsync } from "../hooks/useAsync";
import type { RefreshRule, RefreshSchedule, RefreshHistory, RefreshStats } from "../services/backend";

/* ------------------------------------------------------------------ */
/*  Main page                                                          */
/* ------------------------------------------------------------------ */

export default function ContentRefresh() {
  const { active } = useWebsiteStore();
  const [tab, setTab] = useState<"queue" | "rules" | "history">("queue");
  const [scanResult, setScanResult] = useState<{ pages_scanned: number; stale_pages_found: number; schedules_created: number } | null>(null);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const stats = useAsync(() => (active ? api.stats(active.id) : Promise.resolve(null)), [active?.id]);
  const schedules = useAsync(() => (active ? api.listSchedules(active.id) : Promise.resolve([])), [active?.id]);
  const rules = useAsync(() => (active ? api.listRules(active.id) : Promise.resolve([])), [active?.id]);
  const history = useAsync(() => (active ? api.history(active.id) : Promise.resolve([])), [active?.id]);

  const runScan = useCallback(async () => {
    if (!active) return;
    setScanning(true);
    setError(null);
    try {
      const result = await api.scan(active.id);
      setScanResult(result);
      await Promise.all([schedules.reload(), stats.reload()]);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
    setScanning(false);
  }, [active, schedules, stats]);

  const refreshAll = useCallback(async () => {
    await Promise.all([schedules.reload(), stats.reload(), rules.reload(), history.reload()]);
  }, [schedules, stats, rules, history]);

  if (!active) return <Empty text="Add a website first." />;

  const s = stats.data as RefreshStats | null;

  return (
    <>
      <h2 className="page-title">Content Refresh</h2>
      <p className="page-sub">
        Detect stale content, prioritize pages to refresh, and track refresh impact on SEO metrics.
      </p>

      {error && <ErrorBox message={error} />}

      {/* Stats cards */}
      <div style={{ display: "flex", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
        <StatCard label="Pending" value={s?.pending ?? 0} color="var(--warning)" />
        <StatCard label="In Progress" value={s?.in_progress ?? 0} color="var(--primary)" />
        <StatCard label="Completed" value={s?.completed ?? 0} color="var(--green)" />
        <StatCard label="Skipped" value={s?.skipped ?? 0} color="var(--text-muted)" />
        <StatCard label="Avg Priority" value={s ? Math.round(s.avg_priority) : 0} color="var(--primary)" />
      </div>

      {/* Scan button */}
      <div className="card" style={{ marginBottom: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <strong>Staleness Scan</strong>
          <span style={{ marginLeft: 8, color: "var(--text-muted)", fontSize: 13 }}>
            Detects stale pages and creates refresh schedules
          </span>
        </div>
        <button className="btn btn-primary" onClick={runScan} disabled={scanning}>
          {scanning ? "Scanning…" : "Run Scan"}
        </button>
      </div>

      {scanResult && (
        <div className="card" style={{ marginBottom: 16, borderColor: "var(--green)" }}>
          Scan complete: {scanResult.pages_scanned} pages scanned, {scanResult.stale_pages_found} stale, {scanResult.schedules_created} schedules created.
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: "flex", gap: 4, marginBottom: 12, borderBottom: "1px solid var(--border)", paddingBottom: 8 }}>
        {(["queue", "rules", "history"] as const).map((t) => (
          <button key={t} className={`btn ${tab === t ? "btn-primary" : ""}`} onClick={() => setTab(t)} style={{ fontSize: 13 }}>
            {t === "queue" ? `Refresh Queue (${schedules.data?.length ?? 0})` : t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === "queue" && (
        <RefreshQueue schedules={schedules} onRefresh={refreshAll} />
      )}
      {tab === "rules" && (
        <RulesTab rules={rules} onRefresh={refreshAll} />
      )}
      {tab === "history" && (
        <HistoryTab history={history} />
      )}
    </>
  );
}

/* ------------------------------------------------------------------ */
/*  Stat card                                                           */
/* ------------------------------------------------------------------ */

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="card" style={{ flex: "1 1 120px", textAlign: "center", padding: 12 }}>
      <div style={{ fontSize: 24, fontWeight: 700, color }}>{value}</div>
      <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{label}</div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Refresh Queue                                                       */
/* ------------------------------------------------------------------ */

function RefreshQueue({
  schedules,
  onRefresh,
}: {
  schedules: ReturnType<typeof useAsync>;
  onRefresh: () => void;
}) {
  const [statusFilter, setStatusFilter] = useState<string>("pending");

  const filtered = ((schedules.data as RefreshSchedule[]) ?? []).filter(
    (s) => statusFilter === "all" || s.status === statusFilter
  );

  const updateStatus = useCallback(async (id: number, status: string) => {
    await api.updateStatus(id, status);
    await onRefresh();
  }, [onRefresh]);

  const skip = useCallback(async (id: number) => {
    await api.skip(id);
    await onRefresh();
  }, [onRefresh]);

  const remove = useCallback(async (id: number) => {
    await api.deleteSchedule(id);
    await onRefresh();
  }, [onRefresh]);

  if (schedules.loading) return <Loading />;

  return (
    <div className="card">
      {/* Status filter */}
      <div style={{ display: "flex", gap: 4, marginBottom: 12 }}>
        {["pending", "in_progress", "completed", "skipped", "all"].map((s) => (
          <button
            key={s}
            className={`btn ${statusFilter === s ? "btn-primary" : ""}`}
            onClick={() => setStatusFilter(s)}
            style={{ fontSize: 12 }}
          >
            {s}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <Empty text="No schedules in this status." />
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: "2px solid var(--border)" }}>
              <th style={{ textAlign: "left", padding: 8 }}>Page</th>
              <th style={{ textAlign: "right", padding: 8 }}>Score</th>
              <th style={{ textAlign: "left", padding: 8 }}>Priority Date</th>
              <th style={{ textAlign: "left", padding: 8 }}>Status</th>
              <th style={{ textAlign: "left", padding: 8 }}>Reason</th>
              <th style={{ textAlign: "right", padding: 8 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((s) => (
              <tr key={s.id} style={{ borderBottom: "1px solid var(--border)" }}>
                <td style={{ padding: 8, maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  Page #{s.page_id}
                </td>
                <td style={{ padding: 8, textAlign: "right", fontWeight: 600, color: s.priority_score >= 60 ? "var(--danger)" : s.priority_score >= 30 ? "var(--warning)" : "var(--text-muted)" }}>
                  {s.priority_score}
                </td>
                <td style={{ padding: 8, fontSize: 12 }}>{s.priority_date ?? "—"}</td>
                <td style={{ padding: 8 }}><Badge value={s.status} /></td>
                <td style={{ padding: 8, fontSize: 12, maxWidth: 250, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {s.reason ?? "—"}
                </td>
                <td style={{ padding: 8, textAlign: "right" }}>
                  {s.status === "pending" && (
                    <>
                      <button className="btn" style={{ fontSize: 11, marginRight: 4 }} onClick={() => updateStatus(s.id, "in_progress")}>Start</button>
                      <button className="btn" style={{ fontSize: 11, marginRight: 4 }} onClick={() => skip(s.id)}>Skip</button>
                    </>
                  )}
                  {s.status === "in_progress" && (
                    <button className="btn btn-primary" style={{ fontSize: 11, marginRight: 4 }} onClick={() => updateStatus(s.id, "completed")}>Done</button>
                  )}
                  <button className="btn" style={{ fontSize: 11, color: "var(--danger)" }} onClick={() => remove(s.id)}>×</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Rules Tab                                                           */
/* ------------------------------------------------------------------ */

function RulesTab({
  rules,
  onRefresh,
}: {
  rules: ReturnType<typeof useAsync>;
  onRefresh: () => void;
}) {
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [minAge, setMinAge] = useState(90);
  const [dropPct, setDropPct] = useState(10);
  const [creating, setCreating] = useState(false);

  const create = useCallback(async () => {
    if (!name.trim()) return;
    setCreating(true);
    try {
      await api.createRule({ website_id: 0, name: name.trim(), min_age_days: minAge, traffic_drop_pct: dropPct }); // website_id set by backend from active
      setShowForm(false);
      setName("");
      await onRefresh();
    } catch {}
    setCreating(false);
  }, [name, minAge, dropPct, onRefresh]);

  const remove = useCallback(async (id: number) => {
    await api.deleteRule(id);
    await onRefresh();
  }, [onRefresh]);

  if (rules.loading) return <Loading />;

  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <h3 style={{ margin: 0 }}>Rules</h3>
        <button className="btn" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "Add Rule"}
        </button>
      </div>

      {showForm && (
        <div style={{ marginBottom: 12, padding: 12, background: "var(--bg-secondary)", borderRadius: 8 }}>
          <div style={{ display: "flex", gap: 8, marginBottom: 8, flexWrap: "wrap" }}>
            <input placeholder="Rule name" value={name} onChange={(e) => setName(e.target.value)} style={{ flex: 1, minWidth: 150, padding: "6px 10px", border: "1px solid var(--border)", borderRadius: 4 }} />
            <input type="number" placeholder="Min age (days)" value={minAge} onChange={(e) => setMinAge(Number(e.target.value))} style={{ width: 120, padding: "6px 10px", border: "1px solid var(--border)", borderRadius: 4 }} />
            <input type="number" placeholder="Drop %" value={dropPct} onChange={(e) => setDropPct(Number(e.target.value))} style={{ width: 100, padding: "6px 10px", border: "1px solid var(--border)", borderRadius: 4 }} />
            <button className="btn btn-primary" onClick={create} disabled={creating}>{creating ? "Creating…" : "Create"}</button>
          </div>
        </div>
      )}

      {(rules.data as RefreshRule[]).length === 0 ? (
        <Empty text="No rules configured. Add a rule to define staleness thresholds." />
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: "2px solid var(--border)" }}>
              <th style={{ textAlign: "left", padding: 8 }}>Name</th>
              <th style={{ textAlign: "right", padding: 8 }}>Min Age</th>
              <th style={{ textAlign: "right", padding: 8 }}>Drop %</th>
              <th style={{ textAlign: "right", padding: 8 }}>Staleness W</th>
              <th style={{ textAlign: "right", padding: 8 }}>Traffic W</th>
              <th style={{ textAlign: "center", padding: 8 }}>Enabled</th>
              <th style={{ textAlign: "right", padding: 8 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {(rules.data as RefreshRule[]).map((r) => (
              <tr key={r.id} style={{ borderBottom: "1px solid var(--border)" }}>
                <td style={{ padding: 8, fontWeight: 600 }}>{r.name}</td>
                <td style={{ padding: 8, textAlign: "right" }}>{r.min_age_days}d</td>
                <td style={{ padding: 8, textAlign: "right" }}>{r.traffic_drop_pct}%</td>
                <td style={{ padding: 8, textAlign: "right" }}>{r.staleness_weight}</td>
                <td style={{ padding: 8, textAlign: "right" }}>{r.traffic_weight}</td>
                <td style={{ padding: 8, textAlign: "center" }}>{r.enabled ? "✓" : "—"}</td>
                <td style={{ padding: 8, textAlign: "right" }}>
                  <button className="btn" style={{ fontSize: 11, color: "var(--danger)" }} onClick={() => remove(r.id)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  History Tab                                                         */
/* ------------------------------------------------------------------ */

function HistoryTab({ history }: { history: ReturnType<typeof useAsync> }) {
  if (history.loading) return <Loading />;

  const items = (history.data as RefreshHistory[]) ?? [];

  return (
    <div className="card">
      <h3>Refresh History</h3>
      {items.length === 0 ? (
        <Empty text="No refresh history yet." />
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: "2px solid var(--border)" }}>
              <th style={{ textAlign: "left", padding: 8 }}>Date</th>
              <th style={{ textAlign: "left", padding: 8 }}>Page</th>
              <th style={{ textAlign: "left", padding: 8 }}>Action</th>
              <th style={{ textAlign: "right", padding: 8 }}>Clicks Δ</th>
              <th style={{ textAlign: "right", padding: 8 }}>Impressions Δ</th>
              <th style={{ textAlign: "right", padding: 8 }}>Position Δ</th>
              <th style={{ textAlign: "left", padding: 8 }}>Notes</th>
            </tr>
          </thead>
          <tbody>
            {items.map((h) => (
              <tr key={h.id} style={{ borderBottom: "1px solid var(--border)" }}>
                <td style={{ padding: 8, fontSize: 12 }}>{h.created_at?.slice(0, 10)}</td>
                <td style={{ padding: 8 }}>Page #{h.page_id}</td>
                <td style={{ padding: 8 }}><Badge value={h.action} /></td>
                <td style={{ padding: 8, textAlign: "right" }}>
                  {h.clicks_before != null && h.clicks_after != null
                    ? `${h.clicks_after - h.clicks_before > 0 ? "+" : ""}${h.clicks_after - h.clicks_before}`
                    : "—"}
                </td>
                <td style={{ padding: 8, textAlign: "right" }}>
                  {h.impressions_before != null && h.impressions_after != null
                    ? `${h.impressions_after - h.impressions_before > 0 ? "+" : ""}${h.impressions_after - h.impressions_before}`
                    : "—"}
                </td>
                <td style={{ padding: 8, textAlign: "right" }}>
                  {h.position_before != null && h.position_after != null
                    ? `${(h.position_after - h.position_before).toFixed(1)}`
                    : "—"}
                </td>
                <td style={{ padding: 8, fontSize: 12, maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {h.notes ?? "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
