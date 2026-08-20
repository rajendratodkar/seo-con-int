import { useEffect, useState } from "react";
import { api } from "../services/api";
import { reportGenerator } from "../services/backend";
import type { ReportSummary, ReportResponse } from "../types";

interface Website {
  id: number;
  name: string;
  url: string;
}

export default function Reports() {
  const [websites, setWebsites] = useState<Website[]>([]);
  const [selectedWebsite, setSelectedWebsite] = useState<number>(0);
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [selectedReport, setSelectedReport] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    title: "",
    report_type: "full",
    format: "html",
    period_days: 30,
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
      reportGenerator.list(selectedWebsite).then((res) => setReports(res));
    }
  }, [selectedWebsite]);

  const handleGenerate = async () => {
    if (!selectedWebsite || !form.title) return;
    setGenerating(true);
    try {
      const res = await reportGenerator.create({
        website_id: selectedWebsite,
        title: form.title,
        report_type: form.report_type,
        format: form.format,
        period_days: form.period_days,
      });
      setSelectedReport(res as unknown as ReportResponse);
      setShowForm(false);
      setForm({ title: "", report_type: "full", format: "html", period_days: 30 });
      // Refresh list
      reportGenerator.list(selectedWebsite).then((res) => setReports(res));
    } catch (e) {
      console.error("Failed to generate report", e);
    }
    setGenerating(false);
  };

  const handleViewReport = async (id: number) => {
    setLoading(true);
    try {
      const res = await reportGenerator.get(id);
      setSelectedReport(res as unknown as ReportResponse);
    } catch (e) {
      console.error("Failed to load report", e);
    }
    setLoading(false);
  };

  const handleDeleteReport = async (id: number) => {
    if (!confirm("Delete this report?")) return;
    await reportGenerator.delete(id);
    setReports(reports.filter((r) => r.id !== id));
    if (selectedReport?.id === id) setSelectedReport(null);
  };

  const handleDownloadHtml = (reportId: number) => {
    const url = reportGenerator.getHtml(reportId);
    window.open(url, "_blank");
  };

  const handleDownloadPdf = async (reportId: number) => {
    try {
      const url = `/api/reports/generate/${reportId}/pdf`;
      const a = document.createElement("a");
      a.href = url;
      a.download = `seo-report-${reportId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch (e) {
      console.error("Failed to download PDF", e);
    }
  };

  return (
    <div style={{ padding: "1.5rem" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
        <div>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 700, margin: 0 }}>📊 SEO Audit Reports</h1>
          <p style={{ color: "#6b7280", margin: "0.25rem 0 0" }}>Generate comprehensive SEO reports for your websites</p>
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
            + New Report
          </button>
        </div>
      </div>

      {/* Generate Form Modal */}
      {showForm && (
        <div style={{
          position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center",
          zIndex: 1000,
        }}>
          <div style={{
            backgroundColor: "white", borderRadius: "12px", padding: "1.5rem",
            width: "420px", boxShadow: "0 20px 25px -5px rgba(0,0,0,0.1)",
          }}>
            <h2 style={{ margin: "0 0 1rem", fontSize: "1.25rem" }}>Generate New Report</h2>

            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: "0.25rem" }}>Report Title</label>
              <input
                type="text"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="e.g. Monthly SEO Audit - January 2026"
                style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #d1d5db", boxSizing: "border-box" }}
              />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
              <div>
                <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: "0.25rem" }}>Report Type</label>
                <select
                  value={form.report_type}
                  onChange={(e) => setForm({ ...form, report_type: e.target.value })}
                  style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #d1d5db" }}
                >
                  <option value="full">Full Audit</option>
                  <option value="technical">Technical SEO</option>
                  <option value="content">Content Analysis</option>
                  <option value="performance">Performance</option>
                </select>
              </div>
              <div>
                <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: "0.25rem" }}>Period</label>
                <select
                  value={form.period_days}
                  onChange={(e) => setForm({ ...form, period_days: Number(e.target.value) })}
                  style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #d1d5db" }}
                >
                  <option value={7}>Last 7 days</option>
                  <option value={30}>Last 30 days</option>
                  <option value={90}>Last 90 days</option>
                  <option value={365}>Last year</option>
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
                onClick={handleGenerate}
                disabled={generating || !form.title}
                style={{
                  padding: "0.5rem 1rem",
                  borderRadius: "6px",
                  border: "none",
                  background: generating ? "#93c5fd" : "#2563eb",
                  color: "white",
                  cursor: generating ? "not-allowed" : "pointer",
                  fontWeight: 600,
                }}
              >
                {generating ? "Generating..." : "Generate Report"}
              </button>
            </div>
          </div>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "340px 1fr", gap: "1.5rem" }}>
        {/* Reports List */}
        <div>
          <h2 style={{ fontSize: "1rem", fontWeight: 600, margin: "0 0 0.75rem", color: "#374151" }}>
            Reports ({reports.length})
          </h2>
          {reports.length === 0 ? (
            <div style={{
              padding: "2rem", textAlign: "center", backgroundColor: "#f9fafb",
              borderRadius: "8px", color: "#6b7280",
            }}>
              <p style={{ fontSize: "2rem", margin: "0 0 0.5rem" }}>📄</p>
              <p style={{ margin: 0 }}>No reports yet</p>
              <p style={{ fontSize: "0.8rem", margin: "0.5rem 0 0" }}>Click "New Report" to generate one</p>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {reports.map((r) => (
                <div
                  key={r.id}
                  onClick={() => handleViewReport(r.id)}
                  style={{
                    padding: "0.75rem",
                    backgroundColor: selectedReport?.id === r.id ? "#eff6ff" : "white",
                    border: `1px solid ${selectedReport?.id === r.id ? "#2563eb" : "#e5e7eb"}`,
                    borderRadius: "8px",
                    cursor: "pointer",
                    transition: "all 0.15s",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: "0.9rem", marginBottom: "0.25rem" }}>{r.title}</div>
                      <div style={{ fontSize: "0.75rem", color: "#6b7280" }}>
                        {r.period_days}d period • {r.report_type}
                      </div>
                    </div>
                    <span style={{
                      fontSize: "0.7rem",
                      padding: "0.15rem 0.5rem",
                      borderRadius: "999px",
                      backgroundColor: r.status === "completed" ? "#dcfce7" : r.status === "generating" ? "#fef3c7" : "#f3f4f6",
                      color: r.status === "completed" ? "#166534" : r.status === "generating" ? "#92400e" : "#6b7280",
                    }}>
                      {r.status}
                    </span>
                  </div>
                  <div style={{ fontSize: "0.7rem", color: "#9ca3af", marginTop: "0.25rem" }}>
                    {r.created_at?.slice(0, 10)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Report Preview */}
        <div>
          {loading ? (
            <div style={{ padding: "3rem", textAlign: "center", color: "#6b7280" }}>Loading...</div>
          ) : selectedReport ? (
            <div>
              {/* Report Header */}
              <div style={{
                background: "linear-gradient(135deg, #2563eb, #1d4ed8)",
                color: "white",
                padding: "1.5rem",
                borderRadius: "12px 12px 0 0",
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div>
                    <h2 style={{ margin: "0 0 0.25rem", fontSize: "1.25rem" }}>{selectedReport.title}</h2>
                    <p style={{ margin: 0, opacity: 0.9, fontSize: "0.875rem" }}>
                      Last {selectedReport.period_days} days • Generated {selectedReport.generated_at?.slice(0, 10) || "pending"}
                    </p>
                  </div>
                  <div style={{ display: "flex", gap: "0.5rem" }}>
                    {selectedReport.status === "completed" && (
                      <>
                        <button
                          onClick={() => handleDownloadHtml(selectedReport.id)}
                          style={{
                            padding: "0.4rem 0.75rem",
                            backgroundColor: "rgba(255,255,255,0.2)",
                            color: "white",
                            border: "1px solid rgba(255,255,255,0.3)",
                            borderRadius: "6px",
                            cursor: "pointer",
                            fontSize: "0.8rem",
                          }}
                        >
                          HTML
                        </button>
                        <button
                          onClick={() => handleDownloadPdf(selectedReport.id)}
                          style={{
                            padding: "0.4rem 0.75rem",
                            backgroundColor: "rgba(220,38,38,0.3)",
                            color: "white",
                            border: "1px solid rgba(220,38,38,0.5)",
                            borderRadius: "6px",
                            cursor: "pointer",
                            fontSize: "0.8rem",
                            fontWeight: 600,
                          }}
                        >
                          PDF
                        </button>
                      </>
                    )}
                    <button
                      onClick={() => handleDeleteReport(selectedReport.id)}
                      style={{
                        padding: "0.4rem 0.75rem",
                        backgroundColor: "rgba(220,38,38,0.3)",
                        color: "white",
                        border: "1px solid rgba(220,38,38,0.5)",
                        borderRadius: "6px",
                        cursor: "pointer",
                        fontSize: "0.8rem",
                      }}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>

              {/* Report Body */}
              {selectedReport.status === "completed" && selectedReport.report_data ? (
                <div style={{ backgroundColor: "white", borderRadius: "0 0 12px 12px", padding: "1.5rem", border: "1px solid #e5e7eb", borderTop: "none" }}>
                  <ReportBody data={JSON.parse(selectedReport.report_data)} />
                </div>
              ) : selectedReport.status === "generating" ? (
                <div style={{
                  backgroundColor: "white", borderRadius: "0 0 12px 12px", padding: "3rem",
                  textAlign: "center", border: "1px solid #e5e7eb", borderTop: "none",
                }}>
                  <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>⏳</div>
                  <p>Generating report...</p>
                </div>
              ) : (
                <div style={{
                  backgroundColor: "white", borderRadius: "0 0 12px 12px", padding: "3rem",
                  textAlign: "center", border: "1px solid #e5e7eb", borderTop: "none", color: "#6b7280",
                }}>
                  Report data not available
                </div>
              )}
            </div>
          ) : (
            <div style={{
              padding: "3rem", textAlign: "center", backgroundColor: "#f9fafb",
              borderRadius: "12px", color: "#6b7280",
            }}>
              <p style={{ fontSize: "3rem", margin: "0 0 0.5rem" }}>📊</p>
              <p style={{ fontSize: "1rem", fontWeight: 600, margin: "0 0 0.25rem" }}>Select a report to preview</p>
              <p style={{ margin: 0, fontSize: "0.875rem" }}>Or create a new one to get started</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Report Body Component
function ReportBody({ data }: { data: Record<string, unknown> }) {
  const overview = data.overview as Record<string, number> | undefined;
  const traffic = data.traffic as Record<string, unknown> | undefined;
  const rankings = data.rankings as Record<string, unknown> | undefined;
  const findings = data.findings as Record<string, unknown> | undefined;

  const trend = (traffic?.trend as { date: string; clicks: number; impressions: number }[]) || [];
  const topPages = (rankings?.top_pages as { page_url: string; clicks: number; impressions: number; ctr: number; position: number }[]) || [];
  const topQueries = (rankings?.top_queries as { query: string; clicks: number; impressions: number; ctr: number; position: number }[]) || [];
  const dist = (rankings?.distribution as Record<string, number>) || {};
  const findingsSummary = (findings?.summary as { severity: string; rec_type: string; count: number }[]) || [];

  const totalKw = Object.values(dist).reduce((a, b) => a + b, 0) || 1;

  return (
    <div>
      {/* KPI Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "0.75rem", marginBottom: "1.5rem" }}>
        {[
          { label: "Total Clicks", value: overview?.total_clicks?.toLocaleString() || "0" },
          { label: "Total Impressions", value: overview?.total_impressions?.toLocaleString() || "0" },
          { label: "Avg CTR", value: overview?.avg_ctr ? `${(overview.avg_ctr * 100).toFixed(2)}%` : "0%" },
          { label: "Avg Position", value: overview?.avg_position?.toFixed(1) || "0" },
          { label: "Pages Indexed", value: overview?.pages_indexed?.toLocaleString() || "0" },
          { label: "Unique Queries", value: overview?.unique_queries?.toLocaleString() || "0" },
        ].map((kpi) => (
          <div key={kpi.label} style={{
            padding: "0.75rem", backgroundColor: "#f9fafb", borderRadius: "8px", textAlign: "center",
          }}>
            <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "#2563eb" }}>{kpi.value}</div>
            <div style={{ fontSize: "0.75rem", color: "#6b7280" }}>{kpi.label}</div>
          </div>
        ))}
      </div>

      {/* Traffic Trend */}
      {trend.length > 0 && (
        <div style={{ marginBottom: "1.5rem" }}>
          <h3 style={{ fontSize: "1rem", fontWeight: 600, margin: "0 0 0.75rem" }}>📈 Traffic Trend</h3>
          <div style={{ display: "flex", alignItems: "flex-end", gap: "2px", height: "120px", padding: "0.5rem 0" }}>
            {trend.slice(-14).map((d, i) => {
              const maxClicks = Math.max(...trend.slice(-14).map((t) => t.clicks), 1);
              const pct = (d.clicks / maxClicks) * 100;
              return (
                <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center" }}>
                  <div style={{
                    width: "100%", backgroundColor: "#2563eb", height: `${pct}%`, minHeight: "2px",
                    borderRadius: "3px 3px 0 0", opacity: 0.8,
                  }} />
                  <div style={{ fontSize: "0.6rem", color: "#9ca3af", marginTop: "2px" }}>{d.date.slice(5)}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Rankings Distribution */}
      <div style={{ marginBottom: "1.5rem" }}>
        <h3 style={{ fontSize: "1rem", fontWeight: 600, margin: "0 0 0.75rem" }}>🎯 Rankings Distribution</h3>
        <div style={{ display: "flex", height: "28px", borderRadius: "6px", overflow: "hidden" }}>
          {[
            { label: "Top 3", value: dist.top_3 || 0, color: "#16a34a" },
            { label: "4-10", value: dist.pos_4_10 || 0, color: "#2563eb" },
            { label: "11-20", value: dist.pos_11_20 || 0, color: "#d97706" },
            { label: "21+", value: dist.pos_21_plus || 0, color: "#dc2626" },
          ].map((seg) => (
            <div key={seg.label} style={{
              width: `${(seg.value / totalKw) * 100}%`,
              backgroundColor: seg.color,
              display: "flex", alignItems: "center", justifyContent: "center",
              color: "white", fontSize: "0.7rem", fontWeight: 600,
              minWidth: seg.value > 0 ? "50px" : "0",
            }}>
              {seg.value > 0 && `${seg.label}: ${seg.value}`}
            </div>
          ))}
        </div>
      </div>

      {/* Top Pages */}
      {topPages.length > 0 && (
        <div style={{ marginBottom: "1.5rem" }}>
          <h3 style={{ fontSize: "1rem", fontWeight: 600, margin: "0 0 0.75rem" }}>📄 Top Pages</h3>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left", padding: "0.5rem", borderBottom: "2px solid #e5e7eb" }}>Page</th>
                <th style={{ textAlign: "right", padding: "0.5rem", borderBottom: "2px solid #e5e7eb" }}>Clicks</th>
                <th style={{ textAlign: "right", padding: "0.5rem", borderBottom: "2px solid #e5e7eb" }}>Impressions</th>
                <th style={{ textAlign: "right", padding: "0.5rem", borderBottom: "2px solid #e5e7eb" }}>CTR</th>
                <th style={{ textAlign: "right", padding: "0.5rem", borderBottom: "2px solid #e5e7eb" }}>Position</th>
              </tr>
            </thead>
            <tbody>
              {topPages.map((p, i) => (
                <tr key={i}>
                  <td style={{ padding: "0.5rem", borderBottom: "1px solid #f3f4f6" }} title={p.page_url}>
                    {p.page_url.length > 50 ? p.page_url.slice(0, 50) + "..." : p.page_url}
                  </td>
                  <td style={{ padding: "0.5rem", textAlign: "right", borderBottom: "1px solid #f3f4f6" }}>{p.clicks.toLocaleString()}</td>
                  <td style={{ padding: "0.5rem", textAlign: "right", borderBottom: "1px solid #f3f4f6" }}>{p.impressions.toLocaleString()}</td>
                  <td style={{ padding: "0.5rem", textAlign: "right", borderBottom: "1px solid #f3f4f6" }}>{p.ctr.toFixed(2)}%</td>
                  <td style={{ padding: "0.5rem", textAlign: "right", borderBottom: "1px solid #f3f4f6" }}>{p.position.toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Top Queries */}
      {topQueries.length > 0 && (
        <div style={{ marginBottom: "1.5rem" }}>
          <h3 style={{ fontSize: "1rem", fontWeight: 600, margin: "0 0 0.75rem" }}>🔍 Top Queries</h3>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left", padding: "0.5rem", borderBottom: "2px solid #e5e7eb" }}>Query</th>
                <th style={{ textAlign: "right", padding: "0.5rem", borderBottom: "2px solid #e5e7eb" }}>Clicks</th>
                <th style={{ textAlign: "right", padding: "0.5rem", borderBottom: "2px solid #e5e7eb" }}>Impressions</th>
                <th style={{ textAlign: "right", padding: "0.5rem", borderBottom: "2px solid #e5e7eb" }}>CTR</th>
                <th style={{ textAlign: "right", padding: "0.5rem", borderBottom: "2px solid #e5e7eb" }}>Position</th>
              </tr>
            </thead>
            <tbody>
              {topQueries.map((q, i) => (
                <tr key={i}>
                  <td style={{ padding: "0.5rem", borderBottom: "1px solid #f3f4f6" }}>{q.query}</td>
                  <td style={{ padding: "0.5rem", textAlign: "right", borderBottom: "1px solid #f3f4f6" }}>{q.clicks.toLocaleString()}</td>
                  <td style={{ padding: "0.5rem", textAlign: "right", borderBottom: "1px solid #f3f4f6" }}>{q.impressions.toLocaleString()}</td>
                  <td style={{ padding: "0.5rem", textAlign: "right", borderBottom: "1px solid #f3f4f6" }}>{q.ctr.toFixed(2)}%</td>
                  <td style={{ padding: "0.5rem", textAlign: "right", borderBottom: "1px solid #f3f4f6" }}>{q.position.toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Findings */}
      {findingsSummary.length > 0 && (
        <div>
          <h3 style={{ fontSize: "1rem", fontWeight: 600, margin: "0 0 0.75rem" }}>⚠️ SEO Findings</h3>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left", padding: "0.5rem", borderBottom: "2px solid #e5e7eb" }}>Severity</th>
                <th style={{ textAlign: "left", padding: "0.5rem", borderBottom: "2px solid #e5e7eb" }}>Type</th>
                <th style={{ textAlign: "right", padding: "0.5rem", borderBottom: "2px solid #e5e7eb" }}>Count</th>
              </tr>
            </thead>
            <tbody>
              {findingsSummary.map((f, i) => (
                <tr key={i}>
                  <td style={{ padding: "0.5rem", borderBottom: "1px solid #f3f4f6" }}>
                    <span style={{
                      fontSize: "0.75rem", padding: "0.15rem 0.5rem", borderRadius: "999px",
                      backgroundColor: f.severity === "high" ? "#fef2f2" : f.severity === "medium" ? "#fffbeb" : "#f0fdf4",
                      color: f.severity === "high" ? "#991b1b" : f.severity === "medium" ? "#92400e" : "#166534",
                    }}>
                      {f.severity}
                    </span>
                  </td>
                  <td style={{ padding: "0.5rem", borderBottom: "1px solid #f3f4f6" }}>{f.rec_type}</td>
                  <td style={{ padding: "0.5rem", textAlign: "right", borderBottom: "1px solid #f3f4f6", fontWeight: 600 }}>{f.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
