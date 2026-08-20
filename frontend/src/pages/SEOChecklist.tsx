import { useCallback, useState } from "react";
import { seoChecklist as api } from "../services/backend";
import { Badge, ErrorBox, Loading } from "../components/common";
import { useAsync } from "../hooks/useAsync";
import { useWebsiteStore } from "../stores/websiteStore";
import type { ChecklistOut, ChecklistDetail, ChecklistItemOut } from "../types";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const CATEGORIES = [
  { value: "meta", label: "Meta", color: "#3b82f6" },
  { value: "content", label: "Content", color: "#22c55e" },
  { value: "technical", label: "Technical", color: "#f59e0b" },
  { value: "links", label: "Links", color: "#8b5cf6" },
  { value: "structured_data", label: "Schema", color: "#ec4899" },
  { value: "performance", label: "Performance", color: "#ef4444" },
];

const STATUS_ICONS: Record<string, string> = {
  todo: "⬜",
  done: "✅",
  skipped: "⏭️",
  blocked: "🚫",
};

// ---------------------------------------------------------------------------
// Checklist List
// ---------------------------------------------------------------------------

function ChecklistList({ onSelect }: { onSelect: (id: number) => void }) {
  const { active } = useWebsiteStore();
  const list = useAsync(() => active ? api.list(active.id) : Promise.resolve([]), [active?.id]);
  const [error, setError] = useState<string | null>(null);
  const [pageId, setPageId] = useState("");

  const create = useCallback(async () => {
    if (!active || !pageId) return;
    try {
      const result = await api.create(active.id, parseInt(pageId));
      setPageId("");
      await list.reload();
      onSelect(result.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [active, pageId, list, onSelect]);

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

  const checklists: ChecklistOut[] = list.data ?? [];

  return (
    <>
      <div className="row" style={{ justifyContent: "space-between", marginBottom: 12 }}>
        <h3 style={{ margin: 0 }}>SEO Checklists {active ? `— ${active.name}` : ""}</h3>
      </div>

      {error && <ErrorBox message={error} />}

      <div className="card" style={{ marginBottom: 12 }}>
        <div className="row" style={{ gap: 8 }}>
          <input placeholder="Page ID" value={pageId} onChange={(e) => setPageId(e.target.value)} style={{ width: 100 }} />
          <button className="small" onClick={create} disabled={!pageId}>Create Checklist</button>
        </div>
      </div>

      {checklists.length === 0 ? (
        <p className="muted">No checklists yet. Create one for a page to start tracking SEO tasks.</p>
      ) : (
        <table className="data">
          <thead>
            <tr><th>Page ID</th><th>Status</th><th>Progress</th><th>Items</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {checklists.map((c) => (
              <tr key={c.id}>
                <td><strong>#{c.page_id}</strong></td>
                <td><Badge value={c.status} /></td>
                <td>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <div style={{ width: 80, height: 6, background: "#e5e7eb", borderRadius: 3 }}>
                      <div style={{ width: `${c.progress_pct}%`, height: "100%", background: c.progress_pct >= 100 ? "#22c55e" : "#3b82f6", borderRadius: 3 }} />
                    </div>
                    <span style={{ fontSize: 11 }}>{c.done_items}/{c.total_items} ({c.progress_pct}%)</span>
                  </div>
                </td>
                <td>{c.total_items}</td>
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
// Checklist Detail
// ---------------------------------------------------------------------------

function ChecklistDetail({ checklistId, onBack }: { checklistId: number; onBack: () => void }) {
  const detail = useAsync(() => api.get(checklistId), [checklistId]);
  const [error, setError] = useState<string | null>(null);
  const [newCategory, setNewCategory] = useState("meta");
  const [newItem, setNewItem] = useState("");
  const [newNotes, setNewNotes] = useState("");

  const autoGenerate = useCallback(async () => {
    try {
      const result = await api.autoGenerate(checklistId);
      alert(`Added ${result.items_added} items from ${result.total_findings} findings.`);
      await detail.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [checklistId, detail]);

  const addItem = useCallback(async () => {
    if (!newItem.trim()) return;
    try {
      await api.addItem(checklistId, newCategory, newItem, newNotes || undefined);
      setNewItem("");
      setNewNotes("");
      await detail.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [checklistId, newCategory, newItem, newNotes, detail]);

  const toggleItem = useCallback(async (item: ChecklistItemOut) => {
    const newStatus = item.status === "done" ? "todo" : "done";
    try {
      await api.updateItem(item.id, { status: newStatus });
      await detail.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [detail]);

  const deleteItem = useCallback(async (itemId: number) => {
    try {
      await api.deleteItem(itemId);
      await detail.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [detail]);

  const complete = useCallback(async () => {
    try {
      await api.complete(checklistId);
      await detail.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [checklistId, detail]);

  if (detail.loading) return <Loading />;
  if (detail.error) return <ErrorBox message={detail.error} />;
  if (!detail.data) return <ErrorBox message="Checklist not found" />;

  const data: ChecklistDetail = detail.data;
  const grouped = CATEGORIES.map((cat) => ({
    ...cat,
    items: data.items.filter((i) => i.category === cat.value),
  })).filter((g) => g.items.length > 0);

  return (
    <>
      <button className="small" onClick={onBack} style={{ marginBottom: 12 }}>← Back</button>
      {error && <ErrorBox message={error} />}

      <div className="row" style={{ justifyContent: "space-between", marginBottom: 12 }}>
        <div>
          <h3 style={{ margin: 0 }}>Page #{data.page_id}</h3>
          {data.page_url && <div className="muted" style={{ fontSize: 11 }}>{data.page_url}</div>}
        </div>
        <div className="row" style={{ gap: 8 }}>
          <Badge value={data.status} />
          <span style={{ fontSize: 12 }}>{data.done_items}/{data.total_items} ({data.progress_pct}%)</span>
          <button className="small" onClick={autoGenerate}>🤖 Auto-Generate from Findings</button>
          {data.status !== "completed" && (
            <button className="small" onClick={complete}>✓ Mark Complete</button>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div style={{ height: 8, background: "#e5e7eb", borderRadius: 4, marginBottom: 16, overflow: "hidden" }}>
        <div style={{ width: `${data.progress_pct}%`, height: "100%", background: data.progress_pct >= 100 ? "#22c55e" : "#3b82f6", borderRadius: 4, transition: "width 0.3s" }} />
      </div>

      {/* Add item */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
          <select value={newCategory} onChange={(e) => setNewCategory(e.target.value)}>
            {CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
          <input placeholder="Add a checklist item" value={newItem} onChange={(e) => setNewItem(e.target.value)} onKeyDown={(e) => e.key === "Enter" && addItem()} style={{ flex: 1 }} />
          <input placeholder="Notes (optional)" value={newNotes} onChange={(e) => setNewNotes(e.target.value)} style={{ width: 200 }} />
          <button className="small" onClick={addItem} disabled={!newItem.trim()}>Add</button>
        </div>
      </div>

      {/* Grouped items */}
      {grouped.map((group) => (
        <div key={group.value} className="card" style={{ marginBottom: 12 }}>
          <h4 style={{ margin: "0 0 8px", color: group.color }}>{group.label} ({group.items.filter((i) => i.status === "done").length}/{group.items.length})</h4>
          {group.items.map((item) => (
            <div key={item.id} style={{
              display: "flex", alignItems: "center", gap: 8, padding: "6px 0",
              borderBottom: "1px solid #f3f4f6",
              opacity: item.status === "done" ? 0.6 : 1,
            }}>
              <button
                onClick={() => toggleItem(item)}
                style={{ background: "none", border: "none", cursor: "pointer", fontSize: 16, padding: 0 }}
                title={item.status === "done" ? "Mark todo" : "Mark done"}
              >
                {STATUS_ICONS[item.status] ?? "⬜"}
              </button>
              <span style={{
                flex: 1,
                fontSize: 13,
                textDecoration: item.status === "done" ? "line-through" : "none",
              }}>
                {item.item_text}
              </span>
              {item.finding_id && <Badge value="auto" />}
              {item.notes && <span className="muted" style={{ fontSize: 10 }} title={item.notes}>📝</span>}
              <button className="small" onClick={() => deleteItem(item.id)} style={{ fontSize: 10 }}>×</button>
            </div>
          ))}
        </div>
      ))}

      {data.items.length === 0 && (
        <p className="muted">No items yet. Click "Auto-Generate from Findings" or add items manually.</p>
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function SEOChecklist() {
  const [selectedId, setSelectedId] = useState<number | null>(null);

  if (selectedId) {
    return <ChecklistDetail checklistId={selectedId} onBack={() => setSelectedId(null)} />;
  }

  return (
    <>
      <h2 className="page-title">✅ SEO Checklist</h2>
      <p className="page-sub">
        Auto-generate per-page SEO checklists from findings and track your progress.
      </p>
      <ChecklistList onSelect={(id) => setSelectedId(id)} />
    </>
  );
}
