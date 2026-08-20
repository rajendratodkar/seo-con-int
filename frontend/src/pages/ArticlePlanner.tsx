import { useState } from "react";
import { plans as api } from "../services/backend";
import { Badge, Empty, ErrorBox, Loading } from "../components/common";
import { useAsync } from "../hooks/useAsync";

export default function ArticlePlanner() {
  const list = useAsync(() => api.list(), []);
  const [title, setTitle] = useState("");
  const [error, setError] = useState<string | null>(null);

  if (list.loading) return <Loading />;
  if (list.error) return <ErrorBox message={list.error} />;

  const create = async () => {
    if (!title.trim()) return;
    setError(null);
    try {
      await api.create(title.trim());
      setTitle("");
      await list.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const draft = async (planId: number) => {
    setError(null);
    try {
      await api.generateDraft(planId);
      alert("AI draft generated. It is stored as an AI suggestion until you edit/approve it.");
      await list.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <>
      <h2 className="page-title">Article Planner</h2>
      <p className="page-sub">Briefs are assembled from real data. AI drafts are labeled suggestions.</p>

      <div className="card">
        <div className="row">
          <input placeholder="New article title" value={title} onChange={(e) => setTitle(e.target.value)} style={{ minWidth: 300 }} />
          <button className="primary" onClick={create}>Create plan</button>
        </div>
        {error && <ErrorBox message={error} />}
      </div>

      {list.data && list.data.items.length > 0 ? (
        <table className="data">
          <thead><tr><th>Title</th><th>Intent</th><th>Status</th><th></th></tr></thead>
          <tbody>
            {list.data.items.map((plan) => (
              <tr key={plan.id}>
                <td>{plan.title}</td>
                <td>{plan.search_intent ? <Badge value={plan.search_intent} /> : "—"}</td>
                <td><Badge value={plan.status} /></td>
                <td>
                  {plan.status === "draft" && (
                    <span className="muted">Mark brief-ready via API, then generate draft</span>
                  )}
                  {(plan.status === "brief_ready" || plan.status === "drafting") && (
                    <button className="small" onClick={() => draft(plan.id)}>Generate AI draft</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <Empty text="No article plans yet. Approve a content idea, then plan an article." />
      )}
    </>
  );
}
