import { useState } from "react";
import { Link } from "react-router-dom";
import { searchConsole as api } from "../services/backend";
import { useWebsiteStore } from "../stores/websiteStore";
import { Empty, ErrorBox, Loading } from "../components/common";
import { useAsync } from "../hooks/useAsync";

// File upload section component
function FileUploadSection({ websiteId }: { websiteId: number }) {
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<{ message: string; rows_imported?: number } | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadError(null);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("website_id", String(websiteId));
      formData.append("import_type", "performance");

      const response = await fetch("/api/sc-upload/upload", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.message || "Upload failed");
      }

      setUploadResult(result);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : String(err));
    } finally {
      setUploading(false);
      e.target.value = ""; // Reset file input
    }
  };

  return (
    <div className="card">
      <h3>📁 Upload Search Console Data</h3>
      <p className="muted">
        Import data from Google Search Console exports. Supports CSV and JSON files.
      </p>
      <div className="row" style={{ alignItems: "center" }}>
        <label className="btn" style={{ cursor: "pointer" }}>
          {uploading ? "Uploading…" : "Choose CSV or JSON file"}
          <input
            type="file"
            accept=".csv,.json"
            onChange={handleFileUpload}
            disabled={uploading}
            style={{ display: "none" }}
          />
        </label>
        <span className="muted">Supported: Performance report CSV, GSC API JSON</span>
      </div>
      {uploadError && <ErrorBox message={uploadError} />}
      {uploadResult && (
        <div className="card" style={{ borderColor: "var(--green)", marginTop: 12 }}>
          ✅ {uploadResult.message}
          {uploadResult.rows_imported != null && (
            <span className="muted" style={{ marginLeft: 8 }}>
              ({uploadResult.rows_imported} rows imported)
            </span>
          )}
        </div>
      )}
    </div>
  );
}

