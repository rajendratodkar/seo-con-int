import { useCallback, useEffect, useState } from "react";
import { contentBriefs as api } from "../services/backend";
import { useWebsiteStore } from "../stores/websiteStore";
import { Badge, Empty, ErrorBox, Loading } from "../components/common";
import { useAsync } from "../hooks/useAsync";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface BriefSummary {
  id: number;
  website_id: number;
  target_keyword: string;
  primary_keyword: string;
  search_intent: string | null;
  target_word_count: number | null;
  status: string;
  version: number;
  created_at: string;
  updated_at: string;
}

interface BriefDetail extends BriefSummary {
  secondary_keywords: string[] | null;
  title_options: string[] | null;
  meta_descriptions: string[] | null;
  outline: { heading: string; level: number; priority: string; notes?: string }[] | null;
  faq: { question: string; answer: string }[] | null;
  things_to_avoid: string[] | null;
  key_talking_points: string[] | null;
  serp_features: Record<string, unknown> | null;
  internal_links: { anchor: string; target_section: string; reason: string }[] | null;
  source_evidence: Record<string, unknown> | null;
  markdown_export: string | null;
}

interface Competitor {
  id: number;
  url: string;
  title: string | null;
  word_count: number | null;
  headings: string | null;
  keyword_density: number | null;
  media_count: number;
  has_faq: number;
  has_schema: number;
}

/* ------------------------------------------------------------------ */
/*  Main page                                                          */
/* ------------------------------------------------------------------ */

