import { useCallback, useState } from "react";
import { monitoring as api } from "../services/backend";
import { Badge, ErrorBox, Loading } from "../components/common";
import { useAsync } from "../hooks/useAsync";
import { useWebsiteStore } from "../stores/websiteStore";
import type { AlertChannel, AlertHistoryEntry, MonitoringRule } from "../types";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const RULE_TYPES = [
  { value: "ranking_drop", label: "Ranking Drop", desc: "Average position worsens beyond threshold" },
  { value: "traffic_drop", label: "Traffic Drop", desc: "Total clicks drop significantly" },
  { value: "ctr_drop", label: "CTR Drop", desc: "Click-through rate drops while position stays stable" },
  { value: "new_seo_issue", label: "New SEO Issue", desc: "New open findings detected" },
  { value: "crawl_error", label: "Crawl Error", desc: "HTTP errors or crawl failures" },
];

const INTERVALS = [
  { value: "hourly", label: "Hourly" },
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
];

// ---------------------------------------------------------------------------
// Channels Tab
// ---------------------------------------------------------------------------

function ChannelsTab() {
  const list = useAsync(() => api.channels(), []);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [type, setType] = useState("desktop");
  const [config, setConfig] = useState("");
  const [testing, setTesting] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const create = useCallback(async () => {
    setError(null);
    try {
      const parsed = config.trim() ? JSON.parse(config) : {};
      await api.createChannel(name, type, parsed);
      setShowForm(false);
      setName("");
      setConfig("");
      await list.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [name, type, config, list]);

  const test = useCallback(async (id: number) => {
    setTesting(id);
    try {
      const result = await api.testChannel(id);
      if (!result.success) setError(result.error ?? "Test failed");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
    setTesting(null);
  }, []);

  const remove = useCallback(async (id: number) => {
    try {
      await api.deleteChannel(id);
      await list.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [list]);

  const toggle = useCallback(async (ch: AlertChannel) => {
    try {
      await api.updateChannel(ch.id, { enabled: !ch.enabled });
      await list.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [list]);

  if (list.loading) return <Loading />;
  if (list.error) return <ErrorBox message={list.error} />;

  const channels: AlertChannel[] = list.data ?? [];

  return (
    <>
      <div className="row" style={{ justifyContent: "space-between", marginBottom: 12 }}>
        <h3 style={{ margin: 0 }}>Alert Channels</h3>
        <button className="small" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "+ Add Channel"}
        </button>
      </div>

      {error && <ErrorBox message={error} />}

      {showForm && (
        <div className="card" style={{ marginBottom: 12 }}>
          <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
            <input placeholder="Channel name" value={name} onChange={(e) => setName(e.target.value)} style={{ width: 200 }} />
            <select value={type} onChange={(e) => setType(e.target.value)}>
              <option value="desktop">Desktop Notification</option>
              <option value="email">Email (SMTP)</option>
              <option value="slack">Slack Webhook</option>
            </select>
            <input
              placeholder='Config JSON (e.g. {"webhook_url": "..."})'
              value={config}
              onChange={(e) => setConfig(e.target.value)}
              style={{ flex: 1, minWidth: 300 }}
            />
            <button className="small" onClick={create} disabled={!name}>Create</button>
          </div>
          <p className="muted" style={{ marginTop: 8, fontSize: 12 }}>
            Email needs: {"{"}"smtp_host", "from_address", "to_addresses": ["..."]{"}"}
            &nbsp;&middot; Slack needs: {"{"}"webhook_url": "https://hooks.slack.com/..."{"}"} &middot; Desktop needs: {"{}"}
          </p>
        </div>
      )}

      {channels.length === 0 ? (
        <p className="muted">No channels configured. Add one to start receiving alerts.</p>
      ) : (
        <table className="data">
          <thead>
            <tr><th>Name</th><th>Type</th><th>Status</th><th>Last Tested</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {channels.map((ch) => (
              <tr key={ch.id}>
                <td><strong>{ch.name}</strong></td>
                <td><Badge value={ch.channel_type} /></td>
                <td>{ch.enabled ? <Badge value="full" /> : <Badge value="pending" />}</td>
                <td className="muted">{ch.last_tested_at ? new Date(ch.last_tested_at).toLocaleString() : "Never"}</td>
                <td>
                  <button className="small" onClick={() => test(ch.id)} disabled={testing === ch.id}>
                    {testing === ch.id ? "Testing…" : "Test"}
                  </button>{" "}
                  <button className="small" onClick={() => toggle(ch)}>
                    {ch.enabled ? "Disable" : "Enable"}
                  </button>{" "}
                  <button className="small" onClick={() => remove(ch.id)}>Delete</button>
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
// Rules Tab
// ---------------------------------------------------------------------------

function RulesTab() {
  const { active } = useWebsiteStore();
  const list = useAsync(() => api.rules(active?.id), [active?.id]);
  const channelList = useAsync(() => api.channels(), []);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [ruleType, setRuleType] = useState("ranking_drop");
  const [interval, setInterval] = useState("daily");
  const [selectedChannels, setSelectedChannels] = useState<number[]>([]);
  const [threshold, setThreshold] = useState("15");
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState<number | null>(null);

  const create = useCallback(async () => {
    if (!active) return;
    setError(null);
    try {
      const config: Record<string, unknown> = { threshold_pct: Number(threshold) };
      await api.createRule({
        website_id: active.id,
        name,
        rule_type: ruleType,
        config,
        channel_ids: selectedChannels,
        check_interval: interval,
      });
      setShowForm(false);
      setName("");
      await list.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [active, name, ruleType, interval, selectedChannels, threshold, list]);

  const toggleRule = useCallback(async (rule: MonitoringRule) => {
    try {
      await api.updateRule(rule.id, { enabled: !rule.enabled });
      await list.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [list]);

  const removeRule = useCallback(async (id: number) => {
    try {
      await api.deleteRule(id);
      await list.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [list]);

  const runCheck = useCallback(async (ruleId: number) => {
    setRunning(ruleId);
    try {
      const result = await api.runCheck(ruleId);
      if (result.alerts_triggered > 0) {
        setError(null);
        alert(`⚠ ${result.alerts_triggered} alert(s) triggered, ${result.notifications_sent} sent.`);
      } else {
        alert("✅ No alerts triggered — everything looks good.");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
    setRunning(null);
  }, []);

  if (list.loading || channelList.loading) return <Loading />;
  if (list.error) return <ErrorBox message={list.error} />;

  const rules: MonitoringRule[] = list.data ?? [];
  const channels: AlertChannel[] = channelList.data ?? [];

  return (
    <>
      <div className="row" style={{ justifyContent: "space-between", marginBottom: 12 }}>
        <h3 style={{ margin: 0 }}>Monitoring Rules {active ? `— ${active.name}` : ""}</h3>
        <div className="row" style={{ gap: 8 }}>
          <button
            className="small"
            onClick={async () => {
              try {
                const r = await api.runAllChecks();
                alert(`Checked ${r.rules_checked} rules, ${r.total_alerts} alert(s) triggered.`);
              } catch (e) {
                setError(e instanceof Error ? e.message : String(e));
              }
            }}
          >
            Run All Checks
          </button>
          <button className="small" onClick={() => setShowForm(!showForm)}>
            {showForm ? "Cancel" : "+ Add Rule"}
          </button>
        </div>
      </div>

      {error && <ErrorBox message={error} />}

      {showForm && (
        <div className="card" style={{ marginBottom: 12 }}>
          <div className="row" style={{ gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
            <input placeholder="Rule name" value={name} onChange={(e) => setName(e.target.value)} style={{ width: 220 }} />
            <select value={ruleType} onChange={(e) => setRuleType(e.target.value)}>
              {RULE_TYPES.map((rt) => (
                <option key={rt.value} value={rt.value}>{rt.label}</option>
              ))}
            </select>
            <select value={interval} onChange={(e) => setInterval(e.target.value)}>
              {INTERVALS.map((iv) => (
                <option key={iv.value} value={iv.value}>{iv.label}</option>
              ))}
            </select>
          </div>
          <div className="row" style={{ gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
            <label style={{ fontSize: 12 }}>
              Threshold %:
              <input
                type="number"
                value={threshold}
                onChange={(e) => setThreshold(e.target.value)}
                style={{ width: 60, marginLeft: 4 }}
                min={1}
                max={100}
              />
            </label>
          </div>
          <div style={{ marginBottom: 8 }}>
            <span className="muted" style={{ fontSize: 12 }}>Notify via: </span>
            {channels.map((ch) => (
              <label key={ch.id} style={{ marginRight: 12, fontSize: 12 }}>
                <input
                  type="checkbox"
                  checked={selectedChannels.includes(ch.id)}
                  onChange={(e) => {
                    setSelectedChannels((prev) =>
                      e.target.checked
                        ? [...prev, ch.id]
                        : prev.filter((id) => id !== ch.id)
                    );
                  }}
                />
                {" "}{ch.name}
              </label>
            ))}
            {channels.length === 0 && <span className="muted" style={{ fontSize: 12 }}>No channels — create one first.</span>}
          </div>
          <p className="muted" style={{ fontSize: 12, marginBottom: 8 }}>
            {RULE_TYPES.find((rt) => rt.value === ruleType)?.desc}
          </p>
          <button className="small" onClick={create} disabled={!name || !active}>Create Rule</button>
        </div>
      )}

      {rules.length === 0 ? (
        <p className="muted">No rules configured. Add one to start monitoring.</p>
      ) : (
        <table className="data">
          <thead>
            <tr><th>Rule</th><th>Type</th><th>Interval</th><th>Status</th><th>Last Checked</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {rules.map((rule) => (
              <tr key={rule.id}>
                <td><strong>{rule.name}</strong></td>
                <td><Badge value={rule.rule_type.replace("_", " ")} /></td>
                <td>{rule.check_interval}</td>
                <td>{rule.enabled ? <Badge value="full" /> : <Badge value="pending" />}</td>
                <td className="muted">{rule.last_checked_at ? new Date(rule.last_checked_at).toLocaleString() : "Never"}</td>
                <td>
                  <button className="small" onClick={() => runCheck(rule.id)} disabled={running === rule.id}>
                    {running === rule.id ? "Running…" : "Check Now"}
                  </button>{" "}
                  <button className="small" onClick={() => toggleRule(rule)}>
                    {rule.enabled ? "Disable" : "Enable"}
                  </button>{" "}
                  <button className="small" onClick={() => removeRule(rule.id)}>Delete</button>
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
// History Tab
// ---------------------------------------------------------------------------

function HistoryTab() {
  const list = useAsync(() => api.history(undefined, 100), []);
  const stats = useAsync(() => api.stats(), []);

  if (list.loading || stats.loading) return <Loading />;
  if (list.error) return <ErrorBox message={list.error} />;

  const history: AlertHistoryEntry[] = list.data ?? [];
  const s = stats.data;

  return (
    <>
      {s && (
        <div className="row" style={{ gap: 16, marginBottom: 16 }}>
          <div className="card" style={{ flex: 1, textAlign: "center" }}>
            <div style={{ fontSize: 28, fontWeight: 700 }}>{s.total}</div>
            <div className="muted" style={{ fontSize: 12 }}>Total Alerts</div>
          </div>
          <div className="card" style={{ flex: 1, textAlign: "center" }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: "#22c55e" }}>{s.by_status?.sent ?? 0}</div>
            <div className="muted" style={{ fontSize: 12 }}>Sent</div>
          </div>
          <div className="card" style={{ flex: 1, textAlign: "center" }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: "#ef4444" }}>{s.by_status?.failed ?? 0}</div>
            <div className="muted" style={{ fontSize: 12 }}>Failed</div>
          </div>
          <div className="card" style={{ flex: 1, textAlign: "center" }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: "#f59e0b" }}>{s.by_severity?.critical ?? 0}</div>
            <div className="muted" style={{ fontSize: 12 }}>Critical</div>
          </div>
        </div>
      )}

      <h3>Alert History</h3>
      {history.length === 0 ? (
        <p className="muted">No alerts sent yet. Run a check to trigger alerts.</p>
      ) : (
        <table className="data">
          <thead>
            <tr><th>Time</th><th>Severity</th><th>Title</th><th>Message</th><th>Status</th></tr>
          </thead>
          <tbody>
            {history.map((h) => (
              <tr key={h.id}>
                <td className="muted" style={{ whiteSpace: "nowrap" }}>{new Date(h.sent_at).toLocaleString()}</td>
                <td><Badge value={h.severity} /></td>
                <td style={{ maxWidth: 250, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{h.title}</td>
                <td style={{ maxWidth: 350, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{h.message}</td>
                <td><Badge value={h.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

type Tab = "channels" | "rules" | "history";

export default function Monitoring() {
  const [tab, setTab] = useState<Tab>("channels");

  return (
    <>
      <h2 className="page-title">🔔 Monitoring & Alerts</h2>
      <p className="page-sub">
        Configure watch rules, alert channels, and review notification history.
      </p>

      <div className="row" style={{ gap: 4, marginBottom: 16 }}>
        {([
          ["channels", "Channels"],
          ["rules", "Rules"],
          ["history", "History"],
        ] as [Tab, string][]).map(([key, label]) => (
          <button
            key={key}
            className={`small${tab === key ? "" : " secondary"}`}
            onClick={() => setTab(key)}
            style={{ fontWeight: tab === key ? 700 : 400 }}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "channels" && <ChannelsTab />}
      {tab === "rules" && <RulesTab />}
      {tab === "history" && <HistoryTab />}
    </>
  );
}
