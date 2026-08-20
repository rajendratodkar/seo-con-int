import { useCallback, useState } from "react";
import { competitors as api } from "../services/backend";
import { Badge, ErrorBox, Loading } from "../components/common";
import { useAsync } from "../hooks/useAsync";
import { useWebsiteStore } from "../stores/websiteStore";
import type { Competitor, CompetitorRanking, ContentGap } from "../types";

// ---------------------------------------------------------------------------
// Competitors Tab
// ---------------------------------------------------------------------------

function CompetitorsTab() {
  const { active } = useWebsiteStore();
  const list = useAsync(() => active ? api.list(active.id) : Promise.resolve([]), [active?.id]);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [importingId, setImportingId] = useState<number | null>(null);
  const [importText, setImportText] = useState("");

  const create = useCallback(async () => {
    if (!active) return;
    setError(null);
    try {
      await api.create(active.id, name, url, notes || undefined);
      setShowForm(false);
      setName("");
      setUrl("");
      setNotes("");
      await list.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [active, name, url, notes, list]);

  const remove = useCallback(async (id: number) => {
    try {
      await api.delete(id);
      await list.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [list]);

  const startImport = useCallback((id: number) => {
    setImportingId(importingId === id ? null : id);
    setImportText("");
  }, [importingId]);

  const doImport = useCallback(async (competitorId: number) => {
    try {
      // Parse CSV-like input: keyword,position,url (one per line)
      const lines = importText.trim().split("\n").filter(Boolean);
      const rankings = lines.map((line) => {
        const parts = line.split(",").map((s) => s.trim());
        return {
          keyword: parts[0],
          position: parseFloat(parts[1]) || 0,
          url: parts[2] || undefined,
        };
      });
      const today = new Date().toISOString().split("T")[0];
      const result = await api.importRankings(competitorId, rankings, today);
      alert(`Imported ${result.imported} rankings`);
      setImportingId(null);
      setImportText("");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [importText]);

  if (list.loading) return <Loading />;
  if (list.error) return <ErrorBox message={list.error} />;

  const competitors: Competitor[] = list.data ?? [];

  return (
    <>
      <div className="row" style={{ justifyContent: "space-between", marginBottom: 12 }}>
        <h3 style={{ margin: 0 }}>Competitors {active ? `— ${active.name}` : ""}</h3>
        <button className="small" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "+ Add Competitor"}
        </button>
      </div>

      {error && <ErrorBox message={error} />}

      {showForm && (
        <div className="card" style={{ marginBottom: 12 }}>
          <div className="row" style={{ gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
            <input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} style={{ width: 200 }} />
            <input placeholder="URL (e.g. https://competitor.com)" value={url} onChange={(e) => setUrl(e.target.value)} style={{ flex: 1, minWidth: 250 }} />
          </div>
          <input placeholder="Notes (optional)" value={notes} onChange={(e) => setNotes(e.target.value)} style={{ width: "100%", marginBottom: 8 }} />
          <button className="small" onClick={create} disabled={!name || !url}>Add Competitor</button>
        </div>
      )}

      {competitors.length === 0 ? (
        <p className="muted">No competitors tracked. Add one to start competitive analysis.</p>
      ) : (
        <table className="data">
          <thead>
            <tr><th>Name</th><th>URL</th><th>Notes</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {competitors.map((c) => (
              <tr key={c.id}>
                <td><strong>{c.name}</strong></td>
                <td className="mono" style={{ fontSize: 12 }}>{c.url}</td>
                <td className="muted">{c.notes || "—"}</td>
                <td>
                  <button className="small" onClick={() => startImport(c.id)}>
                    {importingId === c.id ? "Cancel" : "Import Rankings"}
                  </button>{" "}
                  <button className="small" onClick={() => remove(c.id)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Inline ranking import */}
      {importingId && (
        <div className="card" style={{ marginTop: 12 }}>
          <h4>Import Rankings for Competitor #{importingId}</h4>
          <p className="muted" style={{ fontSize: 12, marginBottom: 8 }}>
            Paste CSV: keyword,position,url (one per line). Example:<br />
            <code>best seo tools,3,https://competitor.com/seo-tools</code>
          </p>
          <textarea
            value={importText}
            onChange={(e) => setImportText(e.target.value)}
            rows={6}
            style={{ width: "100%", fontFamily: "monospace", fontSize: 12, marginBottom: 8 }}
            placeholder={"best seo tools,3,https://competitor.com/seo-tools\nseo audit software,7\ncontent marketing guide,12,https://competitor.com/guide"}
          />
          <button className="small" onClick={() => doImport(importingId)} disabled={!importText.trim()}>
            Import
          </button>
        </div>
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Rankings Detail (for a single competitor)
// ---------------------------------------------------------------------------

function CompetitorDetail({ competitorId, onBack }: { competitorId: number; onBack: () => void }) {
  const detail = useAsync(() => api.get(competitorId), [competitorId]);
  const rankings = useAsync(() => api.rankings(competitorId), [competitorId]);
  const [error, setError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);

  const analyzeGaps = useCallback(async (websiteId: number) => {
    setAnalyzing(true);
    try {
      const result = await api.analyzeGaps(competitorId, websiteId);
      alert(`Found ${result.gaps_found} gaps: ${result.new_content} new content, ${result.quick_win} quick wins, ${result.improve_existing} improve existing.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
    setAnalyzing(false);
  }, [competitorId]);

  if (detail.loading || rankings.loading) return <Loading />;
  if (detail.error) return <ErrorBox message={detail.error} />;
  if (!detail.data) return <ErrorBox message="Competitor not found" />;

  const summary = detail.data;
  const ranks: CompetitorRanking[] = rankings.data ?? [];

  return (
    <>
      <button className="small" onClick={onBack} style={{ marginBottom: 12 }}>← Back</button>
      {error && <ErrorBox message={error} />}

      <h3>{summary.competitor.name}</h3>
      <p className="muted" style={{ marginBottom: 4 }}>{summary.competitor.url}</p>
      <p className="muted" style={{ fontSize: 12, marginBottom: 12 }}>
        {summary.keyword_count} keywords tracked &middot; Avg position: {summary.avg_position ?? "—"}
      </p>

      <div className="card" style={{ marginBottom: 16 }}>
        <h4>Top Keywords</h4>
        {summary.top_keywords.length === 0 ? (
          <p className="muted">No rankings imported yet.</p>
        ) : (
          <table className="data">
            <thead><tr><th>Keyword</th><th>Position</th><th>URL</th></tr></thead>
            <tbody>
              {summary.top_keywords.map((k, i) => (
                <tr key={i}>
                  <td>{k.keyword}</td>
                  <td><Badge value={k.position <= 3 ? "full" : k.position <= 10 ? "amber" : "gray"} /> {k.position}</td>
                  <td className="mono" style={{ fontSize: 11, maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis" }}>{k.url || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// Gaps Tab
// ---------------------------------------------------------------------------

function GapsTab() {
  const { active } = useWebsiteStore();
  const gaps = useAsync(() => active ? api.gaps(active.id) : Promise.resolve([]), [active?.id]);
  const stats = useAsync(() => active ? api.gapStats(active.id) : Promise.resolve(null), [active?.id]);
  const [filter, setFilter] = useState<string | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);

  const updateStatus = useCallback(async (gapId: number, status: string) => {
    try {
      await api.updateGapStatus(gapId, status);
      await gaps.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [gaps]);

  if (gaps.loading || stats.loading) return <Loading />;
  if (gaps.error) return <ErrorBox message={gaps.error} />;

  const gapList: ContentGap[] = gaps.data ?? [];
  const s = stats.data;

  const OPPORTUNITY_COLORS: Record<string, string> = {
    new_content: "blue",
    improve_existing: "amber",
    quick_win: "green",
  };

  return (
    <>
      <h3>Content Gaps {active ? `— ${active.name}` : ""}</h3>
      {error && <ErrorBox message={error} />}

      {s && (
        <div className="row" style={{ gap: 16, marginBottom: 16 }}>
          <div className="card" style={{ flex: 1, textAlign: "center" }}>
            <div style={{ fontSize: 28, fontWeight: 700 }}>{s.total}</div>
            <div className="muted" style={{ fontSize: 12 }}>Total Gaps</div>
          </div>
          <div className="card" style={{ flex: 1, textAlign: "center" }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: "#3b82f6" }}>{s.new_content}</div>
            <div className="muted" style={{ fontSize: 12 }}>New Content</div>
          </div>
          <div className="card" style={{ flex: 1, textAlign: "center" }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: "#22c55e" }}>{s.quick_win}</div>
            <div className="muted" style={{ fontSize: 12 }}>Quick Wins</div>
          </div>
          <div className="card" style={{ flex: 1, textAlign: "center" }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: "#f59e0b" }}>{s.improve_existing}</div>
            <div className="muted" style={{ fontSize: 12 }}>Improve Existing</div>
          </div>
        </div>
      )}

      <div className="row" style={{ gap: 8, marginBottom: 12 }}>
        {[
          [undefined, "All"],
          ["new_content", "New Content"],
          ["quick_win", "Quick Wins"],
          ["improve_existing", "Improve"],
          ["open", "Open Only"],
        ].map(([val, label]) => (
          <button
            key={label}
            className={`small${filter === val ? "" : " secondary"}`}
            onClick={() => setFilter(val as string | undefined)}
          >
            {label}
          </button>
        ))}
      </div>

      {gapList.length === 0 ? (
        <p className="muted">
          No gaps found. Add competitors, import their rankings, then run gap analysis.
        </p>
      ) : (
        <table className="data">
          <thead>
            <tr><th>Keyword</th><th>Competitor Pos</th><th>Our Pos</th><th>Opportunity</th><th>Priority</th><th>Status</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {gapList.slice(0, 50).map((g) => (
              <tr key={g.id}>
                <td><strong>{g.keyword}</strong></td>
                <td>{g.competitor_pos}</td>
                <td>{g.our_position ?? "—"}</td>
                <td><Badge value={g.opportunity} /></td>
                <td>
                  <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                    <div style={{ width: 60, height: 6, background: "#e5e7eb", borderRadius: 3 }}>
                      <div style={{ width: `${g.priority * 100}%`, height: "100%", background: "#3b82f6", borderRadius: 3 }} />
                    </div>
                    <span className="muted" style={{ fontSize: 11 }}>{(g.priority * 100).toFixed(0)}%</span>
                  </div>
                </td>
                <td><Badge value={g.status} /></td>
                <td>
                  {g.status === "open" && (
                    <button className="small" onClick={() => updateStatus(g.id, "reviewed")}>Review</button>
                  )}
                  {g.status === "reviewed" && (
                    <button className="small" onClick={() => updateStatus(g.id, "acted_on")}>Mark Done</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

type Tab = "competitors" | "gaps";

export default function Competitors() {
  const [tab, setTab] = useState<Tab>("competitors");
  const [selectedId, setSelectedId] = useState<number | null>(null);

  if (selectedId) {
    return <CompetitorDetail competitorId={selectedId} onBack={() => setSelectedId(null)} />;
  }

  return (
    <>
      <h2 className="page-title">🏆 Competitor Analysis</h2>
      <p className="page-sub">
        Track competitors, import their rankings, and discover content gaps.
      </p>

      <div className="row" style={{ gap: 4, marginBottom: 16 }}>
        {([
          ["competitors", "Competitors"],
          ["gaps", "Content Gaps"],
        ] as [Tab, string][]).map(([key, label]) => (
          <button
            key={key}
            className={`small${tab === key ? "" : " secondary"}`}
            onClick={() => { setTab(key); setSelectedId(null); }}
            style={{ fontWeight: tab === key ? 700 : 400 }}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "competitors" && !selectedId && <CompetitorsTab />}
      {tab === "gaps" && <GapsTab />}
    </>
  );
}
