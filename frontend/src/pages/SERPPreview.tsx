import { useEffect, useState } from "react";
import { api } from "../services/api";
import { serpPreview } from "../services/backend";
import type { SERPPreviewResult, SERPBulkScoreResult, Page } from "../types";

interface Website {
  id: number;
  name: string;
  url: string;
}

export default function SERPPreview() {
  const [websites, setWebsites] = useState<Website[]>([]);
  const [selectedWebsite, setSelectedWebsite] = useState<number>(0);
  const [pages, setPages] = useState<Page[]>([]);
  const [selectedPage, setSelectedPage] = useState<number>(0);
  const [activeTab, setActiveTab] = useState<"editor" | "bulk">("editor");

  // Editor state
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [url, setUrl] = useState("");
  const [siteName, setSiteName] = useState("");

  // Preview result
  const [preview, setPreview] = useState<SERPPreviewResult | null>(null);
  const [loading, setLoading] = useState(false);

  // Bulk score state
  const [bulkResult, setBulkResult] = useState<SERPBulkScoreResult | null>(null);
  const [bulkLoading, setBulkLoading] = useState(false);

  useEffect(() => {
    api.get<{ items: Website[] }>("/websites/").then((res) => {
      const items = res.items ?? [];
      if (items.length > 0) {
        setWebsites(items);
        setSelectedWebsite(items[0].id);
        setSiteName(items[0].name);
      }
    });
  }, []);

  useEffect(() => {
    if (selectedWebsite) {
      api.get<{ items: Page[] }>(`/pages/?website_id=${selectedWebsite}&page_size=100`).then((res) => {
        setPages(res.items ?? []);
      });
    }
  }, [selectedWebsite]);

  useEffect(() => {
    if (selectedPage) {
      const page = pages.find((p) => p.id === selectedPage);
      if (page) {
        setTitle(page.title || "");
        setDescription(page.meta_description || "");
        setUrl(page.url);
      }
    }
  }, [selectedPage, pages]);

  // Live preview on any input change
  useEffect(() => {
    if (!title && !description && !url) {
      setPreview(null);
      return;
    }

    const timer = setTimeout(() => {
      generatePreview();
    }, 300);

    return () => clearTimeout(timer);
  }, [title, description, url]);

  const generatePreview = async () => {
    if (!title && !description && !url) return;
    setLoading(true);
    try {
      const res = await serpPreview.preview({
        title: title || "Untitled Page",
        description: description || "No description",
        url: url || "https://example.com",
        site_name: siteName || undefined,
      });
      setPreview(res as unknown as SERPPreviewResult);
    } catch (e) {
      console.error("Failed to generate preview", e);
    }
    setLoading(false);
  };

  const runBulkScore = async () => {
    if (!selectedWebsite) return;
    setBulkLoading(true);
    try {
      const res = await serpPreview.bulkScore(selectedWebsite, 200);
      setBulkResult(res as unknown as SERPBulkScoreResult);
    } catch (e) {
      console.error("Failed to bulk score", e);
    }
    setBulkLoading(false);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "good": return "#16a34a";
      case "warning": return "#d97706";
      case "too_long": return "#dc2626";
      case "too_short": return "#d97706";
      default: return "#6b7280";
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "good": return "✓ Good length";
      case "warning": return "⚠ Could be shorter";
      case "too_long": return "✗ Too long — will be truncated";
      case "too_short": return "⚠ Too short — add more detail";
      default: return "";
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 85) return "#16a34a";
    if (score >= 70) return "#2563eb";
    if (score >= 50) return "#d97706";
    return "#dc2626";
  };

  const getTipIcon = (type: string) => {
    switch (type) {
      case "success": return "✅";
      case "info": return "💡";
      case "warning": return "⚠️";
      case "error": return "❌";
      default: return "💡";
    }
  };

  const getTipColor = (type: string) => {
    switch (type) {
      case "success": return "#166534";
      case "info": return "#1e40af";
      case "warning": return "#92400e";
      case "error": return "#991b1b";
      default: return "#374151";
    }
  };

  const getTipBg = (type: string) => {
    switch (type) {
      case "success": return "#f0fdf4";
      case "info": return "#eff6ff";
      case "warning": return "#fffbeb";
      case "error": return "#fef2f2";
      default: return "#f9fafb";
    }
  };

  return (
    <div style={{ padding: "1.5rem" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
        <div>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 700, margin: 0 }}>🔍 SERP Preview</h1>
          <p style={{ color: "#6b7280", margin: "0.25rem 0 0" }}>See how your pages appear in Google search results</p>
        </div>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <select
            value={selectedWebsite}
            onChange={(e) => setSelectedWebsite(Number(e.target.value))}
            style={{ padding: "0.5rem", borderRadius: "6px", border: "1px solid #d1d5db" }}
          >
            {websites.map((w) => (
              <option key={w.id} value={w.id}>{w.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
        {(["editor", "bulk"] as const).map((tab) => (
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
            }}
          >
            {tab === "editor" ? "✏️ Editor" : "📊 Bulk Score"}
          </button>
        ))}
      </div>

      {/* Editor Tab */}
      {activeTab === "editor" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
          {/* Editor Panel */}
          <div style={{ backgroundColor: "white", borderRadius: "12px", padding: "1.5rem", border: "1px solid #e5e7eb" }}>
            <h2 style={{ fontSize: "1rem", fontWeight: 600, margin: "0 0 1rem" }}>Edit Meta Tags</h2>

            {/* Page Selector */}
            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: "0.25rem" }}>
                Load from Page (optional)
              </label>
              <select
                value={selectedPage}
                onChange={(e) => setSelectedPage(Number(e.target.value))}
                style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #d1d5db" }}
              >
                <option value={0}>-- Select a page --</option>
                {pages.map((p) => (
                  <option key={p.id} value={p.id}>{p.title || p.url}</option>
                ))}
              </select>
            </div>

            {/* Title Input */}
            <div style={{ marginBottom: "1rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.25rem" }}>
                <label style={{ fontSize: "0.875rem", fontWeight: 600 }}>Title Tag</label>
                <span style={{ fontSize: "0.75rem", color: getStatusColor(preview?.title_status || ""), fontWeight: 500 }}>
                  {title.length}/60 chars
                </span>
              </div>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Enter your page title"
                style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #d1d5db", boxSizing: "border-box" }}
              />
              {preview && (
                <p style={{ fontSize: "0.75rem", color: getStatusColor(preview.title_status), margin: "0.25rem 0 0" }}>
                  {getStatusLabel(preview.title_status)}
                </p>
              )}
            </div>

            {/* Description Input */}
            <div style={{ marginBottom: "1rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.25rem" }}>
                <label style={{ fontSize: "0.875rem", fontWeight: 600 }}>Meta Description</label>
                <span style={{ fontSize: "0.75rem", color: getStatusColor(preview?.description_status || ""), fontWeight: 500 }}>
                  {description.length}/160 chars
                </span>
              </div>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Enter your meta description"
                rows={3}
                style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #d1d5db", boxSizing: "border-box", resize: "vertical" }}
              />
              {preview && (
                <p style={{ fontSize: "0.75rem", color: getStatusColor(preview.description_status), margin: "0.25rem 0 0" }}>
                  {getStatusLabel(preview.description_status)}
                </p>
              )}
            </div>

            {/* URL Input */}
            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: "0.25rem" }}>Page URL</label>
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com/page"
                style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #d1d5db", boxSizing: "border-box" }}
              />
            </div>

            {/* Site Name */}
            <div>
              <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: "0.25rem" }}>Site Name (optional)</label>
              <input
                type="text"
                value={siteName}
                onChange={(e) => setSiteName(e.target.value)}
                placeholder="Your Site Name"
                style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #d1d5db", boxSizing: "border-box" }}
              />
            </div>
          </div>

          {/* Preview Panel */}
          <div>
            <h2 style={{ fontSize: "1rem", fontWeight: 600, margin: "0 0 0.75rem" }}>Google Search Preview</h2>

            {/* Google-style SERP Card */}
            <div style={{ backgroundColor: "white", borderRadius: "12px", padding: "1.5rem", border: "1px solid #e5e7eb" }}>
              {preview ? (
                <div style={{ fontFamily: "Arial, sans-serif" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
                    <div style={{
                      width: "28px", height: "28px", borderRadius: "50%",
                      backgroundColor: "#f3f4f6", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.8rem",
                    }}>
                      {preview.site_name?.[0] || preview.display_url[0]}
                    </div>
                    <div>
                      <div style={{ fontSize: "0.8rem", color: "#202124" }}>{preview.site_name || preview.display_url}</div>
                      <div style={{ fontSize: "0.75rem", color: "#4d5156" }}>{preview.display_url}</div>
                    </div>
                  </div>
                  <h3 style={{ fontSize: "1.25rem", color: "#1a0dab", fontWeight: 400, margin: "0.5rem 0 0.25rem", lineHeight: 1.3, cursor: "pointer" }}>
                    {preview.truncated_title}
                  </h3>
                  <p style={{ fontSize: "0.875rem", color: "#4d5156", margin: 0, lineHeight: 1.5 }}>
                    {preview.truncated_description}
                  </p>
                  <div style={{ display: "flex", gap: "1rem", marginTop: "1rem", paddingTop: "1rem", borderTop: "1px solid #f3f4f6" }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: "0.75rem", color: "#6b7280", marginBottom: "0.25rem" }}>Title Length</div>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                        <div style={{ flex: 1, height: "6px", backgroundColor: "#f3f4f6", borderRadius: "3px", overflow: "hidden" }}>
                          <div style={{ width: `${Math.min((preview.title_length / 60) * 100, 100)}%`, height: "100%", backgroundColor: getStatusColor(preview.title_status), borderRadius: "3px" }} />
                        </div>
                        <span style={{ fontSize: "0.75rem", color: "#374151", fontWeight: 600 }}>{preview.title_length}/60</span>
                      </div>
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: "0.75rem", color: "#6b7280", marginBottom: "0.25rem" }}>Description Length</div>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                        <div style={{ flex: 1, height: "6px", backgroundColor: "#f3f4f6", borderRadius: "3px", overflow: "hidden" }}>
                          <div style={{ width: `${Math.min((preview.description_length / 160) * 100, 100)}%`, height: "100%", backgroundColor: getStatusColor(preview.description_status), borderRadius: "3px" }} />
                        </div>
                        <span style={{ fontSize: "0.75rem", color: "#374151", fontWeight: 600 }}>{preview.description_length}/160</span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ padding: "3rem", textAlign: "center", color: "#9ca3af" }}>
                  <p style={{ fontSize: "2rem", margin: "0 0 0.5rem" }}>🔍</p>
                  <p style={{ margin: 0 }}>Enter title and description to see preview</p>
                </div>
              )}
            </div>

            {/* Score Card */}
            {preview && (
              <div style={{ marginTop: "1rem", backgroundColor: "white", borderRadius: "12px", padding: "1.5rem", border: "1px solid #e5e7eb" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
                  <h3 style={{ fontSize: "1rem", fontWeight: 600, margin: 0 }}>📊 Snippet Score</h3>
                  <div style={{
                    width: "60px", height: "60px", borderRadius: "50%", border: `4px solid ${getScoreColor(preview.score)}`,
                    display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.25rem", fontWeight: 700, color: getScoreColor(preview.score),
                  }}>
                    {preview.score}
                  </div>
                </div>
                {preview.score_breakdown && (
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "0.75rem" }}>
                    {[
                      { label: "Title", data: preview.score_breakdown.title },
                      { label: "Description", data: preview.score_breakdown.description },
                      { label: "URL", data: preview.score_breakdown.url },
                    ].map((item) => (
                      <div key={item.label} style={{ textAlign: "center" }}>
                        <div style={{ fontSize: "0.75rem", color: "#6b7280", marginBottom: "0.25rem" }}>{item.label}</div>
                        <div style={{ height: "8px", backgroundColor: "#f3f4f6", borderRadius: "4px", overflow: "hidden", marginBottom: "0.25rem" }}>
                          <div style={{ width: `${(item.data.score / item.data.max) * 100}%`, height: "100%", backgroundColor: getScoreColor(item.data.score), borderRadius: "4px" }} />
                        </div>
                        <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "#374151" }}>{item.data.score}/{item.data.max}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Tips */}
            {preview && preview.tips && preview.tips.length > 0 && (
              <div style={{ marginTop: "1rem", backgroundColor: "white", borderRadius: "12px", padding: "1.5rem", border: "1px solid #e5e7eb" }}>
                <h3 style={{ fontSize: "1rem", fontWeight: 600, margin: "0 0 0.75rem" }}>💡 Optimization Tips</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  {preview.tips.map((tip, i) => (
                    <div key={i} style={{
                      display: "flex", alignItems: "flex-start", gap: "0.5rem", padding: "0.5rem 0.75rem",
                      backgroundColor: getTipBg(tip.type), borderRadius: "6px", fontSize: "0.8rem", color: getTipColor(tip.type),
                    }}>
                      <span style={{ flexShrink: 0 }}>{getTipIcon(tip.type)}</span>
                      <span>{tip.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Bulk Score Tab */}
      {activeTab === "bulk" && (
        <div>
          {/* Action Bar */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
            <p style={{ color: "#6b7280", margin: 0 }}>
              Score all pages in your website to find optimization opportunities
            </p>
            <button
              onClick={runBulkScore}
              disabled={bulkLoading || !selectedWebsite}
              style={{
                padding: "0.5rem 1.5rem", borderRadius: "6px", border: "none",
                background: bulkLoading ? "#93c5fd" : "#2563eb", color: "white",
                cursor: bulkLoading ? "not-allowed" : "pointer", fontWeight: 600,
              }}
            >
              {bulkLoading ? "Scoring..." : "🔍 Run Bulk Score"}
            </button>
          </div>

          {bulkResult && (
            <>
              {/* Summary Cards */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "1rem", marginBottom: "1.5rem" }}>
                <div style={{ padding: "1rem", backgroundColor: "white", borderRadius: "8px", border: "1px solid #e5e7eb", textAlign: "center" }}>
                  <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#2563eb" }}>{bulkResult.total_pages}</div>
                  <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>Total Pages</div>
                </div>
                <div style={{ padding: "1rem", backgroundColor: "white", borderRadius: "8px", border: "1px solid #e5e7eb", textAlign: "center" }}>
                  <div style={{ fontSize: "1.5rem", fontWeight: 700, color: getScoreColor(bulkResult.avg_score) }}>{bulkResult.avg_score}</div>
                  <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>Avg Score</div>
                </div>
                <div style={{ padding: "1rem", backgroundColor: "white", borderRadius: "8px", border: "1px solid #e5e7eb", textAlign: "center" }}>
                  <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#16a34a" }}>{bulkResult.distribution.excellent}</div>
                  <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>Excellent (85+)</div>
                </div>
                <div style={{ padding: "1rem", backgroundColor: "white", borderRadius: "8px", border: "1px solid #e5e7eb", textAlign: "center" }}>
                  <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#d97706" }}>{bulkResult.distribution.moderate}</div>
                  <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>Moderate (50-84)</div>
                </div>
                <div style={{ padding: "1rem", backgroundColor: "white", borderRadius: "8px", border: "1px solid #e5e7eb", textAlign: "center" }}>
                  <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#dc2626" }}>{bulkResult.distribution.poor}</div>
                  <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>Poor (&lt;50)</div>
                </div>
              </div>

              {/* Common Issues */}
              {bulkResult.common_issues.length > 0 && (
                <div style={{ backgroundColor: "white", borderRadius: "12px", padding: "1.5rem", border: "1px solid #e5e7eb", marginBottom: "1.5rem" }}>
                  <h3 style={{ fontSize: "1rem", fontWeight: 600, margin: "0 0 1rem" }}>🚨 Most Common Issues</h3>
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                    {bulkResult.common_issues.map((issue, i) => (
                      <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.5rem 0.75rem", backgroundColor: "#fef2f2", borderRadius: "6px" }}>
                        <span style={{ fontSize: "0.85rem", color: "#991b1b" }}>{issue.issue}</span>
                        <span style={{ fontSize: "0.8rem", fontWeight: 600, color: "#991b1b" }}>{issue.count} pages</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Pages Table */}
              <div style={{ backgroundColor: "white", borderRadius: "12px", border: "1px solid #e5e7eb", overflow: "hidden" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
                  <thead>
                    <tr style={{ backgroundColor: "#f9fafb" }}>
                      <th style={{ textAlign: "left", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>Page</th>
                      <th style={{ textAlign: "left", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>Title</th>
                      <th style={{ textAlign: "center", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>Score</th>
                      <th style={{ textAlign: "center", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>Title</th>
                      <th style={{ textAlign: "center", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>Desc</th>
                      <th style={{ textAlign: "left", padding: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>Top Issue</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bulkResult.pages.map((page) => (
                      <tr key={page.page_id}>
                        <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6", fontFamily: "monospace", fontSize: "0.8rem" }}>
                          {page.url.length > 40 ? page.url.slice(0, 40) + "..." : page.url}
                        </td>
                        <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6", maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {page.title}
                        </td>
                        <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6", textAlign: "center" }}>
                          <span style={{
                            display: "inline-block", padding: "0.2rem 0.5rem", borderRadius: "999px", fontWeight: 700,
                            backgroundColor: `${getScoreColor(page.score)}15`, color: getScoreColor(page.score),
                          }}>
                            {page.score}
                          </span>
                        </td>
                        <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6", textAlign: "center", color: page.title_length > 60 ? "#dc2626" : "#6b7280" }}>
                          {page.title_length}/60
                        </td>
                        <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6", textAlign: "center", color: page.description_length > 160 ? "#dc2626" : page.description_length < 70 ? "#d97706" : "#6b7280" }}>
                          {page.description_length}/160
                        </td>
                        <td style={{ padding: "0.75rem", borderBottom: "1px solid #f3f4f6", fontSize: "0.8rem", color: "#6b7280" }}>
                          {page.top_issues.length > 0 ? page.top_issues[0].text.slice(0, 50) + "..." : "✓ No issues"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {!bulkResult && !bulkLoading && (
            <div style={{ padding: "4rem", textAlign: "center", backgroundColor: "white", borderRadius: "12px", border: "1px solid #e5e7eb" }}>
              <p style={{ fontSize: "3rem", margin: "0 0 0.5rem" }}>📊</p>
              <p style={{ fontSize: "1rem", fontWeight: 600, margin: "0 0 0.25rem" }}>No bulk score data yet</p>
              <p style={{ color: "#6b7280", margin: 0 }}>Click "Run Bulk Score" to analyze all pages in your website</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