export default function SearchConsole() {
  const [showUpload, setShowUpload] = useState(false);
  const { active } = useWebsiteStore();
  const status = useAsync(() => api.oauthStatus(), []);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [showGuide, setShowGuide] = useState(false);

  if (!active) return <Empty text="Add a website first." />;
  if (status.loading) return <Loading />;

  const configured = status.data?.configured ?? false;
  const connected = status.data?.connected ?? false;

  const startOAuth = async () => {
    setError(null);
    setMessage(null);
    try {
      const result = await api.oauthUrl();
      const url = result.auth_url ?? result.url;
      if (!result.configured || !url) {
        // No Google credentials yet — point the user at Settings + the guide.
        setShowGuide(true);
        setError(
          "Google credentials are not configured yet. Add your OAuth Client ID and Client Secret " +
            "in Settings → Google, then come back. The ℹ guide below explains the whole process.",
        );
        return;
      }
      window.open(url, "_blank");
      setMessage(
        "Google sign-in opened in a new tab. Sign in and click Allow — the tab then shows a " +
          "confirmation. Return here and click “2 · Discover properties”.",
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const discover = async () => {
    setError(null);
    setMessage(null);
    try {
      const result = await api.discover();
      setMessage(`Discovered ${(result.items ?? []).length} properties. Connect one to this website below.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <>
      <div className="row" style={{ alignItems: "center" }}>
        <h2 className="page-title" style={{ margin: 0 }}>Search Console</h2>
        <button
          className="small"
          title="How to connect your Google account"
          onClick={() => setShowGuide((v) => !v)}
          aria-label="How to connect your Google account"
        >
          ℹ How to connect
        </button>
        <span className="spacer" />
        <span className={configured ? "badge green" : "badge"}>
          {configured ? "Google client configured" : "Google client not configured"}
        </span>
        <span className={connected ? "badge green" : "badge"}>
          {connected ? "Google account connected" : "Not connected"}
        </span>
        <button className="small" onClick={() => status.reload()}>Refresh status</button>
      </div>
      <p className="page-sub">Connect Google Search Console for “{active.name}” and import performance data.</p>

      {showGuide && <ConnectGuide redirectUri={status.data?.redirect_uri} />}

      <div className="card">
        <div className="row">
          <button className="primary" onClick={startOAuth}>1 · Connect Google account</button>
          <button onClick={discover}>2 · Discover properties</button>
          <button onClick={() => setShowUpload((v) => !v)}>📁 Upload CSV/JSON</button>
        </div>
        {message && <p className="muted">{message}</p>}
        {error && <ErrorBox message={error} />}
        <p className="muted">
          Requires a Google OAuth client configured in <Link to="/settings">Settings → Google</Link>. Raw API
          payloads are kept for recalculation; imported rows are never overwritten in place.
        </p>
      </div>

      {showUpload && <FileUploadSection websiteId={active.id} />}

      <PropertiesTable websiteId={active.id} />
    </>
  );
}

function ConnectGuide({ redirectUri }: { redirectUri?: string }) {
  return (
    <div className="card">
      <h3>How to connect your Google account</h3>
      <p className="muted">One-time setup in the Google Cloud Console, then connect from this app.</p>
      <ol style={{ lineHeight: 1.7, paddingLeft: 22 }}>
        <li>
          Open the <strong>Google Cloud Console</strong> (console.cloud.google.com) and sign in with the same
          Google account that has access to your Search Console property.
        </li>
        <li>
          Select an existing project or create a new one (top-left project dropdown → <em>New Project</em>).
        </li>
        <li>
          Enable the APIs: go to <em>APIs &amp; Services → Library</em>, search for{" "}
          <strong>Google Search Console API</strong> and click <em>Enable</em> (optionally also enable the{" "}
          <em>Google Analytics API</em>).
        </li>
        <li>
          Configure the consent screen: <em>APIs &amp; Services → OAuth consent screen</em>, choose{" "}
          <em>External</em>, fill in the app name and your email, then under <em>Test users</em> add the Google
          account you want to connect.
        </li>
        <li>
          Create credentials: <em>APIs &amp; Services → Credentials → Create Credentials → OAuth client ID</em>,
          application type <strong>Desktop app</strong>, give it a name and click <em>Create</em>. Desktop apps
          automatically allow the local redirect this app uses
          {redirectUri ? (<><code className="mono"> ({redirectUri})</code></>) : null}.
        </li>
        <li>
          Copy the <strong>Client ID</strong> and <strong>Client Secret</strong>, open{" "}
          <Link to="/settings">Settings → Google</Link> in this app, paste both and save.
        </li>
        <li>
          Back here: click <strong>1 · Connect Google account</strong>, sign in and click <em>Allow</em>. A
          confirmation page appears in that tab.
        </li>
        <li>
          Return here, click <strong>2 · Discover properties</strong>, pick your site and click{" "}
          <em>Connect to website</em>, then <em>Sync</em> to import performance data.
        </li>
      </ol>
      <p className="muted">
        Tokens are stored locally and refreshed automatically. Because the app is in “test users” mode, Google
        may show an “unverified app” warning — click <em>Advanced → Continue</em>; this is expected for a private
        desktop app.
      </p>
    </div>
  );
}

function PropertiesTable({ websiteId }: { websiteId: number }) {
  const [properties, setProperties] = useState<Array<Record<string, unknown>> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setError(null);
    try {
      const result = await api.properties();
      setProperties((result.items ?? []) as Array<Record<string, unknown>>);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const connect = async (propertyId: number) => {
    await api.connect(propertyId, websiteId);
    await load();
  };

  const sync = async (propertyId: number) => {
    try {
      await api.sync(propertyId);
      alert("Sync started in the background.");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div className="card">
      <div className="row">
        <h3 style={{ margin: 0 }}>Properties</h3>
        <span className="spacer" />
        <button className="small" onClick={load}>Load</button>
      </div>
      {error && <ErrorBox message={error} />}
      {properties && properties.length === 0 && <p className="muted">No properties found yet.</p>}
      {properties && properties.length > 0 && (
        <table className="data">
          <thead><tr><th>Property</th><th>Permission</th><th>Status</th><th></th></tr></thead>
          <tbody>
            {properties.map((p) => (
              <tr key={String(p.id)}>
                <td className="mono">{String(p.site_url)}</td>
                <td>{String(p.permission_level ?? "—")}</td>
                <td>{String(p.status)}</td>
                <td>
                  {p.website_id ? (
                    <button className="small" onClick={() => sync(Number(p.id))}>Sync</button>
                  ) : (
                    <button className="small" onClick={() => connect(Number(p.id))}>Connect to website</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
