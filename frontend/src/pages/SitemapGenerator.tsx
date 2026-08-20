import { useCallback, useState } from "react";
import { sitemapGen as api } from "../services/backend";
import { Badge, ErrorBox, Loading } from "../components/common";
import { useAsync } from "../hooks/useAsync";
import { useWebsiteStore } from "../stores/websiteStore";
import type { SitemapOverrideOut } from "../types";

// ---------------------------------------------------------------------------
// Settings Tab
// ---------------------------------------------------------------------------

function SettingsTab() {
  const { active } = useWebsiteStore();
  const settings = useAsync(() => active ? api.settings(active.id) : Promise.resolve(null), [active?.id]);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const [priority, setPriority] = useState("0.5");
  const [changefreq, setChangefreq] = useState("weekly");
  const [maxUrls, setMaxUrls] = useState("50000");
  const [excludePatterns, setExcludePatterns] = useState("");

  const updateSettings = useCallback(async () => {
    if (!active) return;
    try {
      const patterns = excludePatterns.split("\n").filter((l) => l.trim());
      await api.updateSettings(active.id, {
        default_priority: parseFloat(priority),
        default_changefreq: changefreq,
        max_urls: parseInt(maxUrls),
        exclude_patterns: patterns,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [active, priority, changefreq, maxUrls, excludePatterns]);

  if (settings.loading) return <Loading />;

  return (
    <div className="card">
      <h3>Sitemap Settings</h3>
      {error && <ErrorBox message={error} />}
      {saved && <div style={{ color: "#22c55e", fontSize: 12, marginBottom: 8 }}>✓ Settings saved</div>}

      <div className="row" style={{ gap: 16, flexWrap: "wrap", marginBottom: 12 }}>
        <div>
          <label style={{ fontSize: 12, display: "block", marginBottom: 2 }}>Default Priority (0-1)</label>
          <input type="number" value={priority} onChange={(e) => setPriority(e.target.value)} min={0} max={1} step={0.1} style={{ width: 80 }} />
        </div>
        <div>
          <label style={{ fontSize: 12, display: "block", marginBottom: 2 }}>Change Frequency</label>
          <select value={changefreq} onChange={(e) => setChangefreq(e.target.value)}>
            {["always", "hourly", "daily", "weekly", "monthly", "yearly", "never"].map((f) => (
              <option key={f} value={f}>{f}</option>
            ))}
          </select>
        </div>
        <div>
          <label style={{ fontSize: 12, display: "block", marginBottom: 2 }}>Max URLs</label>
          <input type="number" value={maxUrls} onChange={(e) => setMaxUrls(e.target.value)} min={1} max={500000} style={{ width: 100 }} />
        </div>
      </div>

      <div style={{ marginBottom: 12 }}>
        <label style={{ fontSize: 12, display: "block", marginBottom: 2 }}>Exclude URL Patterns (one per line, supports wildcards)</label>
        <textarea
          value={excludePatterns}
          onChange={(e) => setExcludePatterns(e.target.value)}
          rows={3}
          placeholder={"https://example.com/admin/*\nhttps://example.com/api/*"}
          style={{ width: "100%", fontFamily: "monospace", fontSize: 11 }}
        />
      </div>

      <button className="small" onClick={updateSettings}>Save Settings</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Overrides Tab
// ---------------------------------------------------------------------------

function OverridesTab() {
  const { active } = useWebsiteStore();
  const overrides = useAsync(() => active ? api.overrides(active.id) : Promise.resolve([]), [active?.id]);
  const [error, setError] = useState<string | null>(null);
  const [pattern, setPattern] = useState("");
  const [priority, setPriority] = useState("");
  const [changefreq, setChangefreq] = useState("");
  const [include, setInclude] = useState(true);

  const add = useCallback(async () => {
    if (!active || !pattern.trim()) return;
    try {
      await api.addOverride(active.id, pattern, priority ? parseFloat(priority) : undefined, changefreq || undefined, include);
      setPattern("");
      setPriority("");
      setChangefreq("");
      await overrides.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [active, pattern, priority, changefreq, include, overrides]);

  const remove = useCallback(async (id: number) => {
    try {
      await api.deleteOverride(id);
      await overrides.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [overrides]);

  if (overrides.loading) return <Loading />;

  const list: SitemapOverrideOut[] = overrides.data ?? [];

  return (
    <div className="card">
      <h3>URL Pattern Overrides</h3>
      <p className="muted" style={{ fontSize: 12, marginBottom: 8 }}>Customize priority and change frequency for URL patterns (uses wildcards like <code>/blog/*</code>).</p>
      {error && <ErrorBox message={error} />}

      <div className="row" style={{ gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
        <input placeholder="URL pattern (e.g. /blog/*)" value={pattern} onChange={(e) => setPattern(e.target.value)} style={{ flex: 1, minWidth: 200 }} />
        <input placeholder="Priority" value={priority} onChange={(e) => setPriority(e.target.value)} type="number" min={0} max={1} step={0.1} style={{ width: 80 }} />
        <select value={changefreq} onChange={(e) => setChangefreq(e.target.value)}>
          <option value="">Default</option>
          {["always", "hourly", "daily", "weekly", "monthly", "yearly", "never"].map((f) => (
            <option key={f} value={f}>{f}</option>
          ))}
        </select>
        <label style={{ fontSize: 12, display: "flex", alignItems: "center", gap: 4 }}>
          <input type="checkbox" checked={include} onChange={(e) => setInclude(e.target.checked)} /> Include
        </label>
        <button className="small" onClick={add} disabled={!pattern.trim()}>Add</button>
      </div>

      {list.length > 0 && (
        <table className="data">
          <thead>
            <tr><th>Pattern</th><th>Priority</th><th>Change Freq</th><th>Include</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {list.map((o) => (
              <tr key={o.id}>
                <td className="mono" style={{ fontSize: 12 }}>{o.url_pattern}</td>
                <td>{o.priority ?? "—"}</td>
                <td>{o.changefreq ?? "default"}</td>
                <td>{o.include ? <Badge value="yes" /> : <Badge value="no" />}</td>
                <td><button className="small" onClick={() => remove(o.id)}>Delete</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Preview Tab
// ---------------------------------------------------------------------------

function PreviewTab() {
  const { active } = useWebsiteStore();
  const [preview, setPreview] = useState<{ url_count: number; excluded_count: number; total_pages: number; xml_preview: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = useCallback(async () => {
    if (!active) return;
    setLoading(true);
    setError(null);
    try {
      const r = await api.preview(active.id);
      setPreview(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
    setLoading(false);
  }, [active]);

  const download = useCallback(async () => {
    if (!active) return;
    try {
      const xml = await api.generate(active.id);
      const blob = new Blob([xml as unknown as BlobPart], { type: "application/xml" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "sitemap.xml";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [active]);

  return (
    <div className="card">
      <h3>Preview & Generate</h3>
      {error && <ErrorBox message={error} />}

      <div className="row" style={{ gap: 8, marginBottom: 12 }}>
        <button className="small" onClick={generate} disabled={loading}>
          {loading ? "Generating…" : "👁 Preview"}
        </button>
        <button className="small" onClick={download}>⬇ Download sitemap.xml</button>
      </div>

      {preview && (
        <>
          <div className="row" style={{ gap: 16, marginBottom: 12 }}>
            <div className="card" style={{ flex: 1, textAlign: "center" }}>
              <div style={{ fontSize: 24, fontWeight: 700, color: "#22c55e" }}>{preview.url_count}</div>
              <div className="muted" style={{ fontSize: 11 }}>URLs Included</div>
            </div>
            <div className="card" style={{ flex: 1, textAlign: "center" }}>
              <div style={{ fontSize: 24, fontWeight: 700, color: "#ef4444" }}>{preview.excluded_count}</div>
              <div className="muted" style={{ fontSize: 11 }}>Excluded</div>
            </div>
            <div className="card" style={{ flex: 1, textAlign: "center" }}>
              <div style={{ fontSize: 24, fontWeight: 700 }}>{preview.total_pages}</div>
              <div className="muted" style={{ fontSize: 11 }}>Total Pages</div>
            </div>
          </div>

          <h4>XML Preview</h4>
          <pre style={{
            background: "#f9fafb",
            padding: 12,
            borderRadius: 6,
            fontSize: 10,
            overflow: "auto",
            maxHeight: 300,
            border: "1px solid #e5e7eb",
          }}>
            {preview.xml_preview}
          </pre>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

type Tab = "settings" | "overrides" | "preview";

export default function SitemapGenerator() {
  const [tab, setTab] = useState<Tab>("preview");

  return (
    <>
      <h2 className="page-title">🗺️ Sitemap Generator</h2>
      <p className="page-sub">Generate XML sitemaps from crawled pages with priority and changefreq settings.</p>

      <div className="row" style={{ gap: 4, marginBottom: 16 }}>
        {([
          ["settings", "Settings"],
          ["overrides", "Overrides"],
          ["preview", "Preview & Generate"],
        ] as [Tab, string][]).map(([key, label]) => (
          <button key={key} className={`small${tab === key ? "" : " secondary"}`} onClick={() => setTab(key)} style={{ fontWeight: tab === key ? 700 : 400 }}>
            {label}
          </button>
        ))}
      </div>

      {tab === "settings" && <SettingsTab />}
      {tab === "overrides" && <OverridesTab />}
      {tab === "preview" && <PreviewTab />}
    </>
  );
}
