import { useCallback, useState } from "react";
import { backlinks as api } from "../services/backend";
import { Badge, ErrorBox, Loading } from "../components/common";
import { useAsync } from "../hooks/useAsync";
import { useWebsiteStore } from "../stores/websiteStore";
import type { BacklinkOut } from "../types";

// ---------------------------------------------------------------------------
// Profile Tab
// ---------------------------------------------------------------------------

function ProfileTab() {
  const { active } = useWebsiteStore();
  const profile = useAsync(() => active ? api.profile(active.id) : Promise.resolve(null), [active?.id]);

  if (profile.loading) return <Loading />;
  if (profile.error) return <ErrorBox message={profile.error} />;

  const p = profile.data;
  if (!p) return <p className="muted">No data</p>;

  return (
    <>
      <div className="row" style={{ gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
        <div className="card" style={{ flex: 1, minWidth: 120, textAlign: "center" }}>
          <div style={{ fontSize: 28, fontWeight: 700 }}>{p.total_links}</div>
          <div className="muted" style={{ fontSize: 12 }}>Total Links</div>
        </div>
        <div className="card" style={{ flex: 1, minWidth: 120, textAlign: "center" }}>
          <div style={{ fontSize: 28, fontWeight: 700, color: "#22c55e" }}>{p.active_links}</div>
          <div className="muted" style={{ fontSize: 12 }}>Active</div>
        </div>
        <div className="card" style={{ flex: 1, minWidth: 120, textAlign: "center" }}>
          <div style={{ fontSize: 28, fontWeight: 700, color: "#ef4444" }}>{p.lost_links}</div>
          <div className="muted" style={{ fontSize: 12 }}>Lost</div>
        </div>
        <div className="card" style={{ flex: 1, minWidth: 120, textAlign: "center" }}>
          <div style={{ fontSize: 28, fontWeight: 700, color: "#f59e0b" }}>{p.broken_links}</div>
          <div className="muted" style={{ fontSize: 12 }}>Broken</div>
        </div>
        <div className="card" style={{ flex: 1, minWidth: 120, textAlign: "center" }}>
          <div style={{ fontSize: 28, fontWeight: 700 }}>{p.unique_domains}</div>
          <div className="muted" style={{ fontSize: 12 }}>Unique Domains</div>
        </div>
        <div className="card" style={{ flex: 1, minWidth: 120, textAlign: "center" }}>
          <div style={{ fontSize: 28, fontWeight: 700 }}>{p.avg_domain_authority ?? "—"}</div>
          <div className="muted" style={{ fontSize: 12 }}>Avg DA</div>
        </div>
      </div>

      <div className="row" style={{ gap: 16 }}>
        {/* Top Domains */}
        <div className="card" style={{ flex: 1 }}>
          <h3>Top Linking Domains</h3>
          {p.top_domains.length === 0 ? (
            <p className="muted">No backlinks yet</p>
          ) : (
            <table className="data">
              <thead><tr><th>Domain</th><th>Links</th><th>Max DA</th></tr></thead>
              <tbody>
                {p.top_domains.map((d, i) => (
                  <tr key={i}>
                    <td><strong>{d.source_domain}</strong></td>
                    <td>{d.links}</td>
                    <td>{d.max_da ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Recent Changes */}
        <div className="card" style={{ flex: 1 }}>
          <h3>Recent Changes</h3>
          {p.recent_changes.length === 0 ? (
            <p className="muted">No changes recorded</p>
          ) : (
            <table className="data">
              <thead><tr><th>Date</th><th>Type</th><th>Source</th></tr></thead>
              <tbody>
                {p.recent_changes.map((c) => (
                  <tr key={c.id}>
                    <td className="muted" style={{ fontSize: 11 }}>{new Date(c.detected_at).toLocaleDateString()}</td>
                    <td><Badge value={c.change_type} /></td>
                    <td style={{ fontSize: 11, maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{c.source_url}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// Links Tab
// ---------------------------------------------------------------------------

function LinksTab() {
  const { active } = useWebsiteStore();
  const [filterStatus, setFilterStatus] = useState<string | undefined>(undefined);
  const links = useAsync(
    () => active ? api.list(active.id, filterStatus) : Promise.resolve([]),
    [active?.id, filterStatus],
  );
  const [showForm, setShowForm] = useState(false);
  const [sourceUrl, setSourceUrl] = useState("");
  const [targetUrl, setTargetUrl] = useState("");
  const [anchorText, setAnchorText] = useState("");
  const [da, setDa] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [importText, setImportText] = useState("");

  const add = useCallback(async () => {
    if (!active || !sourceUrl || !targetUrl) return;
    setError(null);
    try {
      await api.add({
        website_id: active.id,
        source_url: sourceUrl,
        target_url: targetUrl,
        anchor_text: anchorText || undefined,
        domain_authority: da ? parseInt(da) : undefined,
      });
      setSourceUrl("");
      setTargetUrl("");
      setAnchorText("");
      setDa("");
      setShowForm(false);
      await links.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [active, sourceUrl, targetUrl, anchorText, da, links]);

  const doImport = useCallback(async () => {
    if (!active || !importText.trim()) return;
    try {
      const lines = importText.trim().split("\n").filter(Boolean);
      const backlinks = lines.map((line) => {
        const parts = line.split(",").map((s) => s.trim());
        return { source_url: parts[0], target_url: parts[1], anchor_text: parts[2] || undefined };
      });
      const result = await api.import(active.id, backlinks);
      alert(`Imported ${result.imported} backlinks`);
      setImportText("");
      await links.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [active, importText, links]);

  const remove = useCallback(async (id: number) => {
    try {
      await api.delete(id);
      await links.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [links]);

  const markLost = useCallback(async (id: number) => {
    try {
      await api.update(id, { status: "lost" });
      await links.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [links]);

  if (links.loading) return <Loading />;
  if (links.error) return <ErrorBox message={links.error} />;

  const list: BacklinkOut[] = links.data ?? [];

  return (
    <>
      <div className="row" style={{ justifyContent: "space-between", marginBottom: 12 }}>
        <h3 style={{ margin: 0 }}>Backlinks {active ? `— ${active.name}` : ""}</h3>
        <div className="row" style={{ gap: 8 }}>
          <select value={filterStatus ?? ""} onChange={(e) => setFilterStatus(e.target.value || undefined)} style={{ fontSize: 12 }}>
            <option value="">All</option>
            <option value="active">Active</option>
            <option value="lost">Lost</option>
            <option value="broken">Broken</option>
          </select>
          <button className="small" onClick={() => setShowForm(!showForm)}>
            {showForm ? "Cancel" : "+ Add Backlink"}
          </button>
        </div>
      </div>

      {error && <ErrorBox message={error} />}

      {showForm && (
        <div className="card" style={{ marginBottom: 12 }}>
          <div className="row" style={{ gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
            <input placeholder="Source URL" value={sourceUrl} onChange={(e) => setSourceUrl(e.target.value)} style={{ flex: 1, minWidth: 250 }} />
            <input placeholder="Target URL (your page)" value={targetUrl} onChange={(e) => setTargetUrl(e.target.value)} style={{ flex: 1, minWidth: 250 }} />
          </div>
          <div className="row" style={{ gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
            <input placeholder="Anchor text" value={anchorText} onChange={(e) => setAnchorText(e.target.value)} style={{ width: 200 }} />
            <input placeholder="Domain Authority (0-100)" value={da} onChange={(e) => setDa(e.target.value)} type="number" min={0} max={100} style={{ width: 180 }} />
            <button className="small" onClick={add} disabled={!sourceUrl || !targetUrl}>Add</button>
          </div>
          <details style={{ marginTop: 8 }}>
            <summary style={{ fontSize: 12, cursor: "pointer" }}>Bulk Import (CSV)</summary>
            <textarea
              value={importText}
              onChange={(e) => setImportText(e.target.value)}
              rows={4}
              placeholder={"https://other.com/article,https://mysite.com/page,anchor text\nhttps://blog.com/post,https://mysite.com/other"}
              style={{ width: "100%", fontFamily: "monospace", fontSize: 11, marginTop: 4 }}
            />
            <button className="small" onClick={doImport} disabled={!importText.trim()} style={{ marginTop: 4 }}>Import</button>
          </details>
        </div>
      )}

      {list.length === 0 ? (
        <p className="muted">No backlinks tracked. Add one manually or import from CSV.</p>
      ) : (
        <table className="data">
          <thead>
            <tr><th>Source</th><th>Target</th><th>Anchor</th><th>DA</th><th>Status</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {list.map((b) => (
              <tr key={b.id}>
                <td style={{ fontSize: 11, maxWidth: 250, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={b.source_url}>
                  {b.source_domain}
                </td>
                <td style={{ fontSize: 11, maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={b.target_url}>
                  {b.target_url.split("/").slice(2).join("/")}
                </td>
                <td>{b.anchor_text ?? "—"}</td>
                <td>{b.domain_authority ?? "—"}</td>
                <td><Badge value={b.status} /></td>
                <td>
                  {b.status === "active" && (
                    <button className="small" onClick={() => markLost(b.id)}>Mark Lost</button>
                  )}{" "}
                  <button className="small" onClick={() => remove(b.id)}>Delete</button>
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

type Tab = "profile" | "links";

export default function Backlinks() {
  const [tab, setTab] = useState<Tab>("profile");

  return (
    <>
      <h2 className="page-title">🔗 Backlink Monitor</h2>
      <p className="page-sub">Track inbound links, domain authority, and link changes over time.</p>

      <div className="row" style={{ gap: 4, marginBottom: 16 }}>
        {([
          ["profile", "Profile"],
          ["links", "Links"],
        ] as [Tab, string][]).map(([key, label]) => (
          <button key={key} className={`small${tab === key ? "" : " secondary"}`} onClick={() => setTab(key)} style={{ fontWeight: tab === key ? 700 : 400 }}>
            {label}
          </button>
        ))}
      </div>

      {tab === "profile" && <ProfileTab />}
      {tab === "links" && <LinksTab />}
    </>
  );
}
