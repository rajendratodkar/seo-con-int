import React, { useRef, useState } from "react";
import { research as api } from "../services/backend";
import { track } from "../services/telemetry";
import { useWebsiteStore } from "../stores/websiteStore";
import { Badge, Empty, ErrorBox, Loading } from "../components/common";
import { useAsync } from "../hooks/useAsync";

export default function Research() {
  const { active } = useWebsiteStore();
  const list = useAsync(() => api.list(), []);
  const [sourceType, setSourceType] = useState("youtube");
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  if (list.loading) return <Loading />;
  if (list.error) return <ErrorBox message={list.error} />;

  const add = async () => {
    if (!url.trim()) return;
    setError(null);
    try {
      await api.add(sourceType, url.trim(), active?.id);
      setUrl("");
      await list.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const ingestFile = async (file: File) => {
    setError(null);
    try {
      const content = await file.text();
      await api.fromFile(file.name, content, active?.id);
      track("action", "research_file_drop");
      await list.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) void ingestFile(file);
  };

  return (
    <>
      <h2 className="page-title">Research</h2>
      <p className="page-sub">
        YouTube + podcast sources and local files. Availability is always honest — metadata-only
        sources are never presented as analyzed content.
      </p>

      <div
        className="card"
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        style={dragOver ? { outline: "2px dashed #2e86ab", outlineOffset: -2 } : undefined}
      >
        <div className="row">
          <select value={sourceType} onChange={(e) => setSourceType(e.target.value)}>
            <option value="youtube">YouTube video</option>
            <option value="podcast">Podcast feed (RSS)</option>
            <option value="article">Article URL</option>
          </select>
          <input placeholder="https://…" value={url} onChange={(e) => setUrl(e.target.value)} style={{ minWidth: 320 }} />
          <button className="primary" onClick={add}>Add source</button>
        </div>
        <div className="row" style={{ marginTop: 8 }}>
          <button onClick={() => fileInput.current?.click()}>📁 Open local file…</button>
          <input
            ref={fileInput}
            type="file"
            accept=".txt,.md,.markdown,.html,.htm,.csv"
            style={{ display: "none" }}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void ingestFile(file);
              e.target.value = "";
            }}
          />
          <span className="muted">…or drag & drop a .txt / .md / .html / .csv file anywhere on this card.</span>
        </div>
        {error && <ErrorBox message={error} />}
        <p className="muted">Extraction runs in the background: topics, claims (with evidence) and questions.</p>
      </div>

      {list.data && list.data.items.length > 0 ? (
        <table className="data">
          <thead><tr><th>Title</th><th>Type</th><th>Availability</th><th>Extraction</th><th></th></tr></thead>
          <tbody>
            {list.data.items.map((s) => (
              <tr key={s.id}>
                <td>
                  <div>{s.title ?? s.url}</div>
                  {s.error_message && <div className="muted" style={{ fontSize: 12 }}>{s.error_message}</div>}
                </td>
                <td><Badge value={s.source_type} /></td>
                <td><Badge value={s.availability_status} /></td>
                <td><Badge value={s.extraction_status} /></td>
                <td>
                  <button className="small" onClick={async () => { await api.remove(s.id); await list.reload(); }}>
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <Empty text="No research sources yet." />
      )}
    </>
  );
}
