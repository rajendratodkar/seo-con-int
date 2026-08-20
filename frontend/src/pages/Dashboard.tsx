import { useAsync } from "../hooks/useAsync";
import { health, reports } from "../services/backend";
import { useWebsiteStore } from "../stores/websiteStore";
import { Badge, Empty, ErrorBox, Loading } from "../components/common";

export default function Dashboard() {
  const { active, loading: websitesLoading, error: websitesError } = useWebsiteStore();
  const appHealth = useAsync(() => health(), []);
  const weekly = useAsync(
    async () => (active ? reports.weekly(active.id) : null),
    [active?.id],
  );

  if (appHealth.loading) return <Loading />;

  return (
    <>
      <h2 className="page-title">Dashboard</h2>
      <p className="page-sub">Backend {appHealth.data?.status} · database {appHealth.data?.database} · v{appHealth.data?.version}</p>

      {websitesError ? (
        <ErrorBox message={`Could not reach the backend: ${websitesError}. Make sure the backend is running, then reload.`} />
      ) : websitesLoading ? (
        <Loading />
      ) : !active ? (
        <Empty text="No website added yet. Go to Websites → Add website to get started." />
      ) : weekly.error ? (
        <ErrorBox message={weekly.error} />
      ) : weekly.loading || !weekly.data ? (
        <Loading />
      ) : (
        <>
          <div className="kpi-grid">
            <Kpi label="Clicks (7d)" value={traffic(weekly.data, "clicks")} delta="clicks_delta" data={weekly.data} />
            <Kpi label="Impressions (7d)" value={traffic(weekly.data, "impressions")} delta="impressions_delta" data={weekly.data} />
            <Kpi label="Opportunities" value={weekly.data.opportunities} />
          </div>

          <div className="card">
            <h3>Content audit verdicts</h3>
            <div className="row">
              {Object.entries((weekly.data.audit ?? {}) as Record<string, number>).map(([verdict, count]) => (
                <span key={verdict} className="row">
                  <Badge value={verdict} /> <strong>{count}</strong>
                </span>
              ))}
            </div>
          </div>

          <div className="card">
            <h3>Open findings</h3>
            {Array.isArray(weekly.data.findings) && (weekly.data.findings as Array<Record<string, unknown>>).length > 0 ? (
              <table className="data">
                <thead><tr><th>Severity</th><th>Type</th><th>Count</th></tr></thead>
                <tbody>
                  {(weekly.data.findings as Array<Record<string, unknown>>).map((f, i) => (
                    <tr key={i}>
                      <td><Badge value={String(f.severity)} /></td>
                      <td><Badge value={String(f.rec_type)} /></td>
                      <td>{String(f.n)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="muted">No open findings. Run an analysis from Opportunities.</p>
            )}
          </div>
        </>
      )}
    </>
  );
}

function traffic(data: Record<string, unknown>, key: string): number {
  return ((data.traffic as Record<string, number>)?.[key] ?? 0);
}

function Kpi({ label, value, delta, data }: { label: string; value: unknown; delta?: string; data?: Record<string, unknown> }) {
  const deltaValue = delta && data ? ((data.traffic as Record<string, number>)?.[delta] ?? 0) : undefined;
  return (
    <div className="kpi">
      <div className="label">{label}</div>
      <div className="value">
        {Number(value).toLocaleString()}
        {deltaValue !== undefined && (
          <span style={{ fontSize: 13, marginLeft: 8, color: deltaValue >= 0 ? "var(--green)" : "var(--red)" }}>
            {deltaValue >= 0 ? "▲" : "▼"} {Math.abs(deltaValue).toLocaleString()}
          </span>
        )}
      </div>
    </div>
  );
}
