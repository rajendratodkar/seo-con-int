import { useCallback, useState } from "react";
import { abTests as api } from "../services/backend";
import { Badge, ErrorBox, Loading } from "../components/common";
import { useAsync } from "../hooks/useAsync";
import { useWebsiteStore } from "../stores/websiteStore";
import type { ABTestDetail } from "../types";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const ELEMENTS = [
  { value: "title", label: "Title" },
  { value: "description", label: "Meta Description" },
  { value: "both", label: "Title + Description" },
];

const STATUS_COLORS: Record<string, string> = {
  draft: "gray",
  running: "blue",
  completed: "green",
  cancelled: "red",
};

const WINNER_COLORS: Record<string, string> = {
  control: "gray",
  variant: "green",
  inconclusive: "amber",
  insufficient_data: "gray",
};

// ---------------------------------------------------------------------------
// Test List
// ---------------------------------------------------------------------------

function TestList({ onSelect }: { onSelect: (id: number) => void }) {
  const { active } = useWebsiteStore();
  const list = useAsync(() => api.list(active?.id), [active?.id]);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [element, setElement] = useState("title");
  const [pageId, setPageId] = useState("");
  const [controlTitle, setControlTitle] = useState("");
  const [variantTitle, setVariantTitle] = useState("");
  const [error, setError] = useState<string | null>(null);

  const create = useCallback(async () => {
    if (!active || !pageId) return;
    setError(null);
    try {
      const result = await api.create({
        website_id: active.id,
        page_id: Number(pageId),
        name,
        element,
        control_title: controlTitle || null,
        variant_title: variantTitle || null,
      });
      setCreating(false);
      setName("");
      setPageId("");
      setControlTitle("");
      setVariantTitle("");
      onSelect(result.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [active, pageId, name, element, controlTitle, variantTitle, onSelect]);

  const remove = useCallback(async (id: number) => {
    try {
      await api.delete(id);
      await list.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [list]);

  if (list.loading) return <Loading />;
  if (list.error) return <ErrorBox message={list.error} />;

  const tests: ABTestDetail[] = list.data ?? [];

  return (
    <>
      <div className="row" style={{ justifyContent: "space-between", marginBottom: 12 }}>
        <h3 style={{ margin: 0 }}>A/B Tests {active ? `— ${active.name}` : ""}</h3>
        <button className="small" onClick={() => setCreating(!creating)}>
          {creating ? "Cancel" : "+ New Test"}
        </button>
      </div>

      {error && <ErrorBox message={error} />}

      {creating && (
        <div className="card" style={{ marginBottom: 12 }}>
          <div className="row" style={{ gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
            <input placeholder="Test name" value={name} onChange={(e) => setName(e.target.value)} style={{ width: 220 }} />
            <input placeholder="Page ID" value={pageId} onChange={(e) => setPageId(e.target.value)} style={{ width: 80 }} />
            <select value={element} onChange={(e) => setElement(e.target.value)}>
              {ELEMENTS.map((el) => (
                <option key={el.value} value={el.value}>{el.label}</option>
              ))}
            </select>
          </div>
          <div className="row" style={{ gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
            <input placeholder="Control title (current)" value={controlTitle} onChange={(e) => setControlTitle(e.target.value)} style={{ flex: 1, minWidth: 250 }} />
            <input placeholder="Variant title (new)" value={variantTitle} onChange={(e) => setVariantTitle(e.target.value)} style={{ flex: 1, minWidth: 250 }} />
          </div>
          <p className="muted" style={{ fontSize: 12, marginBottom: 8 }}>
            Leave control fields blank to use the current page values. The variant is the new version you want to test.
          </p>
          <button className="small" onClick={create} disabled={!name || !pageId}>Create Test</button>
        </div>
      )}

      {tests.length === 0 ? (
        <p className="muted">No A/B tests yet. Create one to start measuring SEO changes.</p>
      ) : (
        <table className="data">
          <thead>
            <tr><th>Test</th><th>Element</th><th>Status</th><th>Winner</th><th>Confidence</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {tests.map((t) => (
              <tr key={t.id}>
                <td><strong>{t.name}</strong></td>
                <td><Badge value={t.element} /></td>
                <td><span className="badge" style={{ background: STATUS_COLORS[t.status] ?? "#6b7280" }}>{t.status}</span></td>
                <td>
                  {t.winner ? (
                    <span className="badge" style={{ background: WINNER_COLORS[t.winner] ?? "#6b7280" }}>
                      {t.winner === "insufficient_data" ? "⏳ Collecting" : t.winner}
                    </span>
                  ) : "—"}
                </td>
                <td>{t.confidence != null ? `${(t.confidence * 100).toFixed(1)}%` : "—"}</td>
                <td>
                  <button className="small" onClick={() => onSelect(t.id)}>View</button>{" "}
                  {t.status === "draft" && (
                    <button className="small" onClick={async () => { await api.start(t.id); await list.reload(); }}>Start</button>
                  )}{" "}
                  {t.status === "running" && (
                    <>
                      <button className="small" onClick={async () => { await api.evaluate(t.id); await list.reload(); }}>Evaluate</button>{" "}
                      <button className="small" onClick={async () => { await api.cancel(t.id); await list.reload(); }}>Cancel</button>
                    </>
                  )}{" "}
                  {t.status !== "running" && (
                    <button className="small" onClick={() => remove(t.id)}>Delete</button>
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
// Test Detail
// ---------------------------------------------------------------------------

function TestDetail({ testId, onBack }: { testId: number; onBack: () => void }) {
  const detail = useAsync(() => api.get(testId), [testId]);
  const [error, setError] = useState<string | null>(null);
  const [collecting, setCollecting] = useState(false);

  const collect = useCallback(async () => {
    setCollecting(true);
    try {
      await api.collect(testId);
      await detail.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
    setCollecting(false);
  }, [testId, detail]);

  const evaluate = useCallback(async () => {
    try {
      await api.evaluate(testId);
      await detail.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [testId, detail]);

  if (detail.loading) return <Loading />;
  if (detail.error) return <ErrorBox message={detail.error} />;
  if (!detail.data) return <ErrorBox message="Test not found" />;

  const test: ABTestDetail = detail.data;
  const result = test.result_summary as Record<string, unknown> | null;

  return (
    <>
      <button className="small" onClick={onBack} style={{ marginBottom: 12 }}>← Back to tests</button>

      {error && <ErrorBox message={error} />}

      <h3>{test.name}</h3>
      <div className="row" style={{ gap: 12, marginBottom: 16 }}>
        <Badge value={test.status} />
        <Badge value={test.element} />
        {test.winner && <span className="badge" style={{ background: WINNER_COLORS[test.winner] ?? "#6b7280" }}>Winner: {test.winner}</span>}
        {test.confidence != null && <span className="muted">Confidence: {(test.confidence * 100).toFixed(1)}%</span>}
      </div>

      {/* Variants Comparison */}
      <div className="card" style={{ marginBottom: 16 }}>
        <h3>Variants</h3>
        <table className="data">
          <thead>
            <tr><th>Type</th><th>Title</th><th>Description</th></tr>
          </thead>
          <tbody>
            <tr>
              <td><Badge value="control" /></td>
              <td>{test.control?.title ?? "—"}</td>
              <td>{test.control?.description ?? "—"}</td>
            </tr>
            <tr>
              <td><Badge value="variant" /></td>
              <td>{test.variant?.title ?? "—"}</td>
              <td>{test.variant?.description ?? "—"}</td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Results */}
      {result && (result.winner as string) !== "insufficient_data" && (
        <div className="card" style={{ marginBottom: 16 }}>
          <h3>Results</h3>
          <div className="row" style={{ gap: 16, marginBottom: 12 }}>
            {(["control", "variant"] as const).map((vtype) => {
              const v = result[vtype] as Record<string, string | number> | undefined;
              return (
                <div key={vtype} style={{ flex: 1 }}>
                  <div className="muted" style={{ fontSize: 12 }}>{vtype === "control" ? "Control" : "Variant"}</div>
                  <div style={{ fontSize: 20, fontWeight: 700 }}>{String(v?.ctr)}% CTR</div>
                  <div className="muted" style={{ fontSize: 12 }}>
                    {String(v?.clicks)} clicks / {String(v?.impressions)} imp
                    &middot; Position {String(v?.position)}
                  </div>
                </div>
              );
            })}
          </div>
          <div className="row" style={{ gap: 16 }}>
            <div className="muted" style={{ fontSize: 12 }}>
              CTR difference: <strong style={{ color: (result.ctr_diff_pct as number) > 0 ? "#22c55e" : "#ef4444" }}>
                {(result.ctr_diff_pct as number) > 0 ? "+" : ""}{String(result.ctr_diff_pct)}%
              </strong>
            </div>
            <div className="muted" style={{ fontSize: 12 }}>
              z-score: {String(result.z_score)} &middot; p-value: {String(result.p_value)}
            </div>
            <div className="muted" style={{ fontSize: 12 }}>
              Days: {String(result.days_collected)} / {String(result.min_days_required)}
            </div>
          </div>
        </div>
      )}

      {result && (result.winner as string) === "insufficient_data" && (
        <div className="card" style={{ marginBottom: 16, background: "#fffbeb", border: "1px solid #f59e0b" }}>
          <h3 style={{ margin: "0 0 8px" }}>⏳ Collecting Data</h3>
          <p className="muted">
            {String(result.days_collected ?? 0)} of {String(result.min_days_required ?? 7)} days collected.
            {typeof result.reason === "string" ? ` ${result.reason}` : ""}
          </p>
        </div>
      )}

      {/* Actions */}
      <div className="row" style={{ gap: 8 }}>
        {test.status === "running" && (
          <>
            <button className="small" onClick={collect} disabled={collecting}>
              {collecting ? "Collecting…" : "Collect Data"}
            </button>
            <button className="small" onClick={evaluate}>Evaluate Results</button>
          </>
        )}
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function ABTesting() {
  const [selectedId, setSelectedId] = useState<number | null>(null);

  if (selectedId) {
    return <TestDetail testId={selectedId} onBack={() => setSelectedId(null)} />;
  }

  return (
    <>
      <h2 className="page-title">🧪 A/B Testing</h2>
      <p className="page-sub">
        Test title and description changes, measure their impact on CTR and rankings using real Search Console data.
      </p>
      <TestList onSelect={(id) => setSelectedId(id)} />
    </>
  );
}
