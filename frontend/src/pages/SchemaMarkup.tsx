import { useCallback, useState } from "react";
import { schemas as api } from "../services/backend";
import { Badge, ErrorBox, Loading } from "../components/common";
import { useAsync } from "../hooks/useAsync";
import { useWebsiteStore } from "../stores/websiteStore";

// ---------------------------------------------------------------------------
// Generator Form
// ---------------------------------------------------------------------------

const SCHEMA_FIELDS: Record<string, { label: string; key: string; type?: string; placeholder?: string; required?: boolean }[]> = {
  Article: [
    { label: "Headline", key: "title", required: true, placeholder: "Article title" },
    { label: "URL", key: "url", required: true, placeholder: "https://example.com/article" },
    { label: "Description", key: "description", placeholder: "Brief description" },
    { label: "Author", key: "author_name", placeholder: "Author name" },
    { label: "Publisher", key: "publisher_name", placeholder: "Publisher name" },
    { label: "Image URL", key: "image_url", placeholder: "https://example.com/image.jpg" },
    { label: "Date Published", key: "date_published", type: "date" },
  ],
  FAQPage: [],
  HowTo: [
    { label: "Title", key: "title", required: true, placeholder: "How to..." },
    { label: "Description", key: "description", placeholder: "Brief description" },
    { label: "Total Time", key: "total_time", placeholder: "PT30M (30 minutes)" },
  ],
  Product: [
    { label: "Name", key: "name", required: true, placeholder: "Product name" },
    { label: "Description", key: "description", placeholder: "Product description" },
    { label: "Brand", key: "brand", placeholder: "Brand name" },
    { label: "SKU", key: "sku", placeholder: "SKU-123" },
    { label: "Price", key: "price", type: "number", placeholder: "29.99" },
    { label: "Currency", key: "currency", placeholder: "USD" },
    { label: "Image URL", key: "image_url", placeholder: "https://example.com/product.jpg" },
  ],
  BreadcrumbList: [],
  Organization: [
    { label: "Name", key: "name", required: true, placeholder: "Organization name" },
    { label: "URL", key: "url", placeholder: "https://example.com" },
    { label: "Logo URL", key: "logo_url", placeholder: "https://example.com/logo.png" },
    { label: "Description", key: "description", placeholder: "Brief description" },
  ],
};

