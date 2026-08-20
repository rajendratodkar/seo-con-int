import { useEffect, useState } from "react";
import { api } from "../services/api";
import { rankTracker } from "../services/backend";
import type { TrackedKeywordOut, RankTrackerStats, RankAlertOut, KeywordTrendOut } from "../types";

interface Website {
  id: number;
  name: string;
  url: string;
}

export default function RankTracker() {
  const [websites, setWebsites] = useState<Website[]>([]);
  const [selectedWebsite, setSelectedWebsite] = useState<number>(0);
  const [keywords, setKeywords] = useState<TrackedKeywordOut[]>([]);
  const [stats, setStats] = useState<RankTrackerStats | null>(null);
  const [trends, setTrends] = useState<KeywordTrendOut[]>([]);
  const [alerts, setAlerts] = useState<RankAlertOut[]>([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [activeTab, setActiveTab] = useState<"keywords" | "trends" | "alerts">("keywords");
  const [form, setForm] = useState({ keyword: "", target_url: "", group_name: "", notes: "" });

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
    if (selectedWebsite) loadData();
  }, [selectedWebsite]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [kwRes, statsRes, trendsRes, alertsRes] = await Promise.all([
        rankTracker.listKeywords(selectedWebsite),
        rankTracker.getStats(selectedWebsite),
        rankTracker.getTrends(selectedWebsite, 30),
        rankTracker.getAlerts(selectedWebsite),
      ]);
      setKeywords(kwRes as unknown as TrackedKeywordOut[]);
      setStats(statsRes as unknown as RankTrackerStats);
      setTrends(trendsRes as unknown as KeywordTrendOut[]);
      setAlerts(alertsRes as unknown as RankAlertOut[]);
    } catch (e) {
      console.error("Failed to load rank data", e);
    }
    setLoading(false);
  };

  const handleAddKeyword = async () => {
    if (!form.keyword) return;
    try {
      await rankTracker.createKeyword({
        website_id: selectedWebsite,
        keyword: form.keyword,
        target_url: form.target_url || undefined,
        group_name: form.group_name || undefined,
        notes: form.notes || undefined,
      });
      setShowForm(false);
      setForm({ keyword: "", target_url: "", group_name: "", notes: "" });
      loadData();
    } catch (e) {
      console.error("Failed to add keyword", e);
    }
  };

  const handleDeleteKeyword = async (id: number) => {
    if (!confirm("Delete this keyword?")) return;
    await rankTracker.deleteKeyword(id);
    loadData();
  };

  const getPositionColor = (pos: number | null) => {
    if (!pos) return "#6b7280";
    if (pos <= 3) return "#16a34a";
    if (pos <= 10) return "#2563eb";
    if (pos <= 20) return "#d97706";
    return "#dc2626";
  };

  const getChangeColor = (change: number | null) => {
    if (!change) return "#6b7280";
    if (change > 0) return "#16a34a";
    if (change < 0) return "#dc2626";
    return "#6b7280";
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case "improving": return "📈";
      case "declining": return "📉";
      default: return "➡️";
    }
  };

  const renderMiniChart = (dataPoints: { snapshot_date: string; position: number | null }[]) => {
    const validPoints = dataPoints.filter((d) => d.position !== null);
    if (validPoints.length < 2) return <span style={{ color: "#9ca3af" }}>—</span>;

    const positions = validPoints.map((d) => d.position!);
    const maxPos = Math.max(...positions);
    const minPos = Math.min(...positions);
    const range = maxPos - minPos || 1;

    const width = 80;
    const height = 24;
    const points = positions.map((p, i) => {
      const x = (i / (positions.length - 1)) * width;
      const y = ((p - minPos) / range) * (height - 4) + 2;
      return `${x},${y}`;
    }).join(" ");

    return (
      <svg width={width} height={height} style={{ display: "block" }}>
        <polyline
          points={points}
          fill="none"
          stroke="#2563eb"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  };

  return (
    <div style={{ padding: "1.5rem" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
        <div>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 700, margin: 0 }}>📈 Rank Tracker</h1>
          <p style={{ color: "#6b7280", margin: "0.25rem 0 0" }}>Track keyword positions over time with daily snapshots</p>
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
            + Track Keyword
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "1rem", marginBottom: "1.5rem" }}>
          <div style={{ padding: "1rem", backgroundColor: "white", borderRadius: "8px", border: "1px solid #e5e7eb" }}>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#2563eb" }}>{stats.total_keywords}</div>
            <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>Tracked Keywords</div>
          </div>
          <div style={{ padding: "1rem", backgroundColor: "white", borderRadius: "8px", border: "1px solid #e5e7eb" }}>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#16a34a" }}>{stats.top_10_count}</div>
            <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>Top 10</div>
          </div>
          <div style={{ padding: "1rem", backgroundColor: "white", borderRadius: "8px", border: "1px solid #e5e7eb" }}>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#16a34a" }}>↑{stats.position_improved}</div>
            <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>Improved</div>
          </div>
          <div style={{ padding: "1rem", backgroundColor: "white", borderRadius: "8px", border: "1px solid #e5e7eb" }}>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#dc2626" }}>↓{stats.position_dropped}</div>
            <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>Dropped</div>
          </div>
          <div style={{ padding: "1rem", backgroundColor: "white", borderRadius: "8px", border: "1px solid #e5e7eb" }}>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#2563eb" }}>
              {stats.avg_position ? `#${stats.avg_position}` : "—"}
            </div>
            <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>Avg Position</div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
        {(["keywords", "trends", "alerts"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: "0.5rem 1rem",
              borderRadius: "6px",
              border: "1px solid #d1d5db",
              backgroundColor: activeTab === tab ? "#2563eb" : "white",
              color: activeTab === tab ? "white" : "#374151",
              cursor: "pointer",
              fontWeight: 500,
              textTransform: "capitalize",
            }}
          >
            {tab}
            {tab === "alerts" && alerts.filter((a) => !a.is_read).length > 0 && (
              <span style={{
                marginLeft: "0.25rem",
                padding: "0.1rem 0.4rem",
                borderRadius: "999px",
                backgroundColor: "#dc2626",
                color: "white",
                fontSize: "0.7rem",
              }}>
                {alerts.filter((a) => !a.is_read).length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Add Keyword Modal */}
      {showForm && (
        <div style={{
          position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center",
          zIndex: 1000,
        }}>
          <div style={{
            backgroundColor: "white", borderRadius: "12px", padding: "1.5rem",
            width: "450px", boxShadow: "0 20px 25px -5px rgba(0,0,0,0.1)",
          }}>
            <h2 style={{ margin: "0 0 1rem", fontSize: "1.25rem" }}>Track New Keyword</h2>

            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: "0.25rem" }}>Keyword</label>
              <input
                type="text"
                value={form.keyword}
                onChange={(e) => setForm({ ...form, keyword: e.target.value })}
                placeholder="e.g. best seo tools"
                style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #d1d5db", boxSizing: "border-box" }}
              />
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: "0.25rem" }}>Target URL (optional)</label>
              <input
                type="text"
                value={form.target_url}
                onChange={(e) => setForm({ ...form, target_url: e.target.value })}
                placeholder="https://example.com/page"
                style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #d1d5db", boxSizing: "border-box" }}
              />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
              <div>
                <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: "0.25rem" }}>Group</label>
                <input
                  type="text"
                  value={form.group_name}
                  onChange={(e) => setForm({ ...form, group_name: e.target.value })}
                  placeholder="e.g. Blog"
                  style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #d1d5db", boxSizing: "border-box" }}
                />
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
                onClick={handleAddKeyword}
                disabled={!form.keyword}
                style={{
                  padding: "0.5rem 1rem", borderRadius: "6px", border: "none",
                  background: "#2563eb", color: "white", cursor: "pointer", fontWeight: 600,
                }}
              >
                Add Keyword
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Keywords Tab */}
      {activeTab === "keywords" && (
        <div style={{ backgroundColor: "white", borderRadius: "12px", border: "1px solid #e5e7eb", overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
            <thead>
              <tr style={{ backgroundColor: "#f9fafb" }}>
                <th style={{ textAlign: "left", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>Keyword</th>
                <th style={{ textAlign: "center", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>Position</th>
                <th style={{ textAlign: "center", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>Change</th>
                <th style={{ textAlign: "center", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>Trend</th>
                <th style={{ textAlign: "left", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>Group</th>
                <th style={{ textAlign: "right", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} style={{ padding: "2rem", textAlign: "center", color: "#6b7280" }}>Loading...</td></tr>
              ) : keywords.length === 0 ? (
                <tr><td colSpan={6} style={{ padding: "2rem", textAlign: "center", color: "#6b7280" }}>No keywords tracked yet</td></tr>
              ) : (
                keywords.map((kw) => (
                  <tr key={kw.id} style={{ opacity: kw.is_active ? 1 : 0.6 }}>
                    <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6" }}>
                      <div style={{ fontWeight: 600 }}>{kw.keyword}</div>
                      {kw.target_url && (
                        <div style={{ fontSize: "0.75rem", color: "#6b7280", fontFamily: "monospace" }}>
                          {kw.target_url.length > 40 ? kw.target_url.slice(0, 40) + "..." : kw.target_url}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6", textAlign: "center" }}>
                      <span style={{
                        fontSize: "1.1rem", fontWeight: 700,
                        color: getPositionColor(kw.current_position),
                      }}>
                        {kw.current_position ? `#${kw.current_position}` : "—"}
                      </span>
                    </td>
                    <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6", textAlign: "center" }}>
                      {kw.position_change !== null ? (
                        <span style={{
                          fontSize: "0.85rem", fontWeight: 600,
                          color: getChangeColor(kw.position_change),
                        }}>
                          {kw.position_change > 0 ? `+${kw.position_change}` : kw.position_change}
                        </span>
                      ) : (
                        <span style={{ color: "#9ca3af" }}>—</span>
                      )}
                    </td>
                    <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6", textAlign: "center" }}>
                      {renderMiniChart(
                        trends.find((t) => t.keyword_id === kw.id)?.data_points || []
                      )}
                    </td>
                    <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6" }}>
                      {kw.group_name ? (
                        <span style={{
                          fontSize: "0.75rem", padding: "0.15rem 0.5rem", borderRadius: "999px",
                          backgroundColor: "#eff6ff", color: "#1e40af",
                        }}>
                          {kw.group_name}
                        </span>
                      ) : "—"}
                    </td>
                    <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6", textAlign: "right" }}>
                      <button
                        onClick={() => handleDeleteKeyword(kw.id)}
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
      )}

      {/* Trends Tab */}
      {activeTab === "trends" && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "1rem" }}>
          {trends.length === 0 ? (
            <div style={{ padding: "2rem", textAlign: "center", color: "#6b7280", gridColumn: "1 / -1" }}>
              No trend data available yet. Add snapshots to track positions.
            </div>
          ) : (
            trends.map((t) => (
              <div key={t.keyword_id} style={{
                backgroundColor: "white", borderRadius: "8px", padding: "1rem",
                border: "1px solid #e5e7eb",
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                  <span style={{ fontWeight: 600 }}>{t.keyword}</span>
                  <span style={{ fontSize: "1.25rem" }}>{getTrendIcon(t.trend)}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                  <span style={{ color: "#6b7280", fontSize: "0.85rem" }}>Current Position</span>
                  <span style={{
                    fontWeight: 700, fontSize: "1rem",
                    color: getPositionColor(t.current_position),
                  }}>
                    {t.current_position ? `#${t.current_position}` : "—"}
                  </span>
                </div>
                <div style={{ borderTop: "1px solid #f3f4f6", paddingTop: "0.5rem", marginTop: "0.5rem" }}>
                  {renderMiniChart(t.data_points)}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Alerts Tab */}
      {activeTab === "alerts" && (
        <div style={{ backgroundColor: "white", borderRadius: "12px", border: "1px solid #e5e7eb", overflow: "hidden" }}>
          {alerts.length === 0 ? (
            <div style={{ padding: "2rem", textAlign: "center", color: "#6b7280" }}>No alerts yet</div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column" }}>
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  style={{
                    padding: "0.75rem 1rem",
                    borderBottom: "1px solid #f3f4f6",
                    backgroundColor: alert.is_read ? "white" : "#f0f9ff",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.75rem",
                  }}
                >
                  <span style={{ fontSize: "1.25rem" }}>
                    {alert.change && alert.change > 0 ? "📈" : "📉"}
                  </span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: alert.is_read ? 400 : 600, fontSize: "0.9rem" }}>{alert.message}</div>
                    <div style={{ fontSize: "0.75rem", color: "#6b7280" }}>{alert.created_at?.slice(0, 16)}</div>
                  </div>
                  {!alert.is_read && (
                    <button
                      onClick={async () => {
                        await rankTracker.markAlertRead(alert.id);
                        setAlerts(alerts.map((a) => a.id === alert.id ? { ...a, is_read: true } : a));
                      }}
                      style={{
                        padding: "0.25rem 0.5rem", borderRadius: "4px", border: "1px solid #d1d5db",
                        backgroundColor: "white", cursor: "pointer", fontSize: "0.75rem",
                      }}
                    >
                      Mark read
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
