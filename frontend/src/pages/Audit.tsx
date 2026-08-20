import { audit } from "../services/backend";
import { useWebsiteStore } from "../stores/websiteStore";
import { Badge, Empty, ErrorBox, Loading } from "../components/common";
import { useAsync } from "../hooks/useAsync";

const VERDICTS = ["improve", "consolidate", "refresh", "review", "keep"] as const;

export default function Audit() {
  const { active } = useWebsiteStore();
  const result = useAsync(async () => (active ? audit.run(active.id) : null), [active?.id]);

  if (!active) return <Empty text="Add a website first." />;
  if (result.loading) return <Loading />;
  if (result.error) return <ErrorBox message={result.error} />;
  if (!result.data || result.data.items.length === 0) {
    return <Empty text="No crawled pages to audit. Crawl the website first." />;
  }

  return (
    <>
      <h2 className="page-title">Content Audit</h2>
      <p className="page-sub">Verdicts are computed live from data — never stored as fact.</p>

      <div className="kpi-grid">
        {VERDICTS.map((v) => (
          <div className="kpi" key={v}>
            <div className="label"><Badge value={v} /></div>
            <div className="value">{result.data!.summary[v] ?? 0}</div>
          </div>
        ))}
      </div>

      <table className="data">
        <thead><tr><th>Verdict</th><th>Page</th><th>Reason</th><th>Clicks</th><th>Impressions</th></tr></thead>
        <tbody>
          {result.data.items.map((row) => (
            <tr key={row.page_id}>
              <td><Badge value={row.verdict} /></td>
              <td>
                <div>{row.title ?? row.url}</div>
                <div className="mono muted">{row.url}</div>
              </td>
              <td className="muted">{row.reason}</td>
              <td>{row.clicks.toLocaleString()}</td>
              <td>{row.impressions.toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
