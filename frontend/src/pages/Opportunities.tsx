import { useState } from "react";
import { findings, opportunities } from "../services/backend";
import { useWebsiteStore } from "../stores/websiteStore";
import { AiBadge, Badge, Empty, ErrorBox, Loading } from "../components/common";
import { useAsync } from "../hooks/useAsync";

export default function Opportunities() {
  const { active } = useWebsiteStore();
  const opps = useAsync(async () => (active ? opportunities.list(active.id) : null), [active?.id]);
  const open = useAsync(async () => (active ? findings.list(active.id) : null), [active?.id]);
  const [error, setError] = useState<string | null>(null);

  if (!active) return <Empty text="Add a website first." />;
  if (opps.loading || open.loading) return <Loading />;

  const runAnalysis = async () => {
    setError(null);
    try {
      const result = await findings.analyze(active.id);
      alert(`Analyzed ${result.pages_analyzed} pages · ${result.findings_saved} findings stored.`);
      await open.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const setStatus = async (id: number, status: string) => {
    await findings.setStatus(id, status);
    await open.reload();
  };

  return (
    <>
      <h2 className="page-title">Opportunities &amp; Findings</h2>
      <p className="page-sub">Every recommendation shows What · Why · Evidence · Confidence.</p>

      <div className="row">
        <button className="primary" onClick={runAnalysis}>Run SEO analysis</button>
        {error && <ErrorBox message={error} />}
      </div>

      <div className="card">
        <h3>Data-based opportunities (Search Console strike zone)</h3>
        {opps.data && opps.data.items.length > 0 ? (
          <table className="data">
            <thead><tr><th>Page</th><th>Recommendation</th><th>Evidence</th><th>Confidence</th></tr></thead>
            <tbody>
              {opps.data.items.map((o, i) => (
                <tr key={i}>
                  <td className="mono">{o.page_url}</td>
                  <td>{o.recommendation}</td>
                  <td>{o.evidence}</td>
                  <td><Badge value={o.confidence} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="muted">No opportunities — need Search Console data (≥500 impressions, position 4–12).</p>
        )}
      </div>

      <div className="card">
        <h3>Open findings</h3>
        {open.data && open.data.items.length > 0 ? (
          <table className="data">
            <thead><tr><th>Recommendation</th><th>Why</th><th>Type</th><th>Severity</th><th></th></tr></thead>
            <tbody>
              {open.data.items.map((f) => (
                <tr key={f.id}>
                  <td>{f.recommendation}</td>
                  <td className="muted">{f.why}</td>
                  <td>{f.rec_type === "ai_suggestion" ? <AiBadge /> : <Badge value={f.rec_type} />}</td>
                  <td><Badge value={f.severity} /></td>
                  <td>
                    <button className="small" onClick={() => setStatus(f.id, "accepted")}>Accept</button>{" "}
                    <button className="small" onClick={() => setStatus(f.id, "dismissed")}>Dismiss</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="muted">No open findings. Run an analysis above.</p>
        )}
      </div>
    </>
  );
}