export default function ContentBriefs() {
  const { active } = useWebsiteStore();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [keyword, setKeyword] = useState("");
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const list = useAsync(() => (active ? api.list(active.id) : Promise.resolve([])), [active?.id]);

  const selectBrief = useCallback((id: number) => {
    setSelectedId(id);
    setError(null);
  }, []);

  const generate = useCallback(async () => {
    if (!active || !keyword.trim()) return;
    setGenerating(true);
    setError(null);
    try {
      const brief = await api.generate(active.id, keyword.trim()) as Record<string, unknown>;
      await list.reload();
      setSelectedId(brief.id as number);
      setKeyword("");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
    setGenerating(false);
  }, [active, keyword, list]);

  const remove = useCallback(async (id: number) => {
    try {
      await api.delete(id);
      if (selectedId === id) setSelectedId(null);
      await list.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [selectedId, list]);

  if (!active) return <Empty text="Add a website first." />;

  return (
    <>
      <h2 className="page-title">Content Briefs</h2>
      <p className="page-sub">
        Enter a target keyword to generate a data-driven writing brief with competitor insights, outline, FAQ, and exportable Markdown.
      </p>

      {error && <ErrorBox message={error} />}

      {/* Generate form */}
      <div className="card" style={{ marginBottom: 16 }}>
        <h3>Generate Brief</h3>
        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
          <input
            type="text"
            placeholder="Enter target keyword…"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && generate()}
            style={{ flex: 1, padding: "8px 12px", border: "1px solid var(--border)", borderRadius: 6 }}
          />
          <button
            className="btn btn-primary"
            onClick={generate}
            disabled={generating || !keyword.trim()}
          >
            {generating ? "Analyzing…" : "Generate"}
          </button>
        </div>
      </div>

      {/* Brief list + detail */}
      <div style={{ display: "flex", gap: 16, alignItems: "flex-start" }}>
        {/* Left: list */}
        <div className="card" style={{ minWidth: 320, flexShrink: 0 }}>
          <h3>Briefs ({list.data?.length ?? 0})</h3>
          {list.loading ? (
            <Loading />
          ) : (list.data?.length ?? 0) === 0 ? (
            <Empty text="No briefs yet." />
          ) : (
            <div style={{ marginTop: 8 }}>
              {(list.data as BriefSummary[]).map((b) => (
                <div
                  key={b.id}
                  onClick={() => selectBrief(b.id)}
                  style={{
                    padding: "8px 12px",
                    borderRadius: 6,
                    cursor: "pointer",
                    background: selectedId === b.id ? "var(--bg-active, #e8f0fe)" : "transparent",
                    marginBottom: 4,
                    border: selectedId === b.id ? "1px solid var(--primary)" : "1px solid transparent",
                  }}
                >
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{b.target_keyword}</div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                    <Badge value={b.status} /> · v{b.version} · {b.created_at?.slice(0, 10)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right: detail */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {selectedId ? (
            <BriefDetailPanel briefId={selectedId} onDelete={remove} onRefresh={list.reload} />
          ) : (
            <Empty text="Select a brief to view details." />
          )}
        </div>
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ */
/*  Detail panel                                                        */
/* ------------------------------------------------------------------ */

function BriefDetailPanel({
  briefId,
  onDelete,
  onRefresh,
}: {
  briefId: number;
  onDelete: (id: number) => void;
  onRefresh: () => void;
}) {
  const [tab, setTab] = useState<"overview" | "outline" | "faq" | "competitors" | "markdown">("overview");
  const brief = useAsync(() => api.get(briefId), [briefId]);
  const competitors = useAsync(() => api.competitors(briefId), [briefId]);
  const [updating, setUpdating] = useState(false);

  const data = brief.data as unknown as BriefDetail | undefined;

  const finalize = useCallback(async () => {
    setUpdating(true);
    try {
      await api.finalize(briefId);
      await brief.reload();
      await onRefresh();
    } catch {}
    setUpdating(false);
  }, [briefId, brief, onRefresh]);

  const sendToPlanner = useCallback(async () => {
    setUpdating(true);
    try {
      await api.sendToPlanner(briefId);
      await brief.reload();
      await onRefresh();
    } catch {}
    setUpdating(false);
  }, [briefId, brief, onRefresh]);

  if (brief.loading) return <Loading />;
  if (brief.error) return <ErrorBox message={brief.error} />;
  if (!data) return <Empty text="Brief not found." />;

  const outline = Array.isArray(data.outline) ? data.outline : [];
  const faq = Array.isArray(data.faq) ? data.faq : [];
  const avoid = Array.isArray(data.things_to_avoid) ? data.things_to_avoid : [];
  const talkingPoints = Array.isArray(data.key_talking_points) ? data.key_talking_points : [];
  const titleOptions = Array.isArray(data.title_options) ? data.title_options : [];
  const metaOptions = Array.isArray(data.meta_descriptions) ? data.meta_descriptions : [];
  const secKeywords = Array.isArray(data.secondary_keywords) ? data.secondary_keywords : [];
  const internalLinks = Array.isArray(data.internal_links) ? data.internal_links : [];
  const evidence = (data.source_evidence ?? {}) as Record<string, unknown>;

  return (
    <div className="card">
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <div>
          <h3 style={{ margin: 0 }}>{data.target_keyword}</h3>
          <div style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 4 }}>
            <Badge value={data.status} /> · v{data.version} · Intent: {data.search_intent ?? "N/A"} · Target: {data.target_word_count ?? "N/A"} words
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {data.status === "draft" && (
            <button className="btn" onClick={finalize} disabled={updating}>Finalize</button>
          )}
          {data.status === "finalized" && (
            <button className="btn btn-primary" onClick={sendToPlanner} disabled={updating}>Send to Planner</button>
          )}
          <button className="btn" style={{ color: "var(--danger)" }} onClick={() => onDelete(briefId)}>Delete</button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 4, marginBottom: 12, borderBottom: "1px solid var(--border)", paddingBottom: 8 }}>
        {(["overview", "outline", "faq", "competitors", "markdown"] as const).map((t) => (
          <button key={t} className={`btn ${tab === t ? "btn-primary" : ""}`} onClick={() => setTab(t)} style={{ fontSize: 13 }}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === "overview" && (
        <div>
          {titleOptions.length > 0 && (
            <section style={{ marginBottom: 16 }}>
              <h4>Title Options</h4>
              <ol style={{ paddingLeft: 20 }}>
                {titleOptions.map((t, i) => <li key={i} style={{ marginBottom: 4 }}>{t}</li>)}
              </ol>
            </section>
          )}
          {metaOptions.length > 0 && (
            <section style={{ marginBottom: 16 }}>
              <h4>Meta Descriptions</h4>
              {metaOptions.map((m, i) => (
                <div key={i} style={{ padding: "6px 10px", background: "var(--bg-secondary)", borderRadius: 4, marginBottom: 4, fontSize: 13 }}>
                  {m} <span style={{ color: m.length > 160 ? "var(--danger)" : m.length < 70 ? "var(--warning)" : "var(--success)", fontSize: 11 }}>
                    ({m.length} chars)
                  </span>
                </div>
              ))}
            </section>
          )}
          {secKeywords.length > 0 && (
            <section style={{ marginBottom: 16 }}>
              <h4>Secondary Keywords</h4>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {secKeywords.map((k, i) => <Badge key={i} value={k} />)}
              </div>
            </section>
          )}
          {talkingPoints.length > 0 && (
            <section style={{ marginBottom: 16 }}>
              <h4>Key Talking Points</h4>
              <ul style={{ paddingLeft: 20 }}>
                {talkingPoints.map((p, i) => <li key={i} style={{ marginBottom: 4 }}>{p}</li>)}
              </ul>
            </section>
          )}
          {avoid.length > 0 && (
            <section style={{ marginBottom: 16 }}>
              <h4>Things to Avoid</h4>
              <ul style={{ paddingLeft: 20 }}>
                {avoid.map((a, i) => <li key={i} style={{ marginBottom: 4, color: "var(--warning)" }}>{a}</li>)}
              </ul>
            </section>
          )}
          {internalLinks.length > 0 && (
            <section style={{ marginBottom: 16 }}>
              <h4>Internal Link Suggestions</h4>
              {internalLinks.map((l, i) => (
                <div key={i} style={{ padding: "4px 0", fontSize: 13 }}>
                  <strong>{l.anchor}</strong> → {l.target_section} <span style={{ color: "var(--text-muted)" }}>— {l.reason}</span>
                </div>
              ))}
            </section>
          )}
          {evidence && (
            <section>
              <h4>Source Evidence</h4>
              <pre style={{ fontSize: 12, background: "var(--bg-secondary)", padding: 8, borderRadius: 4, overflow: "auto" }}>
                {JSON.stringify(evidence, null, 2)}
              </pre>
            </section>
          )}
        </div>
      )}

      {tab === "outline" && (
        <div>
          {outline.length === 0 ? (
            <Empty text="No outline generated." />
          ) : (
            <div>
              {outline.map((item, i) => (
                <div
                  key={i}
                  style={{
                    paddingLeft: (item.level - 1) * 24,
                    padding: `${item.level === 1 ? 8 : 4}px ${(item.level - 1) * 24 + 8}px`,
                    borderBottom: "1px solid var(--border)",
                    fontSize: item.level === 1 ? 18 : item.level === 2 ? 15 : 13,
                    fontWeight: item.level <= 2 ? 600 : 400,
                  }}
                >
                  <span>{item.heading}</span>
                  {item.priority && (
                    <Badge value={item.priority} />
                  )}
                  {item.notes && (
                    <span style={{ fontSize: 12, color: "var(--text-muted)", marginLeft: 8 }}>{item.notes}</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === "faq" && (
        <div>
          {faq.length === 0 ? (
            <Empty text="No FAQ suggestions." />
          ) : (
            faq.map((item, i) => (
              <div key={i} style={{ marginBottom: 12, padding: 10, background: "var(--bg-secondary)", borderRadius: 6 }}>
                <div style={{ fontWeight: 600, marginBottom: 4 }}>Q: {item.question}</div>
                {item.answer ? (
                  <div style={{ fontSize: 13 }}>A: {item.answer}</div>
                ) : (
                  <div style={{ fontSize: 12, color: "var(--text-muted)", fontStyle: "italic" }}>Answer not yet written</div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {tab === "competitors" && (
        <div>
          {competitors.loading ? (
            <Loading />
          ) : (competitors.data?.length ?? 0) === 0 ? (
            <Empty text="No competitor data." />
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: "2px solid var(--border)" }}>
                  <th style={{ textAlign: "left", padding: 8 }}>URL</th>
                  <th style={{ textAlign: "right", padding: 8 }}>Words</th>
                  <th style={{ textAlign: "right", padding: 8 }}>Headings</th>
                  <th style={{ textAlign: "right", padding: 8 }}>Images</th>
                  <th style={{ textAlign: "center", padding: 8 }}>FAQ</th>
                  <th style={{ textAlign: "center", padding: 8 }}>Schema</th>
                </tr>
              </thead>
              <tbody>
                {(competitors.data as Competitor[]).map((c) => (
                  <tr key={c.id} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ padding: 8, maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={c.url}>
                      {c.url}
                    </td>
                    <td style={{ padding: 8, textAlign: "right" }}>{c.word_count ?? "—"}</td>
                    <td style={{ padding: 8, textAlign: "right" }}>{c.headings ? JSON.parse(c.headings).length : "—"}</td>
                    <td style={{ padding: 8, textAlign: "right" }}>{c.media_count}</td>
                    <td style={{ padding: 8, textAlign: "center" }}>{c.has_faq ? "✓" : "—"}</td>
                    <td style={{ padding: 8, textAlign: "center" }}>{c.has_schema ? "✓" : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {tab === "markdown" && (
        <div>
          <div style={{ marginBottom: 8 }}>
            <a
              href={api.exportMarkdown(briefId)}
              target="_blank"
              rel="noopener noreferrer"
              className="btn"
            >
              Download Markdown
            </a>
          </div>
          <pre style={{
            fontSize: 13,
            background: "var(--bg-secondary)",
            padding: 16,
            borderRadius: 8,
            whiteSpace: "pre-wrap",
            maxHeight: 600,
            overflow: "auto",
            lineHeight: 1.5,
          }}>
            {data.markdown_export || "No markdown exported yet."}
          </pre>
        </div>
      )}
    </div>
  );
}
