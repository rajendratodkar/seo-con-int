/** Small shared UI pieces. */

export function Loading() {
  return <div className="empty">Loading…</div>;
}

export function ErrorBox({ message }: { message: string }) {
  return <div className="error-box">{message}</div>;
}

export function Empty({ text }: { text: string }) {
  return <div className="empty">{text}</div>;
}

const TONES: Record<string, string> = {
  high: "green",
  medium: "amber",
  low: "gray",
  critical: "red",
  warning: "amber",
  info: "blue",
  data_based: "green",
  rule_based: "blue",
  ai_suggestion: "violet",
  full: "green",
  metadata_only: "amber",
  pending: "gray",
  completed: "green",
  processing: "blue",
  failed: "red",
  approved: "green",
  validated: "green",
  draft: "gray",
  rejected: "red",
  brief_ready: "blue",
  drafting: "amber",
  keep: "green",
  improve: "amber",
  refresh: "blue",
  consolidate: "violet",
  review: "gray",
};

export function Badge({ value }: { value: string }) {
  return <span className={`badge ${TONES[value] ?? "gray"}`}>{value.replace(/_/g, " ")}</span>;
}

/** Rule 5: AI output always gets an explicit badge. */
export function AiBadge() {
  return <span className="badge violet">AI suggestion</span>;
}
