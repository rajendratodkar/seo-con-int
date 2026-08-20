import { useEffect, useState } from "react";
import { api } from "../services/api";
import { redirects } from "../services/backend";
import type { RedirectOut, RedirectStats } from "../types";

interface Website {
  id: number;
  name: string;
  url: string;
}

export default function Redirects() {
  const [websites, setWebsites] = useState<Website[]>([]);
  const [selectedWebsite, setSelectedWebsite] = useState<number>(0);
  const [redirectList, setRedirectList] = useState<RedirectOut[]>([]);
  const [stats, setStats] = useState<RedirectStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [showBulkImport, setShowBulkImport] = useState(false);
  const [filter, setFilter] = useState<string>("");

  // Form state
  const [form, setForm] = useState({
    source_url: "",
    target_url: "",
    status_code: 301,
    notes: "",
  });

  // Bulk import state
  const [bulkText, setBulkText] = useState("");
  const [bulkOverwrite, setBulkOverwrite] = useState(false);

  useEffect(() => {
    api.get<{ items: Website[] }>("/websites/").then((res) => {
      const items = res.items ?? [];
      if (items.length > 0) {
        setWebsites(items);
        setSelectedWebsite(items[0].id);
      }
    });
  }, []);

  useEffect(() => {
    if (selectedWebsite) {
      loadData();
    }
  }, [selectedWebsite, filter]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [redirectsRes, statsRes] = await Promise.all([
        redirects.list(selectedWebsite, filter || undefined),
        redirects.stats(selectedWebsite),
      ]);
      setRedirectList(redirectsRes);
      setStats(statsRes as unknown as RedirectStats);
    } catch (e) {
      console.error("Failed to load redirects", e);
    }
    setLoading(false);
  };

  const handleCreate = async () => {
    if (!form.source_url || !form.target_url) return;
    try {
      await redirects.create({
        website_id: selectedWebsite,
        source_url: form.source_url,
        target_url: form.target_url,
        status_code: form.status_code,
        notes: form.notes || undefined,
      });
      setShowForm(false);
      setForm({ source_url: "", target_url: "", status_code: 301, notes: "" });
      loadData();
    } catch (e) {
      console.error("Failed to create redirect", e);
    }
  };

  const handleBulkImport = async () => {
    const lines = bulkText.split("\n").filter((l) => l.trim());
    const parsed = lines.map((line) => {
      const parts = line.split(",").map((p) => p.trim());
      return {
        source: parts[0] || "",
        target: parts[1] || "",
        status_code: parts[2] ? parseInt(parts[2]) : 301,
      };
    }).filter((r) => r.source && r.target);

    if (parsed.length === 0) return;

    try {
      await redirects.bulkImport(selectedWebsite, parsed, bulkOverwrite);
      setShowBulkImport(false);
      setBulkText("");
      loadData();
    } catch (e) {
      console.error("Failed to bulk import", e);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this redirect?")) return;
    await redirects.delete(id);
    loadData();
  };

  const handleToggleActive = async (redirect: RedirectOut) => {
    await redirects.update(redirect.id, { is_active: !redirect.is_active });
    loadData();
  };

  const getStatusColor = (code: number) => {
    if (code === 301) return "#16a34a";
    if (code === 302) return "#d97706";
    if (code === 307 || code === 308) return "#2563eb";
    return "#6b7280";
  };

  const getStatusLabel = (code: number) => {
    switch (code) {
      case 301: return "301 Permanent";
      case 302: return "302 Temporary";
      case 307: return "307 Temporary";
      case 308: return "308 Permanent";
      default: return `${code}`;
    }
  };

  return (
    <div style={{ padding: "1.5rem" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
        <div>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 700, margin: 0 }}>🔗 Redirect Manager</h1>
          <p style={{ color: "#6b7280", margin: "0.25rem 0 0" }}>Manage 301/302 redirects and detect chains</p>
        </div>
        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
          <select
            value={selectedWebsite}
            onChange={(e) => setSelectedWebsite(Number(e.target.value))}
            style={{ padding: "0.5rem", borderRadius: "6px", border: "1px solid #d1d5db" }}
          >
            {websites.map((w) => (
              <option key={w.id} value={w.id}>{w.name}</option>
            ))}
          </select>
          <button
            onClick={() => setShowBulkImport(true)}
            style={{
              padding: "0.5rem 1rem",
              backgroundColor: "#f3f4f6",
              color: "#374151",
              border: "1px solid #d1d5db",
              borderRadius: "6px",
              cursor: "pointer",
              fontWeight: 500,
            }}
          >
            Bulk Import
          </button>
          <button
            onClick={() => setShowForm(true)}
            style={{
              padding: "0.5rem 1rem",
              backgroundColor: "#2563eb",
              color: "white",
              border: "none",
              borderRadius: "6px",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            + Add Redirect
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "1rem", marginBottom: "1.5rem" }}>
          <div style={{ padding: "1rem", backgroundColor: "white", borderRadius: "8px", border: "1px solid #e5e7eb" }}>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#2563eb" }}>{stats.total}</div>
            <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>Total Redirects</div>
          </div>
          <div style={{ padding: "1rem", backgroundColor: "white", borderRadius: "8px", border: "1px solid #e5e7eb" }}>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#16a34a" }}>{stats.active}</div>
            <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>Active</div>
          </div>
          <div style={{ padding: "1rem", backgroundColor: "white", borderRadius: "8px", border: "1px solid #e5e7eb" }}>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#d97706" }}>{stats.chains_detected}</div>
            <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>Chains Detected</div>
          </div>
          <div style={{ padding: "1rem", backgroundColor: "white", borderRadius: "8px", border: "1px solid #e5e7eb" }}>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#dc2626" }}>{stats.broken_count}</div>
            <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>Broken (4xx/5xx)</div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
        {["", "active", "inactive"].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            style={{
              padding: "0.4rem 0.75rem",
              borderRadius: "6px",
              border: "1px solid #d1d5db",
              backgroundColor: filter === f ? "#2563eb" : "white",
              color: filter === f ? "white" : "#374151",
              cursor: "pointer",
              fontSize: "0.8rem",
            }}
          >
            {f || "All"}
          </button>
        ))}
      </div>

      {/* Create Form Modal */}
      {showForm && (
        <div style={{
          position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center",
          zIndex: 1000,
        }}>
          <div style={{
            backgroundColor: "white", borderRadius: "12px", padding: "1.5rem",
            width: "500px", boxShadow: "0 20px 25px -5px rgba(0,0,0,0.1)",
          }}>
            <h2 style={{ margin: "0 0 1rem", fontSize: "1.25rem" }}>Add Redirect</h2>

            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: "0.25rem" }}>Source URL</label>
              <input
                type="text"
                value={form.source_url}
                onChange={(e) => setForm({ ...form, source_url: e.target.value })}
                placeholder="/old-page"
                style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #d1d5db", boxSizing: "border-box" }}
              />
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: "0.25rem" }}>Target URL</label>
              <input
                type="text"
                value={form.target_url}
                onChange={(e) => setForm({ ...form, target_url: e.target.value })}
                placeholder="/new-page"
                style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #d1d5db", boxSizing: "border-box" }}
              />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
              <div>
                <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: "0.25rem" }}>Status Code</label>
                <select
                  value={form.status_code}
                  onChange={(e) => setForm({ ...form, status_code: Number(e.target.value) })}
                  style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #d1d5db" }}
                >
                  <option value={301}>301 Permanent</option>
                  <option value={302}>302 Temporary</option>
                  <option value={307}>307 Temporary</option>
                  <option value={308}>308 Permanent</option>
                </select>
              </div>
              <div>
                <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: "0.25rem" }}>Notes</label>
                <input
                  type="text"
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  placeholder="Optional"
                  style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #d1d5db", boxSizing: "border-box" }}
                />
              </div>
            </div>

            <div style={{ display: "flex", gap: "0.75rem", justifyContent: "flex-end" }}>
              <button
                onClick={() => setShowForm(false)}
                style={{ padding: "0.5rem 1rem", borderRadius: "6px", border: "1px solid #d1d5db", background: "white", cursor: "pointer" }}
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={!form.source_url || !form.target_url}
                style={{
                  padding: "0.5rem 1rem", borderRadius: "6px", border: "none",
                  background: "#2563eb", color: "white", cursor: "pointer", fontWeight: 600,
                }}
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Import Modal */}
      {showBulkImport && (
        <div style={{
          position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center",
          zIndex: 1000,
        }}>
          <div style={{
            backgroundColor: "white", borderRadius: "12px", padding: "1.5rem",
            width: "550px", boxShadow: "0 20px 25px -5px rgba(0,0,0,0.1)",
          }}>
            <h2 style={{ margin: "0 0 0.5rem", fontSize: "1.25rem" }}>Bulk Import Redirects</h2>
            <p style={{ fontSize: "0.8rem", color: "#6b7280", margin: "0 0 1rem" }}>
              One redirect per line: <code>source, target, status_code</code> (status_code optional, defaults to 301)
            </p>

            <textarea
              value={bulkText}
              onChange={(e) => setBulkText(e.target.value)}
              placeholder={"/old-page, /new-page, 301\n/another-old, /another-new"}
              rows={8}
              style={{
                width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #d1d5db",
                boxSizing: "border-box", fontFamily: "monospace", fontSize: "0.85rem", resize: "vertical",
              }}
            />

            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", margin: "1rem 0" }}>
              <input
                type="checkbox"
                id="overwrite"
                checked={bulkOverwrite}
                onChange={(e) => setBulkOverwrite(e.target.checked)}
              />
              <label htmlFor="overwrite" style={{ fontSize: "0.875rem" }}>Overwrite existing redirects</label>
            </div>

            <div style={{ display: "flex", gap: "0.75rem", justifyContent: "flex-end" }}>
              <button
                onClick={() => setShowBulkImport(false)}
                style={{ padding: "0.5rem 1rem", borderRadius: "6px", border: "1px solid #d1d5db", background: "white", cursor: "pointer" }}
              >
                Cancel
              </button>
              <button
                onClick={handleBulkImport}
                disabled={!bulkText.trim()}
                style={{
                  padding: "0.5rem 1rem", borderRadius: "6px", border: "none",
                  background: "#2563eb", color: "white", cursor: "pointer", fontWeight: 600,
                }}
              >
                Import
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Redirects Table */}
      <div style={{ backgroundColor: "white", borderRadius: "12px", border: "1px solid #e5e7eb", overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
          <thead>
            <tr style={{ backgroundColor: "#f9fafb" }}>
              <th style={{ textAlign: "left", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>Status</th>
              <th style={{ textAlign: "left", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>Source</th>
              <th style={{ textAlign: "left", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>→</th>
              <th style={{ textAlign: "left", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>Target</th>
              <th style={{ textAlign: "center", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>Hits</th>
              <th style={{ textAlign: "center", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>Active</th>
              <th style={{ textAlign: "right", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} style={{ padding: "2rem", textAlign: "center", color: "#6b7280" }}>Loading...</td>
              </tr>
            ) : redirectList.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ padding: "2rem", textAlign: "center", color: "#6b7280" }}>
                  No redirects found. Click "Add Redirect" to create one.
                </td>
              </tr>
            ) : (
              redirectList.map((r) => (
                <tr key={r.id} style={{ opacity: r.is_active ? 1 : 0.6 }}>
                  <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6" }}>
                    <span style={{
                      fontSize: "0.75rem", padding: "0.15rem 0.5rem", borderRadius: "999px",
                      backgroundColor: `${getStatusColor(r.status_code)}15`,
                      color: getStatusColor(r.status_code),
                      fontWeight: 600,
                    }}>
                      {getStatusLabel(r.status_code)}
                    </span>
                  </td>
                  <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6", fontFamily: "monospace", fontSize: "0.8rem" }}>
                    {r.source_url}
                  </td>
                  <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6", color: "#9ca3af" }}>→</td>
                  <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6", fontFamily: "monospace", fontSize: "0.8rem" }}>
                    {r.target_url}
                  </td>
                  <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6", textAlign: "center" }}>
                    {r.hit_count}
                  </td>
                  <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6", textAlign: "center" }}>
                    <button
                      onClick={() => handleToggleActive(r)}
                      style={{
                        padding: "0.25rem 0.5rem", borderRadius: "4px", border: "none",
                        backgroundColor: r.is_active ? "#dcfce7" : "#f3f4f6",
                        color: r.is_active ? "#166534" : "#6b7280",
                        cursor: "pointer", fontSize: "0.75rem",
                      }}
                    >
                      {r.is_active ? "ON" : "OFF"}
                    </button>
                  </td>
                  <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6", textAlign: "right" }}>
                    <button
                      onClick={() => handleDelete(r.id)}
                      style={{
                        padding: "0.25rem 0.5rem", borderRadius: "4px", border: "1px solid #e5e7eb",
                        backgroundColor: "white", color: "#dc2626", cursor: "pointer", fontSize: "0.75rem",
                      }}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
