import { useCallback, useState } from "react";
import { keywordClusters as api } from "../services/backend";
import { Badge, ErrorBox, Loading } from "../components/common";
import { useAsync } from "../hooks/useAsync";
import { useWebsiteStore } from "../stores/websiteStore";
import type { ClusterOut, ClusterDetail } from "../types";

// ---------------------------------------------------------------------------
// Cluster List
// ---------------------------------------------------------------------------

function ClusterList({ onSelect }: { onSelect: (id: number) => void }) {
  const { active } = useWebsiteStore();
  const list = useAsync(() => active ? api.list(active.id) : Promise.resolve([]), [active?.id]);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [pillar, setPillar] = useState("");
  const [autoRunning, setAutoRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const create = useCallback(async () => {
    if (!active) return;
    setError(null);
    try {
      await api.create(active.id, name, description || undefined, pillar || undefined);
      setShowForm(false);
      setName("");
      setDescription("");
      setPillar("");
      await list.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [active, name, description, pillar, list]);

  const autoCluster = useCallback(async () => {
    if (!active) return;
    setAutoRunning(true);
    setError(null);
    try {
      const result = await api.autoCluster(active.id);
      alert(`Created ${result.clusters_created} clusters from ${result.keywords_processed} keywords (${result.keywords_clustered} clustered).`);
      await list.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
    setAutoRunning(false);
  }, [active, list]);

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

  const clusters: ClusterOut[] = list.data ?? [];

  return (
    <>
      <div className="row" style={{ justifyContent: "space-between", marginBottom: 12 }}>
        <h3 style={{ margin: 0 }}>Keyword Clusters {active ? `— ${active.name}` : ""}</h3>
        <div className="row" style={{ gap: 8 }}>
          <button className="small" onClick={autoCluster} disabled={autoRunning}>
            {autoRunning ? "Clustering…" : "🤖 Auto-Cluster"}
          </button>
          <button className="small" onClick={() => setShowForm(!showForm)}>
            {showForm ? "Cancel" : "+ New Cluster"}
          </button>
        </div>
      </div>

      {error && <ErrorBox message={error} />}

      {showForm && (
        <div className="card" style={{ marginBottom: 12 }}>
          <div className="row" style={{ gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
            <input placeholder="Cluster name" value={name} onChange={(e) => setName(e.target.value)} style={{ width: 220 }} />
            <input placeholder="Pillar keyword (optional)" value={pillar} onChange={(e) => setPillar(e.target.value)} style={{ width: 220 }} />
          </div>
          <input placeholder="Description (optional)" value={description} onChange={(e) => setDescription(e.target.value)} style={{ width: "100%", marginBottom: 8 }} />
          <button className="small" onClick={create} disabled={!name}>Create Cluster</button>
        </div>
      )}

      {clusters.length === 0 ? (
        <p className="muted">No clusters yet. Create one manually or use Auto-Cluster to group keywords from Search Console data.</p>
      ) : (
        <table className="data">
          <thead>
            <tr><th>Cluster</th><th>Keywords</th><th>Pillar</th><th>Created</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {clusters.map((c) => (
              <tr key={c.id}>
                <td>
                  <strong>{c.name}</strong>
                  {c.description && <div className="muted" style={{ fontSize: 11 }}>{c.description}</div>}
                </td>
                <td><Badge value={`${c.keyword_count} keywords`} /></td>
                <td>{c.pillar_keyword ?? "—"}</td>
                <td className="muted" style={{ fontSize: 11 }}>{new Date(c.created_at).toLocaleDateString()}</td>
                <td>
                  <button className="small" onClick={() => onSelect(c.id)}>View</button>{" "}
                  <button className="small" onClick={() => remove(c.id)}>Delete</button>
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
// Cluster Detail
// ---------------------------------------------------------------------------

function ClusterDetail({ clusterId, onBack }: { clusterId: number; onBack: () => void }) {
  const detail = useAsync(() => api.get(clusterId), [clusterId]);
  const [error, setError] = useState<string | null>(null);
  const [newKeyword, setNewKeyword] = useState("");

  const addKeyword = useCallback(async () => {
    if (!newKeyword.trim()) return;
    try {
      await api.addKeywords(clusterId, [{ keyword: newKeyword.trim() }]);
      setNewKeyword("");
      await detail.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [clusterId, newKeyword, detail]);

  const removeKeyword = useCallback(async (itemId: number) => {
    try {
      await api.removeKeyword(itemId);
      await detail.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [detail]);

  if (detail.loading) return <Loading />;
  if (detail.error) return <ErrorBox message={detail.error} />;
  if (!detail.data) return <ErrorBox message="Cluster not found" />;

  const cluster: ClusterDetail = detail.data;

  return (
    <>
      <button className="small" onClick={onBack} style={{ marginBottom: 12 }}>← Back to clusters</button>
      {error && <ErrorBox message={error} />}

      <h3>{cluster.name}</h3>
      {cluster.description && <p className="muted">{cluster.description}</p>}
      {cluster.pillar_keyword && (
        <p style={{ fontSize: 12 }}>Pillar keyword: <strong>{cluster.pillar_keyword}</strong></p>
      )}

      {/* Add keyword */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="row" style={{ gap: 8 }}>
          <input
            placeholder="Add keyword to cluster"
            value={newKeyword}
            onChange={(e) => setNewKeyword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addKeyword()}
            style={{ flex: 1 }}
          />
          <button className="small" onClick={addKeyword} disabled={!newKeyword.trim()}>Add</button>
        </div>
      </div>

      {/* Keywords table */}
      <div className="card">
        <h3>Keywords ({cluster.keywords.length})</h3>
        {cluster.keywords.length === 0 ? (
          <p className="muted">No keywords in this cluster yet.</p>
        ) : (
          <table className="data">
            <thead>
              <tr><th>Keyword</th><th>Source</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {cluster.keywords.map((kw) => (
                <tr key={kw.id}>
                  <td><strong>{kw.keyword}</strong></td>
                  <td><Badge value={kw.source} /></td>
                  <td>
                    <button className="small" onClick={() => removeKeyword(kw.id)}>Remove</button>
                  </td>
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
// Main Page
// ---------------------------------------------------------------------------

export default function KeywordClusters() {
  const [selectedId, setSelectedId] = useState<number | null>(null);

  if (selectedId) {
    return <ClusterDetail clusterId={selectedId} onBack={() => setSelectedId(null)} />;
  }

  return (
    <>
      <h2 className="page-title">🧩 Keyword Clusters</h2>
      <p className="page-sub">
        Group related keywords into topic clusters for content planning and internal linking strategy.
      </p>
      <ClusterList onSelect={(id) => setSelectedId(id)} />
    </>
  );
}
