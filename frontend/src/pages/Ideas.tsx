import { useState } from "react";
import { ideas as api } from "../services/backend";
import { useWebsiteStore } from "../stores/websiteStore";
import { Badge, Empty, ErrorBox, Loading } from "../components/common";
import { useAsync } from "../hooks/useAsync";

export default function Ideas() {
  const { active } = useWebsiteStore();
  const list = useAsync(() => api.list(), []);
  const [title, setTitle] = useState("");
  const [error, setError] = useState<string | null>(null);

  if (list.loading) return <Loading />;
  if (list.error) return <ErrorBox message={list.error} />;

  const generate = async () => {
    if (!active) return;
    setError(null);
    try {
      const result = await api.generate(active.id);
      alert(`Generated ${result.items.length} new ideas from real data.`);
      await list.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const addManual = async () => {
    if (!title.trim()) return;
    setError(null);
    try {
      await api.create(title.trim(), undefined, active?.id);
      setTitle("");
      await list.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const decide = async (id: number, status: string) => {
    await api.setStatus(id, status);
    await list.reload();
  };

  return (
    <>
      <h2 className="page-title">Content Ideas</h2>
      <p className="page-sub">Generated only from real data (Search Console gaps, research questions) or added manually.</p>

      <div className="card">
        <div className="row">
          <button className="primary" onClick={generate} disabled={!active}>
            Generate from data {active ? `(${active.name})` : ""}
          </button>
          <input placeholder="Manual idea title" value={title} onChange={(e) => setTitle(e.target.value)} style={{ minWidth: 240 }} />
          <button onClick={addManual}>Add manual</button>
        </div>
        {error && <ErrorBox message={error} />}
      </div>

      {list.data && list.data.items.length > 0 ? (
        <table className="data">
          <thead><tr><th>Title</th><th>Source</th><th>Score</th><th>Status</th><th></th></tr></thead>
          <tbody>
            {list.data.items.map((idea) => (
              <tr key={idea.id}>
                <td>
                  <div>{idea.title}</div>
                  {idea.description && <div className="muted" style={{ fontSize: 12 }}>{idea.description}</div>}
                </td>
                <td>{idea.source_type ? <Badge value={idea.source_type} /> : "—"}</td>
                <td>{idea.score !== null ? idea.score.toFixed(2) : "—"}</td>
                <td><Badge value={idea.status} /></td>
                <td>
                  {idea.status === "draft" && <>
                    <button className="small" onClick={() => decide(idea.id, "approved")}>Approve</button>{" "}
                    <button className="small" onClick={() => decide(idea.id, "rejected")}>Reject</button>
                  </>}
                  {idea.status === "approved" && <span className="muted">Ready for planning</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <Empty text="No ideas yet — generate from data or add one manually." />
      )}
    </>
  );
}
