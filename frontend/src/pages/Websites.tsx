import { useState } from "react";
import { websites as api } from "../services/backend";
import { useWebsiteStore } from "../stores/websiteStore";
import { Badge, Empty, ErrorBox, Loading } from "../components/common";

export default function Websites() {
  const { websites, refresh, active, loading, error: listError } = useWebsiteStore();
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const add = async () => {
    if (!name || !url) return;
    setBusy("add");
    setError(null);
    try {
      await api.create(name, url);
      setName("");
      setUrl("");
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  };

  const crawl = async (id: number) => {
    setBusy(`crawl-${id}`);
    setError(null);
    try {
      const job = await api.crawl(id);
      // Poll the job until done (large sitemap-driven crawls take minutes)
      for (let i = 0; i < 180; i++) {
        await new Promise((r) => setTimeout(r, 2000));
        const status = await api.crawlStatus(job.job_id);
        if (status.status !== "running") break;
      }
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  };

  const remove = async (id: number) => {
    if (!confirm("Delete this website and all its data?")) return;
    await api.remove(id);
    await refresh();
  };

  return (
    <>
      <h2 className="page-title">Websites</h2>
      <p className="page-sub">Add your sites, detect platform, crawl pages.</p>

      <div className="card">
        <div className="row">
          <input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} />
          <input placeholder="https://example.com" value={url} onChange={(e) => setUrl(e.target.value)} style={{ minWidth: 260 }} />
          <button className="primary" onClick={add} disabled={busy === "add"}>Add website</button>
        </div>
        {error && <ErrorBox message={error} />}
      </div>

      {loading ? (
        <Loading />
      ) : listError ? (
        <ErrorBox message={`Could not load websites: ${listError}. Is the backend running?`} />
      ) : websites.length === 0 ? (
        <Empty text="No websites yet. Add your first one above." />
      ) : (
        <table className="data">
          <thead>
            <tr><th>Name</th><th>URL</th><th>Platform</th><th>Status</th><th>Added</th><th></th></tr>
          </thead>
          <tbody>
            {websites.map((w) => (
              <tr key={w.id}>
                <td>{w.name} {active?.id === w.id && <Badge value="approved" />}</td>
                <td className="mono">{w.url}</td>
                <td><Badge value={w.platform} /></td>
                <td><Badge value={w.status} /></td>
                <td className="muted">{w.created_at?.slice(0, 10)}</td>
                <td>
                  <button className="small" onClick={() => crawl(w.id)} disabled={busy === `crawl-${w.id}`}>
                    {busy === `crawl-${w.id}` ? "Crawling…" : "Crawl"}
                  </button>{" "}
                  <button className="small" onClick={() => remove(w.id)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
