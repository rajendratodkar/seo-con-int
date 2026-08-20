import { references as api } from "../services/backend";
import { ErrorBox, Loading } from "../components/common";
import { useAsync } from "../hooks/useAsync";

export default function References() {
  const docs = useAsync(() => api.list(), []);
  const rules = useAsync(() => api.rules(), []);

  if (docs.loading || rules.loading) return <Loading />;
  if (docs.error) return <ErrorBox message={docs.error} />;
  if (rules.error) return <ErrorBox message={rules.error} />;

  return (
    <>
      <h2 className="page-title">References &amp; SEO Rules</h2>
      <p className="page-sub">Official documents (Google, SEBI, AMFI, RBI…) and the rules derived from them.</p>

      <div className="card">
        <h3>Reference documents</h3>
        <table className="data">
          <thead><tr><th>Category</th><th>Title</th><th>URL</th></tr></thead>
          <tbody>
            {(docs.data?.items ?? []).map((doc) => (
              <tr key={doc.id}>
                <td><span className="badge blue">{doc.category}</span></td>
                <td>{doc.title}</td>
                <td>{doc.url ? <a className="plain" href={doc.url} target="_blank" rel="noreferrer">open ↗</a> : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>SEO rules</h3>
        <table className="data">
          <thead><tr><th>Code</th><th>Name</th><th>Category</th><th>Severity</th><th>Reference</th></tr></thead>
          <tbody>
            {(rules.data?.items ?? []).map((rule) => {
              const r = rule as typeof rule & { reference_title?: string; reference_url?: string };
              return (
                <tr key={rule.id}>
                  <td className="mono">{rule.rule_code}</td>
                  <td>{rule.name}</td>
                  <td>{rule.category}</td>
                  <td><span className={`badge ${rule.severity === "critical" ? "red" : rule.severity === "warning" ? "amber" : "blue"}`}>{rule.severity}</span></td>
                  <td>
                    {r.reference_url
                      ? <a className="plain" href={r.reference_url} target="_blank" rel="noreferrer">{r.reference_title ?? "doc"} ↗</a>
                      : <span className="muted">—</span>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}
