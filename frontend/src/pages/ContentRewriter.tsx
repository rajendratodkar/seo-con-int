import { useCallback, useState } from "react";
import { rewriter as api } from "../services/backend";
import { Badge, ErrorBox, Loading } from "../components/common";
import { useAsync } from "../hooks/useAsync";
import { useWebsiteStore } from "../stores/websiteStore";
import type { RewriteOut } from "../types";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const CONTENT_TYPES = [
  { value: "title", label: "Page Title", desc: "Optimize for clicks and keywords (max 60 chars)", icon: "📝" },
  { value: "description", label: "Meta Description", desc: "Compelling snippet for SERPs (120-155 chars)", icon: "📋" },
  { value: "heading", label: "Heading (H1-H3)", desc: "Engaging, keyword-rich headings", icon: "📑" },
  { value: "custom", label: "Custom Text", desc: "Any text — product descriptions, CTAs, etc.", icon: "✏️" },
];

// ---------------------------------------------------------------------------
// Rewrite Form
// ---------------------------------------------------------------------------

function RewriteForm({ onResult }: { onResult: (result: { id: number; original: string; rewrites: string[]; provider: string }) => void }) {
  const { active } = useWebsiteStore();
  const [contentType, setContentType] = useState("title");
  const [original, setOriginal] = useState("");
  const [context, setContext] = useState("");
  const [numVariations, setNumVariations] = useState(3);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const rewrite = useCallback(async () => {
    if (!original.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await api.rewrite({
        website_id: active?.id,
        content_type: contentType,
        original_text: original,
        context: context || undefined,
        num_variations: numVariations,
      });
      onResult(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
    setLoading(false);
  }, [active, contentType, original, context, numVariations, onResult]);

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <h3>Rewrite Content</h3>
      {error && <ErrorBox message={error} />}

      {/* Content type selector */}
      <div className="row" style={{ gap: 8, marginBottom: 12, flexWrap: "wrap" }}>
        {CONTENT_TYPES.map((ct) => (
          <button
            key={ct.value}
            className={`small${contentType === ct.value ? "" : " secondary"}`}
            onClick={() => setContentType(ct.value)}
            style={{ fontWeight: contentType === ct.value ? 700 : 400 }}
          >
            {ct.icon} {ct.label}
          </button>
        ))}
      </div>

      <p className="muted" style={{ fontSize: 12, marginBottom: 8 }}>
        {CONTENT_TYPES.find((ct) => ct.value === contentType)?.desc}
      </p>

      {/* Input */}
      <textarea
        value={original}
        onChange={(e) => setOriginal(e.target.value)}
        rows={3}
        placeholder={contentType === "title" ? "Enter your current page title..." :
                      contentType === "description" ? "Enter your current meta description..." :
                      contentType === "heading" ? "Enter your current heading..." :
                      "Enter the text you want to optimize..."}
        style={{ width: "100%", marginBottom: 8 }}
      />

      <div className="row" style={{ gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
        <input
          placeholder="Target keyword or topic (optional)"
          value={context}
          onChange={(e) => setContext(e.target.value)}
          style={{ flex: 1, minWidth: 250 }}
        />
        <select value={numVariations} onChange={(e) => setNumVariations(parseInt(e.target.value))}>
          {[1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>{n} variations</option>)}
        </select>
      </div>

      <button className="small" onClick={rewrite} disabled={!original.trim() || loading}>
        {loading ? "🔄 Rewriting..." : "✨ Generate Rewrites"}
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Rewrite Results
// ---------------------------------------------------------------------------

function RewriteResults({ result, onClear }: { result: { id: number; original: string; rewrites: string[]; provider: string }; onClear: () => void }) {
  const [selected, setSelected] = useState<number | null>(null);
  const [copied, setCopied] = useState<number | null>(null);

  const copyToClipboard = useCallback((text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopied(index);
    setTimeout(() => setCopied(null), 1500);
  }, []);

  const selectAndApply = useCallback(async (index: number) => {
    try {
      await api.select(result.id, index);
      await api.apply(result.id);
      setSelected(index);
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  }, [result.id]);

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="row" style={{ justifyContent: "space-between", marginBottom: 12 }}>
        <h3 style={{ margin: 0 }}>Rewrite Options</h3>
        <button className="small secondary" onClick={onClear}>New Rewrite</button>
      </div>

      {/* Original */}
      <div style={{ padding: 8, background: "#f9fafb", borderRadius: 6, marginBottom: 12, border: "1px solid #e5e7eb" }}>
        <div className="muted" style={{ fontSize: 11, marginBottom: 2 }}>Original:</div>
        <div style={{ fontSize: 14 }}>{result.original}</div>
      </div>

      {/* Options */}
      {result.rewrites.map((rewrite, i) => (
        <div key={i} style={{
          padding: 12,
          marginBottom: 8,
          borderRadius: 6,
          border: selected === i ? "2px solid #22c55e" : "1px solid #e5e7eb",
          background: selected === i ? "#f0fdf4" : "white",
          cursor: "pointer",
        }}
          onClick={() => setSelected(i)}
        >
          <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ fontSize: 14, flex: 1 }}>{rewrite}</div>
            <div className="row" style={{ gap: 4 }}>
              <span style={{ fontSize: 11, color: "#6b7280" }}>{rewrite.length} chars</span>
              <button
                className="small"
                onClick={(e) => { e.stopPropagation(); copyToClipboard(rewrite, i); }}
                style={{ fontSize: 11 }}
              >
                {copied === i ? "✓" : "📋"}
              </button>
              <button
                className="small"
                onClick={(e) => { e.stopPropagation(); selectAndApply(i); }}
                style={{ fontSize: 11, color: "#22c55e" }}
              >
                Use this
              </button>
            </div>
          </div>
          {selected === i && (
            <div style={{ marginTop: 8, fontSize: 11, color: "#22c55e" }}>
              ✓ Selected — copied to clipboard
            </div>
          )}
        </div>
      ))}

      <div className="muted" style={{ fontSize: 11, marginTop: 8 }}>
        Provider: {result.provider} · Click an option to select it, or copy to clipboard.
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// History Tab
// ---------------------------------------------------------------------------

function HistoryTab() {
  const { active } = useWebsiteStore();
  const history = useAsync(() => api.history(active?.id), [active?.id]);

  if (history.loading) return <Loading />;
  if (history.error) return <ErrorBox message={history.error} />;

  const items: RewriteOut[] = history.data ?? [];

  return (
    <div className="card">
      <h3>Rewrite History</h3>
      {items.length === 0 ? (
        <p className="muted">No rewrites yet. Generate your first rewrite from the "Rewrite" tab.</p>
      ) : (
        <table className="data">
          <thead>
            <tr><th>Date</th><th>Type</th><th>Original</th><th>Rewrites</th><th>Provider</th><th>Status</th></tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td className="muted" style={{ fontSize: 11, whiteSpace: "nowrap" }}>{new Date(item.created_at).toLocaleDateString()}</td>
                <td><Badge value={item.content_type} /></td>
                <td style={{ maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{item.original_text}</td>
                <td>{item.rewrites.length}</td>
                <td className="muted" style={{ fontSize: 11 }}>{item.provider ?? "—"}</td>
                <td>{item.applied ? <Badge value="applied" /> : item.selected_index != null ? <Badge value="selected" /> : <Badge value="pending" />}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

type Tab = "rewrite" | "history";

export default function ContentRewriter() {
  const [tab, setTab] = useState<Tab>("rewrite");
  const [result, setResult] = useState<{ id: number; original: string; rewrites: string[]; provider: string } | null>(null);

  return (
    <>
      <h2 className="page-title">✨ Content Rewriter</h2>
      <p className="page-sub">AI-powered optimization for titles, descriptions, and headings to improve CTR.</p>

      <div className="row" style={{ gap: 4, marginBottom: 16 }}>
        {([
          ["rewrite", "Rewrite"],
          ["history", "History"],
        ] as [Tab, string][]).map(([key, label]) => (
          <button key={key} className={`small${tab === key ? "" : " secondary"}`} onClick={() => setTab(key)} style={{ fontWeight: tab === key ? 700 : 400 }}>
            {label}
          </button>
        ))}
      </div>

      {tab === "rewrite" && (
        <>
          {result ? (
            <RewriteResults result={result} onClear={() => setResult(null)} />
          ) : (
            <RewriteForm onResult={setResult} />
          )}
        </>
      )}

      {tab === "history" && <HistoryTab />}
    </>
  );
}
