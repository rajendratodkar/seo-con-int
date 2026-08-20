import { useCallback, useState } from "react";
import { pageSpeed as api } from "../services/backend";
import { Badge, ErrorBox, Loading } from "../components/common";
import { useAsync } from "../hooks/useAsync";
import { useWebsiteStore } from "../stores/websiteStore";
import type { PageSpeedSnapshotOut } from "../types";

// ---------------------------------------------------------------------------
// Score Gauge (CSS-only circular progress)
// ---------------------------------------------------------------------------

function ScoreGauge({ score, label, size = 64 }: { score: number | null; label: string; size?: number }) {
  const s = score ?? 0;
  const color = s >= 90 ? "#22c55e" : s >= 50 ? "#f59e0b" : "#ef4444";
  const pct = s / 100;
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const dashoffset = circumference * (1 - pct);

  return (
    <div style={{ textAlign: "center" }}>
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#e5e7eb" strokeWidth={4} />
        <circle
          cx={size / 2} cy={size / 2} r={radius} fill="none"
          stroke={color} strokeWidth={4} strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={dashoffset}
          style={{ transition: "stroke-dashoffset 0.5s ease" }}
        />
      </svg>
      <div style={{ marginTop: -size + 4, fontSize: size > 50 ? 18 : 14, fontWeight: 700, color, lineHeight: `${size}px` }}>
        {s}
      </div>
      <div className="muted" style={{ fontSize: 10, marginTop: 2 }}>{label}</div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Metric Card
// ---------------------------------------------------------------------------

function MetricCard({ label, value, unit, good, target }: { label: string; value: number | null; unit: string; good: number; target?: string }) {
  const v = value ?? 0;
  const isGood = unit === "s" ? v <= good : v <= good;
  return (
    <div className="card" style={{ flex: 1, minWidth: 120, textAlign: "center" }}>
      <div className="muted" style={{ fontSize: 11 }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 700, color: isGood ? "#22c55e" : "#f59e0b" }}>
        {v}{unit}
      </div>
      <div className="muted" style={{ fontSize: 10 }}>{target ?? `Good: ≤${good}${unit}`}</div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Score Card Row
// ---------------------------------------------------------------------------

function ScoreRow({ snapshot }: { snapshot: PageSpeedSnapshotOut }) {
  return (
    <div className="row" style={{ gap: 16, justifyContent: "center", marginBottom: 16 }}>
      <ScoreGauge score={snapshot.performance_score} label="Performance" />
      <ScoreGauge score={snapshot.accessibility_score} label="Accessibility" />
      <ScoreGauge score={snapshot.best_practices_score} label="Best Practices" />
      <ScoreGauge score={snapshot.seo_score} label="SEO" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Check Form
// ---------------------------------------------------------------------------

function CheckForm({ onDone }: { onDone: () => void }) {
  const { active } = useWebsiteStore();
  const [pageId, setPageId] = useState("");
  const [url, setUrl] = useState("");
  const [perf, setPerf] = useState("");
  const [access, setAccess] = useState("");
  const [bp, setBp] = useState("");
  const [seo, setSeo] = useState("");
  const [lcp, setLcp] = useState("");
  const [fid, setFid] = useState("");
  const [cls, setCls] = useState("");
  const [fcp, setFcp] = useState("");
  const [ttfb, setTtfb] = useState("");
  const [error, setError] = useState<string | null>(null);

  const save = useCallback(async () => {
    if (!active || !pageId || !url) return;
    setError(null);
    try {
      await api.check({
        website_id: active.id,
        page_id: parseInt(pageId),
        url,
        performance_score: perf ? parseInt(perf) : undefined,
        accessibility_score: access ? parseInt(access) : undefined,
        best_practices_score: bp ? parseInt(bp) : undefined,
        seo_score: seo ? parseInt(seo) : undefined,
        lcp: lcp ? parseFloat(lcp) : undefined,
        fid: fid ? parseFloat(fid) : undefined,
        cls: cls ? parseFloat(cls) : undefined,
        fcp: fcp ? parseFloat(fcp) : undefined,
        ttfb: ttfb ? parseFloat(ttfb) : undefined,
      });
      onDone();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [active, pageId, url, perf, access, bp, seo, lcp, fid, cls, fcp, ttfb, onDone]);

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <h4>Record Page Speed</h4>
      {error && <ErrorBox message={error} />}
      <div className="row" style={{ gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
        <input placeholder="Page ID" value={pageId} onChange={(e) => setPageId(e.target.value)} style={{ width: 80 }} />
        <input placeholder="URL" value={url} onChange={(e) => setUrl(e.target.value)} style={{ flex: 1, minWidth: 250 }} />
      </div>
      <div className="row" style={{ gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
        <input placeholder="Performance (0-100)" value={perf} onChange={(e) => setPerf(e.target.value)} type="number" min={0} max={100} style={{ width: 130 }} />
        <input placeholder="Accessibility (0-100)" value={access} onChange={(e) => setAccess(e.target.value)} type="number" min={0} max={100} style={{ width: 130 }} />
        <input placeholder="Best Practices (0-100)" value={bp} onChange={(e) => setBp(e.target.value)} type="number" min={0} max={100} style={{ width: 130 }} />
        <input placeholder="SEO (0-100)" value={seo} onChange={(e) => setSeo(e.target.value)} type="number" min={0} max={100} style={{ width: 130 }} />
      </div>
      <div className="row" style={{ gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
        <input placeholder="LCP (s)" value={lcp} onChange={(e) => setLcp(e.target.value)} type="number" step="0.1" style={{ width: 100 }} />
        <input placeholder="FID (ms)" value={fid} onChange={(e) => setFid(e.target.value)} type="number" style={{ width: 100 }} />
        <input placeholder="CLS" value={cls} onChange={(e) => setCls(e.target.value)} type="number" step="0.01" style={{ width: 100 }} />
        <input placeholder="FCP (s)" value={fcp} onChange={(e) => setFcp(e.target.value)} type="number" step="0.1" style={{ width: 100 }} />
        <input placeholder="TTFB (s)" value={ttfb} onChange={(e) => setTtfb(e.target.value)} type="number" step="0.1" style={{ width: 100 }} />
      </div>
      <button className="small" onClick={save} disabled={!pageId || !url}>Save Snapshot</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

type Tab = "overview" | "pagescores" | "check";

export default function PageSpeed() {
  const { active } = useWebsiteStore();
  const [tab, setTab] = useState<Tab>("overview");
  const [showForm, setShowForm] = useState(false);

  const summary = useAsync(() => active ? api.summary(active.id) : Promise.resolve(null), [active?.id]);
  const scores = useAsync(() => active ? api.pageScores(active.id) : Promise.resolve([]), [active?.id]);

  if (!active) return <p className="muted">Select a website to view page speed data.</p>;

  const s = summary.data as Record<string, number> | null;
  const pageScores: PageSpeedSnapshotOut[] = scores.data ?? [];

  return (
    <>
      <h2 className="page-title">⚡ Page Speed Insights</h2>
      <p className="page-sub">Track Core Web Vitals and Lighthouse scores per page.</p>

      <div className="row" style={{ gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
        {(["overview", "pagescores", "check"] as Tab[]).map((t) => (
          <button key={t} className={`small${tab === t ? "" : " secondary"}`} onClick={() => setTab(t)} style={{ fontWeight: tab === t ? 700 : 400 }}>
            {t === "overview" ? "📊 Overview" : t === "pagescores" ? "📋 Page Scores" : "➕ Record"}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {tab === "overview" && (
        <>
          {summary.loading ? <Loading /> : s ? (
            <>
              <div className="row" style={{ gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
                <div className="card" style={{ flex: 1, minWidth: 100, textAlign: "center" }}>
                  <div style={{ fontSize: 28, fontWeight: 700 }}>{s.pages_checked}</div>
                  <div className="muted" style={{ fontSize: 12 }}>Pages Checked</div>
                </div>
                <div className="card" style={{ flex: 1, minWidth: 100, textAlign: "center" }}>
                  <div style={{ fontSize: 28, fontWeight: 700, color: (s.avg_performance ?? 0) >= 90 ? "#22c55e" : "#f59e0b" }}>{s.avg_performance ?? "—"}</div>
                  <div className="muted" style={{ fontSize: 12 }}>Avg Performance</div>
                </div>
                <div className="card" style={{ flex: 1, minWidth: 100, textAlign: "center" }}>
                  <div style={{ fontSize: 28, fontWeight: 700, color: (s.avg_accessibility ?? 0) >= 90 ? "#22c55e" : "#f59e0b" }}>{s.avg_accessibility ?? "—"}</div>
                  <div className="muted" style={{ fontSize: 12 }}>Avg Accessibility</div>
                </div>
                <div className="card" style={{ flex: 1, minWidth: 100, textAlign: "center" }}>
                  <div style={{ fontSize: 28, fontWeight: 700, color: (s.avg_seo ?? 0) >= 90 ? "#22c55e" : "#f59e0b" }}>{s.avg_seo ?? "—"}</div>
                  <div className="muted" style={{ fontSize: 12 }}>Avg SEO</div>
                </div>
              </div>

              <h3>Core Web Vitals Averages</h3>
              <div className="row" style={{ gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
                <MetricCard label="LCP" value={s.avg_lcp} unit="s" good={2.5} target="Good: ≤2.5s" />
                <MetricCard label="FID" value={s.avg_fid} unit="ms" good={100} target="Good: ≤100ms" />
                <MetricCard label="CLS" value={s.avg_cls} unit="" good={0.1} target="Good: ≤0.1" />
                <MetricCard label="FCP" value={s.avg_fcp} unit="s" good={1.8} target="Good: ≤1.8s" />
                <MetricCard label="TTFB" value={s.avg_ttfb} unit="s" good={0.8} target="Good: ≤0.8s" />
              </div>
            </>
          ) : <p className="muted">No speed data yet. Record a check from the "Record" tab.</p>}
        </>
      )}

      {/* Page Scores Tab */}
      {tab === "pagescores" && (
        <div className="card">
          <h3>Page Scores (worst first)</h3>
          {pageScores.length === 0 ? (
            <p className="muted">No page scores recorded yet.</p>
          ) : (
            <table className="data">
              <thead>
                <tr><th>Page</th><th>Perf</th><th>Access</th><th>BP</th><th>SEO</th><th>LCP</th><th>CLS</th><th>Date</th></tr>
              </thead>
              <tbody>
                {pageScores.map((ps) => (
                  <tr key={ps.id}>
                    <td style={{ fontSize: 11, maxWidth: 250, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={ps.url}>
                      {ps.url.split("/").slice(2).join("/")}
                    </td>
                    <td><Badge value={ps.performance_score != null && ps.performance_score >= 90 ? "full" : ps.performance_score != null && ps.performance_score >= 50 ? "amber" : "red"} /> {ps.performance_score ?? "—"}</td>
                    <td>{ps.accessibility_score ?? "—"}</td>
                    <td>{ps.best_practices_score ?? "—"}</td>
                    <td>{ps.seo_score ?? "—"}</td>
                    <td>{ps.lcp != null ? `${ps.lcp}s` : "—"}</td>
                    <td>{ps.cls != null ? ps.cls.toFixed(3) : "—"}</td>
                    <td className="muted" style={{ fontSize: 10 }}>{new Date(ps.checked_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Record Tab */}
      {tab === "check" && (
        <CheckForm onDone={() => { setShowForm(false); summary.reload(); scores.reload(); }} />
      )}
    </>
  );
}
