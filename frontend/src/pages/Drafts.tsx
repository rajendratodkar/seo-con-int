import { useEffect, useState } from "react";
import { drafts, publishing } from "../services/backend";
import { AiBadge, Badge, Empty, ErrorBox, Loading } from "../components/common";
import { useAsync } from "../hooks/useAsync";
import type { DraftSummary } from "../types";

export default function Drafts() {
  const list = useAsync(() => drafts.list(), []);
  const logs = useAsync(() => publishing.logs(), []);
  const [selected, setSelected] = useState<number | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reloadAll = async () => {
    await Promise.all([list.reload(), logs.reload()]);
  };

  return (
    <>
      <h2 className="page-title">Drafts &amp; Publishing</h2>
      <p className="page-sub">
        Edit and approve drafts, then send them out. Only <Badge value="approved" /> drafts can leave the app.
      </p>
      {notice && <div className="card" style={{ borderColor: "var(--green)" }}>{notice}</div>}
      {error && <ErrorBox message={error} />}

      <div className="card">
        <div className="row" style={{ alignItems: "flex-start", gap: 16 }}>
          <div style={{ minWidth: 320 }}>
            <h3>Drafts</h3>
            {list.loading ? (
              <Loading />
            ) : list.data && list.data.items.length > 0 ? (
              <table className="data">
                <thead><tr><th>Title</th><th>v</th><th>Status</th></tr></thead>
                <tbody>
                  {list.data.items.map((d) => (
                    <tr key={d.id} onClick={() => { setSelected(d.id); setNotice(null); setError(null); }}
                        style={{ cursor: "pointer", background: selected === d.id ? "rgba(45,212,191,0.08)" : undefined }}>
                      <td>{d.plan_title} {d.ai_provider && <AiBadge />}</td>
                      <td>{d.version}</td>
                      <td><Badge value={d.status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <Empty text="No drafts yet. Generate one from the Article Planner." />
            )}
          </div>
          <div style={{ flex: 1 }}>
            {selected ? (
              <DraftEditor
                draftId={selected}
                onChanged={reloadAll}
                onNotice={setNotice}
                onError={setError}
              />
            ) : (
              <p className="muted">Select a draft to edit, approve, or publish.</p>
            )}
          </div>
        </div>
      </div>

      <TargetConfig onSaved={() => setNotice("Target configuration saved.")} onError={setError} />

      <div className="card">
        <h3>Publishing history</h3>
        {logs.loading ? (
          <Loading />
        ) : logs.data && logs.data.items.length > 0 ? (
          <table className="data">
            <thead><tr><th>When</th><th>Draft</th><th>Target</th><th>Action</th><th>Status</th><th>Result</th></tr></thead>
            <tbody>
              {logs.data.items.map((log) => (
                <tr key={log.id}>
                  <td className="mono">{log.created_at}</td>
                  <td>#{log.draft_id}</td>
                  <td>{log.target}</td>
                  <td>{log.action}</td>
                  <td><Badge value={log.status} /></td>
                  <td>
                    {log.remote_url
                      ? <a className="plain" href={log.remote_url} target="_blank" rel="noreferrer">open ↗</a>
                      : log.error ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <Empty text="Nothing published yet." />
        )}
      </div>
    </>
  );
}

function DraftEditor({ draftId, onChanged, onNotice, onError }: {
  draftId: number;
  onChanged: () => Promise<void>;
  onNotice: (msg: string) => void;
  onError: (msg: string) => void;
}) {
  const draft = useAsync(() => drafts.get(draftId), [draftId]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (draft.data) setText(draft.data.content);
  }, [draft.data?.id]);

  if (draft.loading) return <Loading />;
  if (draft.error) return <ErrorBox message={draft.error} />;
  if (!draft.data) return null;

  const d = draft.data;
  const verifyCount = (text.match(/\[VERIFY:/g) ?? []).length;

  const save = async () => {
    setBusy(true); onError("");
    try {
      await drafts.edit(d.id, text);
      onNotice("Draft saved — status is now human_edited.");
      await Promise.all([draft.reload(), onChanged()]);
    } catch (e) { onError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  };

  const approve = async () => {
    setBusy(true); onError("");
    try {
      await drafts.edit(d.id, text);
      await drafts.approve(d.id);
      onNotice("Draft approved. It can now be published.");
      await Promise.all([draft.reload(), onChanged()]);
    } catch (e) { onError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  };

  const publishWp = async (status: "draft" | "publish") => {
    setBusy(true); onError("");
    try {
      const res = await publishing.wordpress(d.id, status);
      onNotice(`Sent to WordPress as ${status}${res.remote_url ? `: ${res.remote_url}` : ""}.`);
      await onChanged();
    } catch (e) { onError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  };

  const publishGh = async () => {
    setBusy(true); onError("");
    try {
      const res = await publishing.github(d.id);
      onNotice(`Committed to GitHub (${res.path ?? ""} on ${res.branch ?? "branch"}).`);
      await onChanged();
    } catch (e) { onError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  };

  return (
    <div>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h3>{d.plan_title} <span className="muted">v{d.version}</span> <Badge value={d.status} /> {d.ai_provider && <AiBadge />}</h3>
        <div className="row">
          <button className="small" disabled={busy} onClick={save}>Save edits</button>
          <button className="small primary" disabled={busy} onClick={approve}>Approve</button>
        </div>
      </div>
      {d.status !== "approved" && (
        <p className="muted">AI output stays an <strong>AI suggestion</strong> until you edit and approve it.</p>
      )}
      {verifyCount > 0 && (
        <p style={{ color: "var(--amber)" }}>
          ⚠ {verifyCount} unverified fact placeholder{verifyCount > 1 ? "s" : ""} ([VERIFY: …]) remain — resolve them before approval.
        </p>
      )}
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        style={{ width: "100%", minHeight: 320, fontFamily: "var(--mono, monospace)", fontSize: 13 }}
      />
      {d.status === "approved" && (
        <div className="row" style={{ marginTop: 8 }}>
          <span className="muted">Publish:</span>
          <button className="small" disabled={busy} onClick={() => publishWp("draft")}>WordPress → draft</button>
          <button className="small" disabled={busy} onClick={() => publishWp("publish")}>WordPress → publish</button>
          <button className="small" disabled={busy} onClick={publishGh}>GitHub commit</button>
        </div>
      )}
    </div>
  );
}

function TargetConfig({ onSaved, onError }: { onSaved: () => void; onError: (msg: string) => void }) {
  const wp = useAsync(() => publishing.config("wordpress"), []);
  const gh = useAsync(() => publishing.config("github"), []);
  const [wpFields, setWpFields] = useState({ site_url: "", user: "", app_password: "" });
  const [ghFields, setGhFields] = useState({ repo: "", branch: "", path_template: "", token: "" });
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (wp.data) setWpFields((f) => ({ ...f, site_url: wp.data!.site_url ?? "", user: wp.data!.user ?? "" }));
  }, [wp.data?.target]);
  useEffect(() => {
    if (gh.data) setGhFields((f) => ({
      ...f,
      repo: gh.data!.repo ?? "",
      branch: gh.data!.branch ?? "",
      path_template: gh.data!.path_template ?? "",
    }));
  }, [gh.data?.target]);

  const saveWp = async () => {
    setBusy(true);
    try {
      const fields: Record<string, string> = { site_url: wpFields.site_url, user: wpFields.user };
      if (wpFields.app_password) fields.app_password = wpFields.app_password;
      await publishing.saveConfig("wordpress", fields);
      setWpFields((f) => ({ ...f, app_password: "" }));
      await wp.reload();
      onSaved();
    } catch (e) { onError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  };

  const saveGh = async () => {
    setBusy(true);
    try {
      const fields: Record<string, string> = {
        repo: ghFields.repo, branch: ghFields.branch, path_template: ghFields.path_template,
      };
      if (ghFields.token) fields.token = ghFields.token;
      await publishing.saveConfig("github", fields);
      setGhFields((f) => ({ ...f, token: "" }));
      await gh.reload();
      onSaved();
    } catch (e) { onError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  };

  return (
    <div className="card">
      <h3>Publishing targets</h3>
      <div className="row" style={{ alignItems: "flex-start", gap: 24 }}>
        <div style={{ flex: 1 }}>
          <h4>WordPress {wp.data?.has_app_password && <span className="muted">(credentials stored)</span>}</h4>
          <div className="row"><input placeholder="https://example.com" value={wpFields.site_url}
            onChange={(e) => setWpFields({ ...wpFields, site_url: e.target.value })} /></div>
          <div className="row"><input placeholder="WP username" value={wpFields.user}
            onChange={(e) => setWpFields({ ...wpFields, user: e.target.value })} /></div>
          <div className="row"><input type="password" placeholder="Application password" value={wpFields.app_password}
            onChange={(e) => setWpFields({ ...wpFields, app_password: e.target.value })} /></div>
          <button className="small primary" disabled={busy} onClick={saveWp}>Save WordPress config</button>
        </div>
        <div style={{ flex: 1 }}>
          <h4>GitHub / Astro {gh.data?.has_token && <span className="muted">(token stored)</span>}</h4>
          <div className="row"><input placeholder="owner/repo" value={ghFields.repo}
            onChange={(e) => setGhFields({ ...ghFields, repo: e.target.value })} /></div>
          <div className="row"><input placeholder="branch (default: main)" value={ghFields.branch}
            onChange={(e) => setGhFields({ ...ghFields, branch: e.target.value })} /></div>
          <div className="row"><input placeholder="src/content/blog/{slug}.md" value={ghFields.path_template}
            onChange={(e) => setGhFields({ ...ghFields, path_template: e.target.value })} /></div>
          <div className="row"><input type="password" placeholder="Personal access token" value={ghFields.token}
            onChange={(e) => setGhFields({ ...ghFields, token: e.target.value })} /></div>
          <button className="small primary" disabled={busy} onClick={saveGh}>Save GitHub config</button>
        </div>
      </div>
      <p className="muted">Secrets are encrypted at rest. Approved drafts go out as WordPress drafts or branch commits — never silent live publishing.</p>
    </div>
  );
}
