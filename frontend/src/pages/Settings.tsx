import { useState } from "react";
import { searchConsole, settings as api } from "../services/backend";
import { Badge, ErrorBox, Loading } from "../components/common";
import { useAsync } from "../hooks/useAsync";

const PROVIDERS = ["openai", "gemini", "anthropic"];

export default function Settings() {
  const list = useAsync(() => api.providers(), []);
  const google = useAsync(() => searchConsole.oauthConfig(), []);
  const [keys, setKeys] = useState<Record<string, string>>({});
  const [clientId, setClientId] = useState<string | null>(null);
  const [clientSecret, setClientSecret] = useState<string | null>(null);
  const [googleSaved, setGoogleSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);

  if (list.loading || google.loading) return <Loading />;
  if (list.error) return <ErrorBox message={list.error} />;

  const save = async (provider: string, enabled: boolean, isDefault: boolean) => {
    setError(null);
    setSaved(null);
    try {
      const apiKey = keys[provider]?.trim() || null;
      await api.saveProvider(provider, apiKey, enabled, isDefault);
      setSaved(provider);
      setKeys((prev) => ({ ...prev, [provider]: "" }));
      await list.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const saveGoogle = async () => {
    setError(null);
    setGoogleSaved(false);
    try {
      await searchConsole.saveOauthConfig(
        clientId ?? google.data?.client_id ?? "",
        clientSecret ?? google.data?.client_secret ?? "",
      );
      setGoogleSaved(true);
      await google.reload();
      setClientId(null);
      setClientSecret(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <>
      <h2 className="page-title">Settings</h2>
      <p className="page-sub">AI providers are used only for discussion + drafts. All AI output is labeled.</p>

      {error && <ErrorBox message={error} />}

      <div className="card">
        <h3>AI providers</h3>
        <p className="muted">API keys are encrypted at rest and never returned by the API.</p>
        <table className="data">
          <thead><tr><th>Provider</th><th>Model</th><th>Key</th><th>Status</th><th>Save</th></tr></thead>
          <tbody>
            {PROVIDERS.map((provider) => {
              const existing = list.data?.items.find((p) => p.provider === provider);
              return (
                <tr key={provider}>
                  <td><strong>{provider}</strong> {existing?.is_default && <Badge value="approved" />}</td>
                  <td className="mono">{existing?.model ?? "default"}</td>
                  <td>
                    <input
                      type="password"
                      placeholder={existing?.has_api_key ? "•••• stored (leave blank to keep)" : "API key"}
                      value={keys[provider] ?? ""}
                      onChange={(e) => setKeys((prev) => ({ ...prev, [provider]: e.target.value }))}
                      style={{ width: 220 }}
                    />
                  </td>
                  <td>
                    {saved === provider && <span className="badge green">saved</span>}
                    {existing?.enabled ? <Badge value="full" /> : <Badge value="pending" />}
                  </td>
                  <td>
                    <button className="small" onClick={() => save(provider, true, true)}>Enable + default</button>{" "}
                    <button className="small" onClick={() => save(provider, false, false)}>Disable</button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>Google (Search Console &amp; Analytics)</h3>
        <p className="muted">
          Create an OAuth client in the <strong>Google Cloud Console</strong> (type: <em>Desktop app</em>),
          enable the <em>Google Search Console API</em> (and optionally the Analytics API), then paste the
          credentials below. Full step-by-step: click the ℹ button on the Search Console page.
        </p>
        <div className="row" style={{ flexDirection: "column", alignItems: "stretch", gap: 8 }}>
          <input
            style={{ minWidth: 340 }}
            placeholder="OAuth Client ID (…apps.googleusercontent.com)"
            value={clientId ?? google.data?.client_id ?? ""}
            onChange={(e) => setClientId(e.target.value)}
          />
          <input
            style={{ minWidth: 340 }}
            type="password"
            placeholder={google.data?.client_secret ? "•••• stored (type to replace)" : "OAuth Client Secret"}
            value={clientSecret ?? ""}
            onChange={(e) => setClientSecret(e.target.value)}
          />
          <div className="row">
            <button className="primary" onClick={saveGoogle}>Save Google credentials</button>
            {googleSaved && <span className="badge green">saved</span>}
            {google.data?.client_id ? <Badge value="full" /> : <Badge value="pending" />}
          </div>
        </div>
        <p className="muted" style={{ marginTop: 8 }}>
          Authorized redirect URI to add in Google Cloud Console:{" "}
          <code className="mono">{google.data?.redirect_uri}</code>
        </p>
      </div>

      <div className="card">
        <h3>Backend token</h3>
        <p className="muted">
          If the backend requires a token (SCI_BACKEND_TOKEN), paste it here. It is stored locally in
          your browser only and sent as X-Backend-Token.
        </p>
        <div className="row">
          <input
            style={{ minWidth: 340 }}
            placeholder="Backend token (optional)"
            defaultValue={localStorage.getItem("sci_backend_token") ?? ""}
            onBlur={(e) => localStorage.setItem("sci_backend_token", e.target.value)}
          />
        </div>
      </div>
    </>
  );
}