function GeneratorTab() {
  const [schemaType, setSchemaType] = useState("Article");
  const [params, setParams] = useState<Record<string, string>>({});
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<{ valid: boolean; errors: string[] } | null>(null);

  const fields = SCHEMA_FIELDS[schemaType] ?? [];

  const generate = useCallback(async () => {
    setError(null);
    setValidationResult(null);
    try {
      // Convert params to appropriate types
      const typedParams: Record<string, unknown> = {};
      for (const [k, v] of Object.entries(params)) {
        if (v === "") continue;
        const field = fields.find((f) => f.key === k);
        if (field?.type === "number") {
          typedParams[k] = parseFloat(v) || undefined;
        } else {
          typedParams[k] = v;
        }
      }

      // Special handling for FAQPage
      if (schemaType === "FAQPage") {
        const faqJson = params._faq_items || "[]";
        try {
          typedParams.items = JSON.parse(faqJson);
        } catch {
          setError("FAQ items must be valid JSON array: [{\"question\": \"...\", \"answer\": \"...\"}]");
          return;
        }
      }

      // Special handling for HowTo steps
      if (schemaType === "HowTo") {
        const stepsJson = params._steps || "[]";
        try {
          typedParams.steps = JSON.parse(stepsJson);
        } catch {
          setError("HowTo steps must be valid JSON array: [{\"name\": \"...\", \"text\": \"...\"}]");
          return;
        }
      }

      // Special handling for BreadcrumbList
      if (schemaType === "BreadcrumbList") {
        const itemsJson = params._items || "[]";
        try {
          typedParams.items = JSON.parse(itemsJson);
        } catch {
          setError("Breadcrumb items must be valid JSON array: [{\"name\": \"...\", \"url\": \"...\"}]");
          return;
        }
      }

      const r = await api.generate(schemaType, typedParams);
      setResult(JSON.stringify(r.generated, null, 2));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [schemaType, params, fields]);

  const validate = useCallback(async () => {
    if (!result) return;
    setValidating(true);
    try {
      const r = await api.validate(result);
      setValidationResult({ valid: r.valid, errors: r.errors });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
    setValidating(false);
  }, [result]);

  return (
    <>
      <h3>Generate Schema</h3>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="row" style={{ gap: 8, marginBottom: 12, flexWrap: "wrap" }}>
          <span className="muted" style={{ fontSize: 12, alignSelf: "center" }}>Type:</span>
          {["Article", "FAQPage", "HowTo", "Product", "BreadcrumbList", "Organization"].map((t) => (
            <button key={t} className={`small${schemaType === t ? "" : " secondary"}`} onClick={() => { setSchemaType(t); setParams({}); setResult(null); setValidationResult(null); }}>
              {t}
            </button>
          ))}
        </div>

        {error && <ErrorBox message={error} />}

        {/* Dynamic fields */}
        {fields.map((f) => (
          <div key={f.key} style={{ marginBottom: 8 }}>
            <label style={{ fontSize: 12, display: "block", marginBottom: 2 }}>
              {f.label} {f.required && <span style={{ color: "#ef4444" }}>*</span>}
            </label>
            <input
              type={f.type ?? "text"}
              placeholder={f.placeholder}
              value={params[f.key] ?? ""}
              onChange={(e) => setParams((p) => ({ ...p, [f.key]: e.target.value }))}
              style={{ width: "100%" }}
            />
          </div>
        ))}

        {/* Special JSON inputs for complex schemas */}
        {schemaType === "FAQPage" && (
          <div style={{ marginBottom: 8 }}>
            <label style={{ fontSize: 12, display: "block", marginBottom: 2 }}>FAQ Items (JSON array)</label>
            <textarea
              value={params._faq_items ?? '[{"question": "What is SEO?", "answer": "Search Engine Optimization..."}]'}
              onChange={(e) => setParams((p) => ({ ...p, _faq_items: e.target.value }))}
              rows={4}
              style={{ width: "100%", fontFamily: "monospace", fontSize: 11 }}
            />
          </div>
        )}

        {schemaType === "HowTo" && (
          <div style={{ marginBottom: 8 }}>
            <label style={{ fontSize: 12, display: "block", marginBottom: 2 }}>Steps (JSON array)</label>
            <textarea
              value={params._steps ?? '[{"name": "Step 1", "text": "Do this first..."}, {"name": "Step 2", "text": "Then do this..."}]'}
              onChange={(e) => setParams((p) => ({ ...p, _steps: e.target.value }))}
              rows={4}
              style={{ width: "100%", fontFamily: "monospace", fontSize: 11 }}
            />
          </div>
        )}

        {schemaType === "BreadcrumbList" && (
          <div style={{ marginBottom: 8 }}>
            <label style={{ fontSize: 12, display: "block", marginBottom: 2 }}>Breadcrumb Items (JSON array)</label>
            <textarea
              value={params._items ?? '[{"name": "Home", "url": "https://example.com"}, {"name": "Blog", "url": "https://example.com/blog"}]'}
              onChange={(e) => setParams((p) => ({ ...p, _items: e.target.value }))}
              rows={4}
              style={{ width: "100%", fontFamily: "monospace", fontSize: 11 }}
            />
          </div>
        )}

        <button className="small" onClick={generate}>Generate</button>
      </div>

      {/* Preview */}
      {result && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="row" style={{ justifyContent: "space-between", marginBottom: 8 }}>
            <h3 style={{ margin: 0 }}>Preview</h3>
            <div className="row" style={{ gap: 8 }}>
              <button className="small" onClick={validate} disabled={validating}>
                {validating ? "Validating…" : "✓ Validate"}
              </button>
              <button className="small" onClick={() => {
                navigator.clipboard.writeText(result);
                alert("Copied to clipboard!");
              }}>📋 Copy</button>
            </div>
          </div>

          {validationResult && (
            <div style={{ marginBottom: 12, padding: 8, borderRadius: 6, background: validationResult.valid ? "#f0fdf4" : "#fef2f2", border: `1px solid ${validationResult.valid ? "#22c55e" : "#ef4444"}` }}>
              {validationResult.valid ? (
                <span style={{ color: "#22c55e", fontWeight: 600 }}>✅ Valid JSON-LD</span>
              ) : (
                <div>
                  <span style={{ color: "#ef4444", fontWeight: 600 }}>❌ {validationResult.errors.length} error(s):</span>
                  <ul style={{ margin: "4px 0 0 16px", fontSize: 12 }}>
                    {validationResult.errors.map((err, i) => <li key={i}>{err}</li>)}
                  </ul>
                </div>
              )}
            </div>
          )}

          <pre style={{
            background: "#f9fafb",
            padding: 12,
            borderRadius: 6,
            fontSize: 11,
            overflow: "auto",
            maxHeight: 400,
            border: "1px solid #e5e7eb",
          }}>
            {result}
          </pre>
        </div>
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Validator Tab
// ---------------------------------------------------------------------------

function ValidatorTab() {
  const [input, setInput] = useState("");
  const [result, setResult] = useState<{ valid: boolean; errors: string[]; schema_type: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const validate = useCallback(async () => {
    setError(null);
    try {
      const r = await api.validate(input);
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [input]);

  return (
    <>
      <h3>Validate JSON-LD</h3>
      <p className="muted" style={{ fontSize: 12, marginBottom: 8 }}>Paste existing JSON-LD markup to check for errors.</p>
      {error && <ErrorBox message={error} />}
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        rows={10}
        placeholder='{"@context": "https://schema.org", "@type": "Article", "headline": "..."}'
        style={{ width: "100%", fontFamily: "monospace", fontSize: 11, marginBottom: 8 }}
      />
      <button className="small" onClick={validate} disabled={!input.trim()}>Validate</button>

      {result && (
        <div className="card" style={{ marginTop: 12 }}>
          <div style={{ padding: 8, borderRadius: 6, background: result.valid ? "#f0fdf4" : "#fef2f2", border: `1px solid ${result.valid ? "#22c55e" : "#ef4444"}`, marginBottom: 8 }}>
            {result.valid ? (
              <span style={{ color: "#22c55e", fontWeight: 600 }}>✅ Valid — {result.schema_type}</span>
            ) : (
              <div>
                <span style={{ color: "#ef4444", fontWeight: 600 }}>❌ {result.errors.length} error(s):</span>
                <ul style={{ margin: "4px 0 0 16px", fontSize: 12 }}>
                  {result.errors.map((err, i) => <li key={i}>{err}</li>)}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Coverage Tab
// ---------------------------------------------------------------------------

function CoverageTab() {
  const { active } = useWebsiteStore();
  const coverage = useAsync(() => active ? api.coverage(active.id) : Promise.resolve(null), [active?.id]);

  if (coverage.loading) return <Loading />;
  if (coverage.error) return <ErrorBox message={coverage.error} />;

  const data = coverage.data;

  return (
    <>
      <h3>Schema Coverage {active ? `— ${active.name}` : ""}</h3>
      {data ? (
        <div className="row" style={{ gap: 16, flexWrap: "wrap" }}>
          <div className="card" style={{ flex: 1, textAlign: "center" }}>
            <div style={{ fontSize: 28, fontWeight: 700 }}>{data.total_pages}</div>
            <div className="muted" style={{ fontSize: 12 }}>Total Pages</div>
          </div>
          <div className="card" style={{ flex: 1, textAlign: "center" }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: "#22c55e" }}>{data.pages_with_schema}</div>
            <div className="muted" style={{ fontSize: 12 }}>With Schema</div>
          </div>
          <div className="card" style={{ flex: 1, textAlign: "center" }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: "#ef4444" }}>{data.pages_without_schema}</div>
            <div className="muted" style={{ fontSize: 12 }}>Without Schema</div>
          </div>
          <div className="card" style={{ flex: 1, textAlign: "center" }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: "#3b82f6" }}>{data.coverage_pct}%</div>
            <div className="muted" style={{ fontSize: 12 }}>Coverage</div>
          </div>
        </div>
      ) : (
        <p className="muted">No website selected.</p>
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

type Tab = "generate" | "validate" | "coverage";

export default function SchemaMarkup() {
  const [tab, setTab] = useState<Tab>("generate");

  return (
    <>
      <h2 className="page-title">📐 Schema Markup Builder</h2>
      <p className="page-sub">
        Generate, validate, and preview JSON-LD structured data for rich snippets in search results.
      </p>

      <div className="row" style={{ gap: 4, marginBottom: 16 }}>
        {([
          ["generate", "Generate"],
          ["validate", "Validate"],
          ["coverage", "Coverage"],
        ] as [Tab, string][]).map(([key, label]) => (
          <button key={key} className={`small${tab === key ? "" : " secondary"}`} onClick={() => setTab(key)} style={{ fontWeight: tab === key ? 700 : 400 }}>
            {label}
          </button>
        ))}
      </div>

      {tab === "generate" && <GeneratorTab />}
      {tab === "validate" && <ValidatorTab />}
      {tab === "coverage" && <CoverageTab />}
    </>
  );
}
