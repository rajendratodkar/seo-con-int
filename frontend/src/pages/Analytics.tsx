import { useCallback, useState } from "react";
import { reports as api } from "../services/backend";
import { Badge, ErrorBox, Loading } from "../components/common";
import { useAsync } from "../hooks/useAsync";
import { useWebsiteStore } from "../stores/websiteStore";

// ---------------------------------------------------------------------------
// CSS Bar Chart (no dependencies)
// ---------------------------------------------------------------------------

function BarChart({ data, maxValue, height = 120 }: { data: { label: string; value: number; color?: string }[]; maxValue?: number; height?: number }) {
  const max = maxValue ?? Math.max(...data.map((d) => d.value), 1);
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 2, height, padding: "0 4px" }}>
      {data.map((d, i) => (
        <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 2 }}>
          <span style={{ fontSize: 10, color: "#6b7280" }}>{d.value > 0 ? d.value.toLocaleString() : ""}</span>
          <div style={{
            width: "100%",
            height: `${Math.max((d.value / max) * (height - 20), 2)}px`,
            background: d.color ?? "#3b82f6",
            borderRadius: "3px 3px 0 0",
            transition: "height 0.3s ease",
          }} />
          <span style={{ fontSize: 9, color: "#9ca3af", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: "100%" }}>{d.label}</span>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sparkline (CSS mini chart)
// ---------------------------------------------------------------------------

function Sparkline({ values, color = "#3b82f6", height = 32 }: { values: number[]; color?: string; height?: number }) {
  if (values.length === 0) return <span className="muted">No data</span>;
  const max = Math.max(...values, 1);
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 1, height }}>
      {values.map((v, i) => (
        <div key={i} style={{
          flex: 1,
          height: `${Math.max((v / max) * height, 1)}px`,
          background: color,
          borderRadius: 1,
          opacity: 0.7 + (i / values.length) * 0.3,
        }} />
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Horizontal Bar (for ranking distribution)
// ---------------------------------------------------------------------------

function HBar({ label, value, total, color }: { label: string; value: number; total: number; color: string }) {
  const pct = total > 0 ? (value / total) * 100 : 0;
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 2 }}>
        <span>{label}</span>
        <span className="muted">{value} ({pct.toFixed(0)}%)</span>
      </div>
      <div style={{ height: 8, background: "#e5e7eb", borderRadius: 4, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 4, transition: "width 0.3s" }} />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// KPI Card
// ---------------------------------------------------------------------------

function KpiCard({ label, value, sub, color }: { label: string; value: string | number; sub?: string; color?: string }) {
  return (
    <div className="card" style={{ flex: 1, minWidth: 140, textAlign: "center" }}>
      <div className="muted" style={{ fontSize: 12, marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 700, color: color ?? "#111827" }}>{value}</div>
      {sub && <div className="muted" style={{ fontSize: 11, marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Analytics Page
// ---------------------------------------------------------------------------

const PERIODS = [
  { value: 7, label: "7 days" },
  { value: 30, label: "30 days" },
  { value: 90, label: "90 days" },
  { value: 365, label: "1 year" },
];

export default function Analytics() {
  const { active } = useWebsiteStore();
  const [days, setDays] = useState(30);
  const [tab, setTab] = useState<"overview" | "traffic" | "pages" | "queries">("overview");

  const overview = useAsync(() => active ? api.analyticsOverview(active.id, days) : Promise.resolve(null), [active?.id, days]);
  const trend = useAsync(() => active ? api.trafficTrend(active.id, days) : Promise.resolve([]), [active?.id, days]);
  const pages = useAsync(() => active ? api.topPages(active.id, days, 20) : Promise.resolve([]), [active?.id, days]);
  const queries = useAsync(() => active ? api.topQueries(active.id, days, 20) : Promise.resolve([]), [active?.id, days]);

  if (!active) return <p className="muted">Select a website to view analytics.</p>;
  if (overview.loading) return <Loading />;
  if (overview.error) return <ErrorBox message={overview.error} />;

  const data = overview.data as Record<string, unknown> | null;
  const kpis = data?.kpis as Record<string, number> | undefined;
  const trendData = trend.data ?? [];
  const pagesData = (pages.data ?? []) as { page_url: string; clicks: number; impressions: number; ctr: number; position: number }[];
  const queriesData = (queries.data ?? []) as { query: string; clicks: number; impressions: number; ctr: number; position: number }[];
  const rankDist = data?.ranking_distribution as Record<string, number> | undefined;
  const findings = (data?.findings ?? []) as { severity: string; rec_type: string; n: number }[];
  const audit = data?.audit as Record<string, number> | undefined;

  const totalKeywords = (rankDist?.top_3 ?? 0) + (rankDist?.pos_4_10 ?? 0) + (rankDist?.pos_11_20 ?? 0) + (rankDist?.pos_21_plus ?? 0);

  // Sparkline data from trend
  const clicksTrend = trendData.map((d) => d.clicks);
  const impressionsTrend = trendData.map((d) => d.impressions);

  return (
    <>
      <h2 className="page-title">📊 Analytics — {active.name}</h2>

      {/* Controls */}
      <div className="row" style={{ gap: 4, marginBottom: 16, flexWrap: "wrap" }}>
        {PERIODS.map((p) => (
          <button key={p.value} className={`small${days === p.value ? "" : " secondary"}`} onClick={() => setDays(p.value)}>
            {p.label}
          </button>
        ))}
        <div style={{ flex: 1 }} />
        {(["overview", "traffic", "pages", "queries"] as const).map((t) => (
          <button key={t} className={`small${tab === t ? "" : " secondary"}`} onClick={() => setTab(t)} style={{ fontWeight: tab === t ? 700 : 400 }}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {/* KPIs */}
      {kpis && (
        <div className="row" style={{ gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
          <KpiCard label="Total Clicks" value={kpis.total_clicks?.toLocaleString() ?? "0"} />
          <KpiCard label="Total Impressions" value={kpis.total_impressions?.toLocaleString() ?? "0"} />
          <KpiCard label="Avg CTR" value={`${((kpis.avg_ctr ?? 0) * 100).toFixed(2)}%`} color="#3b82f6" />
          <KpiCard label="Avg Position" value={(kpis.avg_position ?? 0).toFixed(1)} color={kpis.avg_position && kpis.avg_position <= 10 ? "#22c55e" : "#f59e0b"} />
          <KpiCard label="Pages Indexed" value={kpis.pages_indexed ?? 0} />
          <KpiCard label="Unique Queries" value={kpis.unique_queries ?? 0} />
        </div>
      )}

      {/* Overview Tab */}
      {tab === "overview" && (
        <>
          {/* Traffic Trend Sparkline */}
          {clicksTrend.length > 0 && (
            <div className="card" style={{ marginBottom: 16 }}>
              <h3>Clicks Trend</h3>
              <Sparkline values={clicksTrend} color="#3b82f6" height={60} />
              <div className="row" style={{ justifyContent: "space-between", marginTop: 4 }}>
                <span className="muted" style={{ fontSize: 10 }}>{trendData[0]?.date}</span>
                <span className="muted" style={{ fontSize: 10 }}>{trendData[trendData.length - 1]?.date}</span>
              </div>
            </div>
          )}

          {/* Ranking Distribution */}
          {rankDist && (
            <div className="card" style={{ marginBottom: 16 }}>
              <h3>Ranking Distribution</h3>
              <HBar label="Top 3 (Top spots)" value={rankDist.top_3 ?? 0} total={totalKeywords} color="#22c55e" />
              <HBar label="4–10 (First page)" value={rankDist.pos_4_10 ?? 0} total={totalKeywords} color="#3b82f6" />
              <HBar label="11–20 (Second page)" value={rankDist.pos_11_20 ?? 0} total={totalKeywords} color="#f59e0b" />
              <HBar label="21+ (Deep results)" value={rankDist.pos_21_plus ?? 0} total={totalKeywords} color="#ef4444" />
            </div>
          )}

          {/* Findings + Audit side by side */}
          <div className="row" style={{ gap: 16, marginBottom: 16 }}>
            <div className="card" style={{ flex: 1 }}>
              <h3>Open Findings</h3>
              {findings.length === 0 ? (
                <p className="muted">No open findings</p>
              ) : (
                <table className="data">
                  <thead><tr><th>Severity</th><th>Type</th><th>Count</th></tr></thead>
                  <tbody>
                    {findings.map((f, i) => (
                      <tr key={i}>
                        <td><Badge value={f.severity} /></td>
                        <td><Badge value={f.rec_type} /></td>
                        <td>{f.n}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
            <div className="card" style={{ flex: 1 }}>
              <h3>Content Audit</h3>
              {audit && Object.keys(audit).length > 0 ? (
                <div>
                  {Object.entries(audit).map(([verdict, count]) => (
                    <div key={verdict} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                      <Badge value={verdict} />
                      <span style={{ fontWeight: 600 }}>{count as number}</span>
                      <div style={{ flex: 1, height: 6, background: "#e5e7eb", borderRadius: 3 }}>
                        <div style={{
                          width: `${((count as number) / Math.max(...Object.values(audit).map(Number), 1)) * 100}%`,
                          height: "100%",
                          background: verdict === "keep" ? "#22c55e" : verdict === "improve" ? "#f59e0b" : verdict === "refresh" ? "#3b82f6" : "#8b5cf6",
                          borderRadius: 3,
                        }} />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="muted">Run a content audit from the Audit page</p>
              )}
            </div>
          </div>
        </>
      )}

      {/* Traffic Tab */}
      {tab === "traffic" && (
        <div className="card">
          <h3>Daily Traffic — Clicks</h3>
          {trendData.length === 0 ? (
            <p className="muted">No traffic data for this period</p>
          ) : (
            <BarChart
              data={trendData.map((d) => ({ label: d.date.slice(5), value: d.clicks, color: "#3b82f6" }))}
              height={160}
            />
          )}
          <h3 style={{ marginTop: 16 }}>Daily Traffic — Impressions</h3>
          {trendData.length === 0 ? (
            <p className="muted">No data</p>
          ) : (
            <BarChart
              data={trendData.map((d) => ({ label: d.date.slice(5), value: d.impressions, color: "#8b5cf6" }))}
              height={160}
            />
          )}
        </div>
      )}

      {/* Pages Tab */}
      {tab === "pages" && (
        <div className="card">
          <h3>Top Pages by Clicks</h3>
          {pagesData.length === 0 ? (
            <p className="muted">No page data for this period</p>
          ) : (
            <>
              <BarChart
                data={pagesData.slice(0, 15).map((p) => ({ label: p.page_url.split("/").pop()?.slice(0, 12) ?? "/", value: p.clicks }))}
                height={140}
              />
              <table className="data" style={{ marginTop: 12 }}>
                <thead><tr><th>Page</th><th>Clicks</th><th>Impressions</th><th>CTR</th><th>Position</th></tr></thead>
                <tbody>
                  {pagesData.map((p, i) => (
                    <tr key={i}>
                      <td style={{ maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={p.page_url}>{p.page_url}</td>
                      <td>{p.clicks.toLocaleString()}</td>
                      <td>{p.impressions.toLocaleString()}</td>
                      <td>{p.ctr.toFixed(2)}%</td>
                      <td><Badge value={p.position <= 3 ? "full" : p.position <= 10 ? "amber" : "gray"} /> {p.position}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>
      )}

      {/* Queries Tab */}
      {tab === "queries" && (
        <div className="card">
          <h3>Top Queries by Impressions</h3>
          {queriesData.length === 0 ? (
            <p className="muted">No query data for this period</p>
          ) : (
            <>
              <BarChart
                data={queriesData.slice(0, 15).map((q) => ({ label: q.query.slice(0, 15), value: q.impressions }))}
                height={140}
              />
              <table className="data" style={{ marginTop: 12 }}>
                <thead><tr><th>Query</th><th>Clicks</th><th>Impressions</th><th>CTR</th><th>Position</th></tr></thead>
                <tbody>
                  {queriesData.map((q, i) => (
                    <tr key={i}>
                      <td><strong>{q.query}</strong></td>
                      <td>{q.clicks.toLocaleString()}</td>
                      <td>{q.impressions.toLocaleString()}</td>
                      <td>{q.ctr.toFixed(2)}%</td>
                      <td><Badge value={q.position <= 3 ? "full" : q.position <= 10 ? "amber" : "gray"} /> {q.position}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>
      )}
    </>
  );
}
