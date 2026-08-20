import { useState } from "react";
import { keywords as api } from "../services/backend";
import { useWebsiteStore } from "../stores/websiteStore";
import { Badge, Empty, ErrorBox, Loading } from "../components/common";
import { useAsync } from "../hooks/useAsync";

export default function Keywords() {
  const { active } = useWebsiteStore();
  const list = useAsync(async () => (active ? api.list(active.id) : null), [active?.id]);
  const [keyword, setKeyword] = useState("");
  const [error, setError] = useState<string | null>(null);

  if (!active) return <Empty text="Add a website first." />;
  if (list.loading) return <Loading />;
  if (list.error) return <ErrorBox message={list.error} />;

  const add = async () => {
    if (!keyword.trim()) return;
    setError(null);
    try {
      await api.create(active.id, keyword.trim());
      setKeyword("");
      await list.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const importSc = async () => {
    setError(null);
    try {
      const result = await api.importFromSc(active.id);
      alert(`Imported ${result.added} keywords from Search Console.`);
      await list.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <>
      <h2 className="page-title">Keywords</h2>
      <p className="page-sub">Track keywords for {active.name}. Import top queries from Search Console or add manually.</p>

      <div className="card">
        <div className="row">
          <input placeholder="New keyword" value={keyword} onChange={(e) => setKeyword(e.target.value)} onKeyDown={(e) => e.key === "Enter" && add()} />
          <button className="primary" onClick={add}>Add</button>
          <button onClick={importSc}>Import from Search Console</button>
        </div>
        {error && <ErrorBox message={error} />}
      </div>

      {list.data && list.data.items.length > 0 ? (
        <table className="data">
          <thead><tr><th>Keyword</th><th>Intent</th><th>Group</th><th>Source</th><th></th></tr></thead>
          <tbody>
            {list.data.items.map((k) => (
              <tr key={k.id}>
                <td>{k.keyword}</td>
                <td>{k.search_intent ? <Badge value={k.search_intent} /> : <span className="muted">—</span>}</td>
                <td>{k.group_name ?? <span className="muted">—</span>}</td>
                <td><Badge value={k.source} /></td>
                <td><button className="small" onClick={async () => { await api.remove(k.id); await list.reload(); }}>Delete</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <Empty text="No keywords yet." />
      )}
    </>
  );
}
