import { useEffect, useState } from "react";
import { api } from "../services/api";
import { serpABTests } from "../services/backend";
import type { SERPABTestOut, SERPABTestStats, Page } from "../types";

interface Website {
  id: number;
  name: string;
  url: string;
}

export default function SERPABTesting() {
  const [websites, setWebsites] = useState<Website[]>([]);
  const [selectedWebsite, setSelectedWebsite] = useState<number>(0);
  const [pages, setPages] = useState<Page[]>([]);
  const [tests, setTests] = useState<SERPABTestOut[]>([]);
  const [stats, setStats] = useState<SERPABTestStats | null>(null);
  const [selectedTest, setSelectedTest] = useState<SERPABTestOut | null>(null);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [activeTab, setActiveTab] = useState<"tests" | "results">("tests");

  // Form state
  const [form, setForm] = useState({
    name: "",
    page_id: 0,
    control_title: "",
    control_description: "",
    variant_title: "",
    variant_description: "",
    min_duration_days: 7,
    confidence_level: 0.95,
  });

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
      api.get<{ items: Page[] }>(`/pages/?website_id=${selectedWebsite}&page_size=100`).then((res) => {
        setPages(res.items ?? []);
      });
    }
  }, [selectedWebsite]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [testsRes, statsRes] = await Promise.all([
        serpABTests.list(selectedWebsite),
        serpABTests.getStats(selectedWebsite),
      ]);
      setTests(testsRes as unknown as SERPABTestOut[]);
      setStats(statsRes as unknown as SERPABTestStats);
    } catch (e) {
      console.error("Failed to load test data", e);
    }
    setLoading(false);
  };

  const handleCreate = async () => {
    if (!form.name || !form.page_id || !form.control_title || !form.variant_title) return;
    try {
      await serpABTests.create({
        website_id: selectedWebsite,
        page_id: form.page_id,
        name: form.name,
        control_title: form.control_title,
        control_description: form.control_description,
        variant_title: form.variant_title,
        variant_description: form.variant_description,
        min_days: form.min_duration_days,
        confidence: form.confidence_level,
      });
      setShowForm(false);
      setForm({
        name: "", page_id: 0, control_title: "", control_description: "",
        variant_title: "", variant_description: "", min_duration_days: 7, confidence_level: 0.95,
      });
      loadData();
    } catch (e) {
      console.error("Failed to create test", e);
    }
  };

  const handleStart = async (id: number) => {
    await serpABTests.start(id);
    loadData();
  };

  const handlePause = async (id: number) => {
    await serpABTests.pause(id);
    loadData();
  };

  const handleResume = async (id: number) => {
    await serpABTests.resume(id);
    loadData();
  };

  const handleEvaluate = async (id: number) => {
    await serpABTests.evaluate(id);
    loadData();
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this test?")) return;
    await serpABTests.delete(id);
    setSelectedTest(null);
    loadData();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "draft": return "#6b7280";
      case "running": return "#2563eb";
      case "paused": return "#d97706";
      case "completed": return "#16a34a";
      case "cancelled": return "#dc2626";
      default: return "#6b7280";
    }
  };

  const getWinnerColor = (winner: string | null) => {
    switch (winner) {
      case "variant": return "#16a34a";
      case "control": return "#2563eb";
      case "inconclusive": return "#d97706";
      default: return "#6b7280";
    }
  };

  return (
    <div style={{ padding: "1.5rem" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
        <div>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 700, margin: 0 }}>🧪 SERP A/B Testing</h1>
          <p style={{ color: "#6b7280", margin: "0.25rem 0 0" }}>Test title/description combinations and measure CTR impact</p>
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
            + New Test
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "1rem", marginBottom: "1.5rem" }}>
          <div style={{ padding: "1rem", backgroundColor: "white", borderRadius: "8px", border: "1px solid #e5e7eb", textAlign: "center" }}>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#2563eb" }}>{stats.total_tests}</div>
            <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>Total Tests</div>
          </div>
          <div style={{ padding: "1rem", backgroundColor: "white", borderRadius: "8px", border: "1px solid #e5e7eb", textAlign: "center" }}>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#16a34a" }}>{stats.running}</div>
            <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>Running</div>
          </div>
          <div style={{ padding: "1rem", backgroundColor: "white", borderRadius: "8px", border: "1px solid #e5e7eb", textAlign: "center" }}>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#16a34a" }}>{stats.variant_wins}</div>
            <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>Variant Wins</div>
          </div>
          <div style={{ padding: "1rem", backgroundColor: "white", borderRadius: "8px", border: "1px solid #e5e7eb", textAlign: "center" }}>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#2563eb" }}>{stats.control_wins}</div>
            <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>Control Wins</div>
          </div>
          <div style={{ padding: "1rem", backgroundColor: "white", borderRadius: "8px", border: "1px solid #e5e7eb", textAlign: "center" }}>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: stats.avg_lift && stats.avg_lift > 0 ? "#16a34a" : "#6b7280" }}>
              {stats.avg_lift ? `${stats.avg_lift > 0 ? "+" : ""}${stats.avg_lift}%` : "—"}
            </div>
            <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>Avg Lift</div>
          </div>
        </div>
      )}

      {/* Create Form Modal */}
      {showForm && (
        <div style={{
          position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center",
          zIndex: 1000,
        }}>
          <div style={{
            backgroundColor: "white", borderRadius: "12px", padding: "1.5rem",
            width: "600px", maxHeight: "90vh", overflow: "auto",
            boxShadow: "0 20px 25px -5px rgba(0,0,0,0.1)",
          }}>
            <h2 style={{ margin: "0 0 1rem", fontSize: "1.25rem" }}>Create SERP A/B Test</h2>

            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: "0.25rem" }}>Test Name</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="e.g. Homepage Title Test"
                style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #d1d5db", boxSizing: "border-box" }}
              />
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: "0.25rem" }}>Page</label>
              <select
                value={form.page_id}
                onChange={(e) => setForm({ ...form, page_id: Number(e.target.value) })}
                style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #d1d5db" }}
              >
                <option value={0}>-- Select a page --</option>
                {pages.map((p) => (
                  <option key={p.id} value={p.id}>{p.title || p.url}</option>
                ))}
              </select>
            </div>

            {/* Control */}
            <div style={{ marginBottom: "1rem", padding: "1rem", backgroundColor: "#f0f9ff", borderRadius: "8px", border: "1px solid #bae6fd" }}>
              <h3 style={{ fontSize: "0.875rem", fontWeight: 600, color: "#0369a1", margin: "0 0 0.75rem" }}>🔵 Control (Original)</h3>
              <div style={{ marginBottom: "0.5rem" }}>
                <input
                  type="text"
                  value={form.control_title}
                  onChange={(e) => setForm({ ...form, control_title: e.target.value })}
                  placeholder="Current title tag"
                  style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #bae6fd", boxSizing: "border-box" }}
                />
              </div>
              <textarea
                value={form.control_description}
                onChange={(e) => setForm({ ...form, control_description: e.target.value })}
                placeholder="Current meta description"
                rows={2}
                style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #bae6fd", boxSizing: "border-box", resize: "vertical" }}
              />
            </div>

            {/* Variant */}
            <div style={{ marginBottom: "1rem", padding: "1rem", backgroundColor: "#f0fdf4", borderRadius: "8px", border: "1px solid #bbf7d0" }}>
              <h3 style={{ fontSize: "0.875rem", fontWeight: 600, color: "#166534", margin: "0 0 0.75rem" }}>🟢 Variant (New)</h3>
              <div style={{ marginBottom: "0.5rem" }}>
                <input
                  type="text"
                  value={form.variant_title}
                  onChange={(e) => setForm({ ...form, variant_title: e.target.value })}
                  placeholder="New title to test"
                  style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #bbf7d0", boxSizing: "border-box" }}
                />
              </div>
              <textarea
                value={form.variant_description}
                onChange={(e) => setForm({ ...form, variant_description: e.target.value })}
                placeholder="New meta description to test"
                rows={2}
                style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #bbf7d0", boxSizing: "border-box", resize: "vertical" }}
              />
            </div>

            {/* Settings */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
              <div>
                <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: "0.25rem" }}>Min Duration (days)</label>
                <input
                  type="number"
                  value={form.min_duration_days}
                  onChange={(e) => setForm({ ...form, min_duration_days: Number(e.target.value) })}
                  min={1}
                  max={90}
                  style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #d1d5db", boxSizing: "border-box" }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: "0.25rem" }}>Confidence Level</label>
                <select
                  value={form.confidence_level}
                  onChange={(e) => setForm({ ...form, confidence_level: Number(e.target.value) })}
                  style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #d1d5db" }}
                >
                  <option value={0.80}>80%</option>
                  <option value={0.90}>90%</option>
                  <option value={0.95}>95%</option>
                  <option value={0.99}>99%</option>
                </select>
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
                disabled={!form.name || !form.page_id || !form.control_title || !form.variant_title}
                style={{
                  padding: "0.5rem 1rem", borderRadius: "6px", border: "none",
                  background: "#2563eb", color: "white", cursor: "pointer", fontWeight: 600,
                }}
              >
                Create Test
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tests List */}
      <div style={{ backgroundColor: "white", borderRadius: "12px", border: "1px solid #e5e7eb", overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
          <thead>
            <tr style={{ backgroundColor: "#f9fafb" }}>
              <th style={{ textAlign: "left", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>Test</th>
              <th style={{ textAlign: "center", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>Status</th>
              <th style={{ textAlign: "center", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>Control CTR</th>
              <th style={{ textAlign: "center", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>Variant CTR</th>
              <th style={{ textAlign: "center", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>Lift</th>
              <th style={{ textAlign: "center", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>Winner</th>
              <th style={{ textAlign: "right", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} style={{ padding: "2rem", textAlign: "center", color: "#6b7280" }}>Loading...</td></tr>
            ) : tests.length === 0 ? (
              <tr><td colSpan={7} style={{ padding: "2rem", textAlign: "center", color: "#6b7280" }}>No tests yet. Create one to get started.</td></tr>
            ) : (
              tests.map((test) => (
                <tr
                  key={test.id}
                  onClick={() => { setSelectedTest(test); setActiveTab("results"); }}
                  style={{ cursor: "pointer", backgroundColor: selectedTest?.id === test.id ? "#f0f9ff" : "white" }}
                >
                  <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6" }}>
                    <div style={{ fontWeight: 600 }}>{test.name}</div>
                    <div style={{ fontSize: "0.75rem", color: "#6b7280" }}>
                      {test.control_title.slice(0, 40)}... → {test.variant_title.slice(0, 40)}...
                    </div>
                  </td>
                  <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6", textAlign: "center" }}>
                    <span style={{
                      fontSize: "0.75rem", padding: "0.15rem 0.5rem", borderRadius: "999px",
                      backgroundColor: `${getStatusColor(test.status)}15`,
                      color: getStatusColor(test.status),
                      fontWeight: 600, textTransform: "capitalize",
                    }}>
                      {test.status}
                    </span>
                  </td>
                  <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6", textAlign: "center" }}>
                    {test.control_ctr ? `${(test.control_ctr * 100).toFixed(2)}%` : "—"}
                  </td>
                  <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6", textAlign: "center" }}>
                    {test.variant_ctr ? `${(test.variant_ctr * 100).toFixed(2)}%` : "—"}
                  </td>
                  <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6", textAlign: "center" }}>
                    {test.lift !== null ? (
                      <span style={{
                        fontWeight: 600,
                        color: test.lift > 0 ? "#16a34a" : test.lift < 0 ? "#dc2626" : "#6b7280",
                      }}>
                        {test.lift > 0 ? "+" : ""}{test.lift.toFixed(1)}%
                      </span>
                    ) : "—"}
                  </td>
                  <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6", textAlign: "center" }}>
                    {test.winner ? (
                      <span style={{
                        fontWeight: 600,
                        color: getWinnerColor(test.winner),
                        textTransform: "capitalize",
                      }}>
                        {test.winner}
                      </span>
                    ) : "—"}
                  </td>
                  <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6", textAlign: "right" }}>
                    <div style={{ display: "flex", gap: "0.25rem", justifyContent: "flex-end" }}>
                      {test.status === "draft" && (
                        <button onClick={(e) => { e.stopPropagation(); handleStart(test.id); }}
                          style={{ padding: "0.25rem 0.5rem", borderRadius: "4px", border: "none", backgroundColor: "#dcfce7", color: "#166534", cursor: "pointer", fontSize: "0.75rem" }}>
                          Start
                        </button>
                      )}
                      {test.status === "running" && (
                        <button onClick={(e) => { e.stopPropagation(); handlePause(test.id); }}
                          style={{ padding: "0.25rem 0.5rem", borderRadius: "4px", border: "none", backgroundColor: "#fef3c7", color: "#92400e", cursor: "pointer", fontSize: "0.75rem" }}>
                          Pause
                        </button>
                      )}
                      {test.status === "paused" && (
                        <button onClick={(e) => { e.stopPropagation(); handleResume(test.id); }}
                          style={{ padding: "0.25rem 0.5rem", borderRadius: "4px", border: "none", backgroundColor: "#dbeafe", color: "#1e40af", cursor: "pointer", fontSize: "0.75rem" }}>
                          Resume
                        </button>
                      )}
                      {(test.status === "running" || test.status === "paused") && (
                        <button onClick={(e) => { e.stopPropagation(); handleEvaluate(test.id); }}
                          style={{ padding: "0.25rem 0.5rem", borderRadius: "4px", border: "none", backgroundColor: "#f3e8ff", color: "#7c3aed", cursor: "pointer", fontSize: "0.75rem" }}>
                          Evaluate
                        </button>
                      )}
                      <button onClick={(e) => { e.stopPropagation(); handleDelete(test.id); }}
                        style={{ padding: "0.25rem 0.5rem", borderRadius: "4px", border: "1px solid #e5e7eb", backgroundColor: "white", color: "#dc2626", cursor: "pointer", fontSize: "0.75rem" }}>
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Test Detail */}
      {selectedTest && (
        <div style={{ marginTop: "1.5rem", backgroundColor: "white", borderRadius: "12px", padding: "1.5rem", border: "1px solid #e5e7eb" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
            <h2 style={{ fontSize: "1.125rem", fontWeight: 600, margin: 0 }}>{selectedTest.name}</h2>
            <span style={{
              fontSize: "0.75rem", padding: "0.25rem 0.75rem", borderRadius: "999px",
              backgroundColor: `${getStatusColor(selectedTest.status)}15`,
              color: getStatusColor(selectedTest.status),
              fontWeight: 600, textTransform: "capitalize",
            }}>
              {selectedTest.status}
            </span>
          </div>

          {/* Side by Side Preview */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1.5rem" }}>
            {/* Control */}
            <div style={{ padding: "1rem", backgroundColor: "#f0f9ff", borderRadius: "8px", border: "1px solid #bae6fd" }}>
              <h3 style={{ fontSize: "0.875rem", fontWeight: 600, color: "#0369a1", margin: "0 0 0.5rem" }}>🔵 Control</h3>
              <div style={{ fontFamily: "Arial, sans-serif", marginBottom: "0.5rem" }}>
                <div style={{ fontSize: "1.1rem", color: "#1a0dab", cursor: "pointer" }}>{selectedTest.control_title}</div>
                <div style={{ fontSize: "0.8rem", color: "#4d5156" }}>{selectedTest.control_description}</div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "0.5rem", fontSize: "0.8rem" }}>
                <div><span style={{ color: "#6b7280" }}>CTR:</span> <strong>{selectedTest.control_ctr ? `${(selectedTest.control_ctr * 100).toFixed(2)}%` : "—"}</strong></div>
                <div><span style={{ color: "#6b7280" }}>Clicks:</span> <strong>{selectedTest.control_clicks}</strong></div>
                <div><span style={{ color: "#6b7280" }}>Imp:</span> <strong>{selectedTest.control_impressions}</strong></div>
              </div>
            </div>

            {/* Variant */}
            <div style={{ padding: "1rem", backgroundColor: "#f0fdf4", borderRadius: "8px", border: "1px solid #bbf7d0" }}>
              <h3 style={{ fontSize: "0.875rem", fontWeight: 600, color: "#166534", margin: "0 0 0.5rem" }}>🟢 Variant</h3>
              <div style={{ fontFamily: "Arial, sans-serif", marginBottom: "0.5rem" }}>
                <div style={{ fontSize: "1.1rem", color: "#1a0dab", cursor: "pointer" }}>{selectedTest.variant_title}</div>
                <div style={{ fontSize: "0.8rem", color: "#4d5156" }}>{selectedTest.variant_description}</div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "0.5rem", fontSize: "0.8rem" }}>
                <div><span style={{ color: "#6b7280" }}>CTR:</span> <strong>{selectedTest.variant_ctr ? `${(selectedTest.variant_ctr * 100).toFixed(2)}%` : "—"}</strong></div>
                <div><span style={{ color: "#6b7280" }}>Clicks:</span> <strong>{selectedTest.variant_clicks}</strong></div>
                <div><span style={{ color: "#6b7280" }}>Imp:</span> <strong>{selectedTest.variant_impressions}</strong></div>
              </div>
            </div>
          </div>

          {/* Results */}
          {selectedTest.status === "completed" && selectedTest.winner && (
            <div style={{
              padding: "1rem",
              backgroundColor: selectedTest.winner === "variant" ? "#f0fdf4" : selectedTest.winner === "control" ? "#f0f9ff" : "#fffbeb",
              borderRadius: "8px",
              border: `1px solid ${selectedTest.winner === "variant" ? "#bbf7d0" : selectedTest.winner === "control" ? "#bae6fd" : "#fde68a"}`,
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <h3 style={{ fontSize: "1rem", fontWeight: 600, margin: "0 0 0.25rem", color: getWinnerColor(selectedTest.winner) }}>
                    {selectedTest.winner === "variant" ? "🎉 Variant Wins!" : selectedTest.winner === "control" ? "🔵 Control Wins" : "⚖️ Inconclusive"}
                  </h3>
                  <p style={{ fontSize: "0.85rem", color: "#6b7280", margin: 0 }}>
                    {selectedTest.lift !== null && `Lift: ${selectedTest.lift > 0 ? "+" : ""}${selectedTest.lift.toFixed(1)}%`}
                    {selectedTest.p_value !== null && ` | p-value: ${selectedTest.p_value.toFixed(4)}`}
                  </p>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: "0.75rem", color: "#6b7280" }}>Z-Score</div>
                  <div style={{ fontWeight: 600 }}>{selectedTest.z_score?.toFixed(2) || "—"}</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
