import { useState } from "react";
import { pages as api } from "../services/backend";
import { useWebsiteStore } from "../stores/websiteStore";
import { Badge, Empty, ErrorBox, Loading } from "../components/common";
import { useAsync } from "../hooks/useAsync";
import type { Page } from "../types";

export default function Content() {
  const { active } = useWebsiteStore();
  const [page, setPage] = useState(1);
  const list = useAsync(
    async () => (active ? api.list(active.id, page) : null),
    [active?.id, page],
  );
  const [selected, setSelected] = useState<Page | null>(null);

  if (!active) return <Empty text="Add a website first." />;
  if (list.loading) return <Loading />;
  if (list.error) return <ErrorBox message={list.error} />;
  if (!list.data || list.data.items.length === 0) {
    return <Empty text="No pages crawled yet. Crawl the website from the Websites page." />;
  }

  return (
    <>
      <h2 className="page-title">Content</h2>
      <p className="page-sub">Crawled page inventory for {active.name} · {list.data.total} pages</p>

      <table className="data">
        <thead>
          <tr><th>Title</th><th>URL</th><th>Status</th><th>Crawl</th><th>Last crawled</th></tr>
        </thead>
        <tbody>
          {list.data.items.map((p) => (
            <tr key={p.id} onClick={() => setSelected(p)} style={{ cursor: "pointer" }}>
              <td>{p.title ?? <span className="muted">—</span>}</td>
              <td className="mono">{p.url}</td>
              <td><Badge value={String(p.status_code ?? "unknown")} /></td>
              <td><Badge value={p.crawl_status} /></td>
              <td className="muted">{p.last_crawled_at?.slice(0, 16) ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="row" style={{ marginTop: 12 }}>
        <button className="small" disabled={page <= 1} onClick={() => setPage(page - 1)}>← Prev</button>
        <span className="muted">Page {page} of {Math.max(1, Math.ceil(list.data.total / list.data.page_size))}</span>
        <button className="small" disabled={page * list.data.page_size >= list.data.total} onClick={() => setPage(page + 1)}>Next →</button>
      </div>

      {selected && <PageDetail page={selected} onClose={() => setSelected(null)} />}
    </>
  );
}

function PageDetail({ page, onClose }: { page: Page; onClose: () => void }) {
  return (
    <div className="card" style={{ marginTop: 16 }}>
      <div className="row">
        <h3 style={{ margin: 0 }}>{page.title ?? page.url}</h3>
        <span className="spacer" />
        <button className="small" onClick={onClose}>Close</button>
      </div>
      <p className="mono">{page.url}</p>
      {page.meta_description
        ? <p className="muted">{page.meta_description}</p>
        : <p className="muted">No meta description captured.</p>}
    </div>
  );
}
