/** Typed endpoint helpers — one per backend prefix. Pages never call fetch directly. */
import { api } from "./api";
import type {
  AiProvider, ArticleDraft, ArticlePlan, AuditRow, ContentIdea, Discussion, DraftSummary,
  Finding, Keyword, Opportunity, Page, Paged, PublishConfig, PublishLog, PublishResult,
  ReferenceDoc, ResearchSource, SeoRule, Website,
} from "../types";

export const health = () => api.get<{ status: string; database: string; version: string }>("/health/");

export const websites = {
  list: () => api.get<Paged<Website>>("/websites/"),
  create: (name: string, url: string) => api.post<Website>("/websites/", { name, url }),
  remove: (id: number) => api.delete(`/websites/${id}`),
  crawl: (id: number) => api.post<{ job_id: number }>(`/websites/${id}/crawl/start`),
  crawlStatus: (jobId: number) => api.get<{ status: string; records_imported: number }>(`/websites/crawl/${jobId}/status`),
};

export const pages = {
  list: (websiteId: number, page = 1) =>
    api.get<Paged<Page>>(`/pages/?website_id=${websiteId}&page=${page}&page_size=50`),
};

export const searchConsole = {
  oauthUrl: () => api.get<{ url: string | null; auth_url: string | null; configured: boolean }>("/search-console/oauth/url"),
  oauthStatus: () => api.get<{ configured: boolean; connected: boolean; redirect_uri: string }>("/search-console/oauth/status"),
  oauthConfig: () => api.get<{ client_id: string; client_secret: string; redirect_uri: string }>("/search-console/oauth/config"),
  saveOauthConfig: (client_id: string, client_secret: string) =>
    api.put<{ saved: boolean }>("/search-console/oauth/config", { client_id, client_secret }),
  properties: () => api.get<{ items: unknown[] }>("/search-console/properties"),
  discover: () => api.get<{ items: unknown[] }>("/search-console/properties/discover"),
  connect: (propertyId: number, websiteId: number) =>
    api.post(`/search-console/properties/${propertyId}/connect?website_id=${websiteId}`),
  sync: (propertyId: number) => api.post(`/search-console/sync?property_id=${propertyId}`),
  stats: (websiteId: number) => api.get<Record<string, unknown>>(`/search-console/stats?website_id=${websiteId}`),
  queries: (websiteId: number) => api.get<{ items: unknown[] }>(`/search-console/queries?website_id=${websiteId}`),
};

export const findings = {
  list: (websiteId: number, status = "open") =>
    api.get<Paged<Finding>>(`/findings/?website_id=${websiteId}&status=${status}&page_size=100`),
  analyze: (websiteId: number) => api.post<{ pages_analyzed: number; findings_saved: number }>(`/seo/analysis/run?website_id=${websiteId}`),
  setStatus: (id: number, status: string) => api.patch<Finding>(`/findings/${id}/status`, { status }),
};

export const opportunities = {
  list: (websiteId: number) => api.get<{ items: Opportunity[] }>(`/opportunities/?website_id=${websiteId}`),
};

export const audit = {
  run: (websiteId: number) =>
    api.get<{ items: AuditRow[]; summary: Record<string, number> }>(`/content-audit/?website_id=${websiteId}`),
};

export const research = {
  list: () => api.get<Paged<ResearchSource>>("/research/sources?page_size=100"),
  add: (sourceType: string, url: string, websiteId?: number) =>
    api.post<ResearchSource>("/research/sources", { source_type: sourceType, url, website_id: websiteId ?? null }),
  fromFile: (filename: string, content: string, websiteId?: number) =>
    api.post<ResearchSource>("/research/sources/from-file", { filename, content, website_id: websiteId ?? null }),
  remove: (id: number) => api.delete(`/research/sources/${id}`),
};

export const ideas = {
  list: () => api.get<Paged<ContentIdea>>("/content-ideas/?page_size=100"),
  generate: (websiteId: number) => api.post<{ items: ContentIdea[] }>(`/content-ideas/generate?website_id=${websiteId}`),
  create: (title: string, description?: string, websiteId?: number) =>
    api.post<ContentIdea>("/content-ideas/", { title, description: description ?? null, website_id: websiteId ?? null }),
  validate: (id: number) => api.post(`/content-ideas/${id}/validate`),
  setStatus: (id: number, status: string) => api.patch<ContentIdea>(`/content-ideas/${id}/status`, { status }),
};

export const keywords = {
  list: (websiteId: number) => api.get<Paged<Keyword>>(`/keywords/?website_id=${websiteId}&page_size=200`),
  importFromSc: (websiteId: number) => api.post<{ added: number }>(`/keywords/import-from-search-console?website_id=${websiteId}`),
  create: (websiteId: number, keyword: string) => api.post<Keyword>("/keywords/", { website_id: websiteId, keyword }),
  remove: (id: number) => api.delete(`/keywords/${id}`),
};

export const plans = {
  list: () => api.get<Paged<ArticlePlan>>("/article-plans/?page_size=100"),
  fromIdea: (ideaId: number) => api.post<ArticlePlan>("/article-plans/from-idea", { idea_id: ideaId }),
  create: (title: string, websiteId?: number) =>
    api.post<ArticlePlan>("/article-plans/", { title, website_id: websiteId ?? null }),
  generateDraft: (planId: number) => api.post(`/content/drafts/generate`, { plan_id: planId }),
};

export const references = {
  list: () => api.get<{ items: ReferenceDoc[] }>("/references/"),
  rules: () => api.get<{ items: SeoRule[] }>("/references/rules"),
};

export const reports = {
  weekly: (websiteId: number) => api.get<Record<string, unknown>>(`/reports/weekly?website_id=${websiteId}`),
  analyticsOverview: (websiteId: number, days = 30) =>
    api.get<Record<string, unknown>>(`/reports/analytics/overview?website_id=${websiteId}&days=${days}`),
  trafficTrend: (websiteId: number, days = 30) =>
    api.get<{ date: string; clicks: number; impressions: number; ctr: number }[]>(`/reports/analytics/traffic-trend?website_id=${websiteId}&days=${days}`),
  rankingDistribution: (websiteId: number, days = 30) =>
    api.get<{ top_3: number; pos_4_10: number; pos_11_20: number; pos_21_plus: number }>(`/reports/analytics/ranking-distribution?website_id=${websiteId}&days=${days}`),
  topPages: (websiteId: number, days = 30, limit = 20) =>
    api.get<{ page_url: string; clicks: number; impressions: number; ctr: number; position: number }[]>(`/reports/analytics/top-pages?website_id=${websiteId}&days=${days}&limit=${limit}`),
  topQueries: (websiteId: number, days = 30, limit = 20) =>
    api.get<{ query: string; clicks: number; impressions: number; ctr: number; position: number }[]>(`/reports/analytics/top-queries?website_id=${websiteId}&days=${days}&limit=${limit}`),
};

export interface GaProperty {
  property_id: string;
  property_name: string;
  account_name: string;
}

export interface GaConnection {
  id: number;
  website_id: number;
  property_id: string;
  property_name: string | null;
  status: string;
}

export interface GaSummary {
  connected: boolean;
  has_data: boolean;
  property_id: string;
  property_name?: string | null;
  current?: { sessions: number; active_users: number; pageviews: number; days: number };
  previous?: { sessions: number; active_users: number; pageviews: number; days: number };
  deltas?: { sessions: number; active_users: number; pageviews: number };
  window?: { current: { start: string; end: string }; previous: { start: string; end: string } };
}

export const googleAnalytics = {
  properties: () => api.get<{ items: GaProperty[] }>("/google-analytics/properties"),
  connection: (websiteId: number) =>
    api.get<{ connection: GaConnection | null }>(`/google-analytics/connection?website_id=${websiteId}`),
  connect: (websiteId: number, propertyId: string, propertyName?: string) =>
    api.post<GaConnection>("/google-analytics/connect", { website_id: websiteId, property_id: propertyId, property_name: propertyName ?? null }),
  disconnect: (websiteId: number) => api.delete(`/google-analytics/connection?website_id=${websiteId}`),
  sync: (websiteId: number) => api.post<{ imported: number }>(`/google-analytics/sync?website_id=${websiteId}`),
  summary: (websiteId: number) => api.get<GaSummary>(`/google-analytics/summary?website_id=${websiteId}`),
};

export const settings = {
  providers: () => api.get<{ items: AiProvider[] }>("/settings/ai-providers"),
  saveProvider: (provider: string, apiKey: string | null, enabled: boolean, isDefault: boolean, model?: string) =>
    api.put<AiProvider>(`/settings/ai-providers/${provider}`, { provider, api_key: apiKey, enabled, is_default: isDefault, model: model ?? null }),
};

export const discussions = {
  list: () => api.get<Paged<Discussion>>("/discussions/?page_size=100"),
  create: (topic: string, ideaId?: number) => api.post<Discussion>("/discussions/", { topic, idea_id: ideaId ?? null }),
};

export const drafts = {
  list: (status?: string) =>
    api.get<{ items: DraftSummary[]; total: number }>(`/content/drafts${status ? `?status=${status}` : ""}`),
  get: (id: number) => api.get<ArticleDraft>(`/content/drafts/${id}`),
  edit: (id: number, content: string) => api.put<ArticleDraft>(`/content/drafts/${id}`, { content }),
  approve: (id: number) => api.post<ArticleDraft>(`/content/drafts/${id}/approve`),
};

export const publishing = {
  config: (target: string) => api.get<PublishConfig>(`/publishing/config/${target}`),
  saveConfig: (target: string, fields: Record<string, string>) =>
    api.put<PublishConfig>(`/publishing/config/${target}`, fields),
  testWordpress: () => api.post<{ connected: boolean }>("/publishing/wordpress/test"),
  wordpress: (draftId: number, status: "draft" | "publish") =>
    api.post<PublishResult>("/publishing/wordpress", { draft_id: draftId, status }),
  github: (draftId: number, path?: string) =>
    api.post<PublishResult>("/publishing/github", { draft_id: draftId, path: path ?? null }),
  logs: () => api.get<{ items: PublishLog[]; total: number }>("/publishing/logs"),
};

export interface DiagnosticsInfo {
  app: string;
  version: string;
  python: string;
  os: string;
  online: boolean;
  proxy_configured: boolean;
  sentry_enabled: boolean;
  data_dir: string;
  log_file: string;
  log_size_bytes: number;
}

export const diagnostics = {
  track: (event: string, detail?: string) =>
    api.post<{ ok: boolean }>("/diagnostics/events", { event, detail: detail ?? null }),
  events: (limit = 100) =>
    api.get<{ items: unknown[]; counts: { total: number; crashes: number } }>(`/diagnostics/events?limit=${limit}`),
  crash: (message: string, stack?: string, route?: string) =>
    api.post<{ ok: boolean }>("/diagnostics/crash", { message, stack: stack ?? null, route: route ?? null }),
  info: () => api.get<DiagnosticsInfo>("/diagnostics/info"),
};

// --- Monitoring & Alerts --------------------------------------------------

import type {
  AlertChannel,
  AlertHistoryEntry,
  AlertStats,
  MonitoringRule,
} from "../types";

export const monitoring = {
  // Channels
  channels: () => api.get<AlertChannel[]>("/monitoring/channels"),
  createChannel: (name: string, channelType: string, config: Record<string, unknown>) =>
    api.post<AlertChannel>("/monitoring/channels", { name, channel_type: channelType, config }),
  updateChannel: (id: number, fields: Partial<Pick<AlertChannel, "name" | "enabled" | "config">>) =>
    api.patch<AlertChannel>(`/monitoring/channels/${id}`, fields),
  deleteChannel: (id: number) => api.delete(`/monitoring/channels/${id}`),
  testChannel: (id: number) =>
    api.post<{ success: boolean; error: string | null }>("/monitoring/channels/test", { channel_id: id }),

  // Rules
  rules: (websiteId?: number) =>
    api.get<MonitoringRule[]>(`/monitoring/rules${websiteId ? `?website_id=${websiteId}` : ""}`),
  createRule: (data: {
    website_id: number;
    name: string;
    rule_type: string;
    config?: Record<string, unknown>;
    channel_ids?: number[];
    check_interval?: string;
  }) => api.post<MonitoringRule>("/monitoring/rules", data),
  updateRule: (id: number, fields: Partial<MonitoringRule>) =>
    api.patch<MonitoringRule>(`/monitoring/rules/${id}`, fields),
  deleteRule: (id: number) => api.delete(`/monitoring/rules/${id}`),
  runCheck: (ruleId: number) =>
    api.post<{ rule_id: number; alerts_triggered: number; notifications_sent: number }>("/monitoring/check", { rule_id: ruleId }),
  runAllChecks: () =>
    api.post<{ rules_checked: number; total_alerts: number }>("/monitoring/check/all"),

  // History
  history: (ruleId?: number, limit = 50) =>
    api.get<AlertHistoryEntry[]>(`/monitoring/history${ruleId ? `?rule_id=${ruleId}` : ""}&limit=${limit}`),
  stats: () => api.get<AlertStats>("/monitoring/stats"),
};

// --- A/B Testing ----------------------------------------------------------

import type { ABTestDetail } from "../types";

export const abTests = {
  list: (websiteId?: number) =>
    api.get<ABTestDetail[]>(`/ab-tests${websiteId ? `?website_id=${websiteId}` : ""}`),
  get: (id: number) => api.get<ABTestDetail>(`/ab-tests/${id}`),
  create: (data: {
    website_id: number;
    page_id: number;
    name: string;
    element?: string;
    control_title?: string | null;
    control_description?: string | null;
    variant_title?: string | null;
    variant_description?: string | null;
    min_duration_days?: number;
  }) => api.post<ABTestDetail>("/ab-tests", data),
  start: (id: number) => api.post<ABTestDetail>(`/ab-tests/${id}/start`),
  collect: (id: number) =>
    api.post<{ snapshots_upserted: number; days_fetched: number }>(`/ab-tests/${id}/collect`),
  evaluate: (id: number) => api.post<ABTestDetail>(`/ab-tests/${id}/evaluate`),
  cancel: (id: number) => api.post<ABTestDetail>(`/ab-tests/${id}/cancel`),
  delete: (id: number) => api.delete(`/ab-tests/${id}`),
};

// --- Competitor Analysis ---------------------------------------------------

import type { Competitor, CompetitorRanking, CompetitorSummary, ContentGap, GapStats } from "../types";

export const competitors = {
  list: (websiteId: number) => api.get<Competitor[]>(`/competitors?website_id=${websiteId}`),
  create: (websiteId: number, name: string, url: string, notes?: string) =>
    api.post<Competitor>("/competitors", { website_id: websiteId, name, url, notes: notes ?? null }),
  get: (id: number) => api.get<CompetitorSummary>(`/competitors/${id}`),
  update: (id: number, fields: Partial<Pick<Competitor, "name" | "notes">>) =>
    api.patch<Competitor>(`/competitors/${id}`, fields),
  delete: (id: number) => api.delete(`/competitors/${id}`),

  // Rankings
  importRankings: (competitorId: number, rankings: { keyword: string; position: number; url?: string; impressions?: number; source?: string }[], snapshotDate: string) =>
    api.post<{ imported: number }>(`/competitors/${competitorId}/rankings`, { competitor_id: competitorId, rankings, snapshot_date: snapshotDate }),
  rankings: (competitorId: number, limit = 200) =>
    api.get<CompetitorRanking[]>(`/competitors/${competitorId}/rankings?limit=${limit}`),

  // Gaps
  analyzeGaps: (competitorId: number, websiteId: number) =>
    api.post<{ gaps_found: number; new_content: number; improve_existing: number; quick_win: number }>(
      `/competitors/${competitorId}/gaps?website_id=${websiteId}`
    ),
  gaps: (websiteId: number, status?: string) =>
    api.get<ContentGap[]>(`/competitors/gaps/all?website_id=${websiteId}${status ? `&status=${status}` : ""}`),
  gapStats: (websiteId: number) => api.get<GapStats>(`/competitors/gaps/stats?website_id=${websiteId}`),
  updateGapStatus: (gapId: number, status: string) =>
    api.patch<ContentGap>(`/competitors/gaps/${gapId}/status?status=${status}`),
  deleteGap: (gapId: number) => api.delete(`/competitors/gaps/${gapId}`),
};

// --- Keyword Clustering ---------------------------------------------------

import type { ClusterOut, ClusterDetail } from "../types";

export const keywordClusters = {
  list: (websiteId: number) => api.get<ClusterOut[]>(`/keyword-clusters?website_id=${websiteId}`),
  get: (id: number) => api.get<ClusterDetail>(`/keyword-clusters/${id}`),
  create: (websiteId: number, name: string, description?: string, pillarKeyword?: string) =>
    api.post<ClusterOut>("/keyword-clusters", { website_id: websiteId, name, description: description ?? null, pillar_keyword: pillarKeyword ?? null }),
  update: (id: number, fields: Partial<Pick<ClusterOut, "name" | "description" | "pillar_keyword">>) =>
    api.patch<ClusterOut>(`/keyword-clusters/${id}`, fields),
  delete: (id: number) => api.delete(`/keyword-clusters/${id}`),
  addKeywords: (clusterId: number, keywords: { keyword: string; search_volume?: number; position?: number }[]) =>
    api.post<{ added: number }>(`/keyword-clusters/${clusterId}/keywords`, keywords),
  removeKeyword: (itemId: number) => api.delete(`/keyword-clusters/keywords/${itemId}`),
  autoCluster: (websiteId: number, minPerCluster = 2, threshold = 0.3) =>
    api.post<{ clusters_created: number; keywords_processed: number; keywords_clustered: number }>("/keyword-clusters/auto", { website_id: websiteId, min_keywords_per_cluster: minPerCluster, similarity_threshold: threshold }),
};

// --- Schema Markup Builder -------------------------------------------------

import type { SchemaOut } from "../types";

export const schemas = {
  types: () => api.get<{ types: string[] }>("/schemas/types"),
  generate: (schemaType: string, params: Record<string, unknown>, pageId?: number) =>
    api.post<{ generated: Record<string, unknown>; source: string }>("/schemas/generate", { schema_type: schemaType, page_id: pageId ?? null, params }),
  validate: (jsonLd: string) =>
    api.post<{ valid: boolean; errors: string[]; schema_type: string; parsed: Record<string, unknown> }>("/schemas/validate", { json_ld: jsonLd }),
  save: (pageId: number, schemaType: string, jsonLd: string) =>
    api.post<SchemaOut>("/schemas/save", { page_id: pageId, schema_type: schemaType, json_ld: jsonLd }),
  listForPage: (pageId: number) => api.get<SchemaOut[]>(`/schemas/page/${pageId}`),
  get: (id: number) => api.get<SchemaOut>(`/schemas/${id}`),
  delete: (id: number) => api.delete(`/schemas/${id}`),
  coverage: (websiteId: number) =>
    api.get<{ total_pages: number; pages_with_schema: number; pages_without_schema: number; coverage_pct: number }>(`/schemas/coverage/summary?website_id=${websiteId}`),
};

// --- Content Calendar ------------------------------------------------------

import type { CalendarEvent } from "../types";

export const calendar = {
  list: (websiteId: number, startDate?: string, endDate?: string, status?: string) =>
    api.get<CalendarEvent[]>(`/calendar?website_id=${websiteId}${startDate ? `&start_date=${startDate}` : ""}${endDate ? `&end_date=${endDate}` : ""}${status ? `&status=${status}` : ""}`),
  create: (data: {
    website_id: number;
    title: string;
    description?: string;
    event_type?: string;
    start_date: string;
    end_date?: string;
    priority?: string;
    assignee?: string;
    notes?: string;
  }) => api.post<CalendarEvent>("/calendar", data),
  get: (id: number) => api.get<CalendarEvent>(`/calendar/${id}`),
  update: (id: number, fields: Partial<CalendarEvent>) =>
    api.patch<CalendarEvent>(`/calendar/${id}`, fields),
  delete: (id: number) => api.delete(`/calendar/${id}`),
  pipeline: (websiteId: number) =>
    api.get<Record<string, number>>(`/calendar/pipeline?website_id=${websiteId}`),
  deadlines: (websiteId: number, days = 14) =>
    api.get<CalendarEvent[]>(`/calendar/deadlines?website_id=${websiteId}&days=${days}`),
};

// --- Backlink Monitor ------------------------------------------------------

import type { BacklinkOut, BacklinkChangeOut, BacklinkProfile } from "../types";

export const backlinks = {
  list: (websiteId: number, status?: string, domain?: string) =>
    api.get<BacklinkOut[]>(`/backlinks?website_id=${websiteId}${status ? `&status=${status}` : ""}${domain ? `&domain=${domain}` : ""}`),
  add: (data: { website_id: number; source_url: string; target_url: string; anchor_text?: string; is_nofollow?: boolean; domain_authority?: number }) =>
    api.post<BacklinkOut>("/backlinks", data),
  import: (websiteId: number, backlinks: { source_url: string; target_url: string; anchor_text?: string; domain_authority?: number }[]) =>
    api.post<{ imported: number }>("/backlinks/import", { website_id: websiteId, backlinks }),
  get: (id: number) => api.get<BacklinkOut>(`/backlinks/${id}`),
  update: (id: number, fields: Partial<BacklinkOut>) =>
    api.patch<BacklinkOut>(`/backlinks/${id}`, fields),
  delete: (id: number) => api.delete(`/backlinks/${id}`),
  profile: (websiteId: number) => api.get<BacklinkProfile>(`/backlinks/profile?website_id=${websiteId}`),
  changes: (websiteId: number, limit = 50) =>
    api.get<BacklinkChangeOut[]>(`/backlinks/changes?website_id=${websiteId}&limit=${limit}`),
};

// --- Page Speed Insights ---------------------------------------------------

import type { PageSpeedSnapshotOut } from "../types";

export const pageSpeed = {
  check: (data: {
    website_id: number; page_id: number; url: string;
    lcp?: number; fid?: number; cls?: number; fcp?: number; ttfb?: number; tti?: number;
    performance_score?: number; accessibility_score?: number; best_practices_score?: number; seo_score?: number;
    opportunities?: Record<string, unknown>[]; diagnostics?: Record<string, unknown>[];
  }) => api.post<PageSpeedSnapshotOut>("/page-speed/check", data),
  latest: (pageId: number) => api.get<PageSpeedSnapshotOut>(`/page-speed/latest/${pageId}`),
  history: (pageId: number, limit = 30) =>
    api.get<PageSpeedSnapshotOut[]>(`/page-speed/history/${pageId}?limit=${limit}`),
  summary: (websiteId: number) =>
    api.get<Record<string, number>>(`/page-speed/summary?website_id=${websiteId}`),
  pageScores: (websiteId: number, limit = 50) =>
    api.get<PageSpeedSnapshotOut[]>(`/page-speed/pagescores?website_id=${websiteId}&limit=${limit}`),
};

// --- Content Rewriter ------------------------------------------------------

import type { RewriteOut } from "../types";

export const rewriter = {
  rewrite: (data: {
    website_id?: number; page_id?: number; content_type: string;
    original_text: string; context?: string; num_variations?: number; provider?: string;
  }) => api.post<{ id: number; original: string; rewrites: string[]; provider: string; model: string | null }>("/rewriter/rewrite", data),
  history: (websiteId?: number, limit = 50) =>
    api.get<RewriteOut[]>(`/rewriter/history${websiteId ? `?website_id=${websiteId}` : ""}${websiteId ? "&" : "?"}limit=${limit}`),
  get: (id: number) => api.get<RewriteOut>(`/rewriter/${id}`),
  select: (id: number, selectedIndex: number) =>
    api.post<RewriteOut>(`/rewriter/${id}/select`, { selected_index: selectedIndex }),
  apply: (id: number) => api.post<RewriteOut>(`/rewriter/${id}/apply`),
};

// --- SEO Checklist ---------------------------------------------------------

import type { ChecklistOut, ChecklistDetail, ChecklistItemOut } from "../types";

export const seoChecklist = {
  create: (websiteId: number, pageId: number) =>
    api.post<ChecklistOut>("/seo-checklist", { website_id: websiteId, page_id: pageId }),
  list: (websiteId: number) => api.get<ChecklistOut[]>(`/seo-checklist?website_id=${websiteId}`),
  get: (id: number) => api.get<ChecklistDetail>(`/seo-checklist/${id}`),
  autoGenerate: (id: number) =>
    api.post<{ items_added: number; total_findings: number }>(`/seo-checklist/${id}/auto-generate`),
  addItem: (checklistId: number, category: string, itemText: string, notes?: string) =>
    api.post<ChecklistItemOut>(`/seo-checklist/${checklistId}/items`, { category, item_text: itemText, notes: notes ?? null }),
  updateItem: (itemId: number, fields: { status?: string; notes?: string }) =>
    api.patch<ChecklistItemOut>(`/seo-checklist/items/${itemId}`, fields),
  deleteItem: (itemId: number) => api.delete(`/seo-checklist/items/${itemId}`),
  complete: (id: number) => api.post<ChecklistOut>(`/seo-checklist/${id}/complete`),
  delete: (id: number) => api.delete(`/seo-checklist/${id}`),
};

// --- Report Generator ------------------------------------------------------

import type { ReportSummary, ReportResponse, ReportSection } from "../types";

export const reportGenerator = {
  create: (data: {
    website_id: number; title: string; report_type?: string;
    format?: string; period_days?: number;
  }) => api.post<ReportResponse>("/reports/generate", data),
  list: (websiteId: number) => api.get<ReportSummary[]>(`/reports/generate?website_id=${websiteId}`),
  get: (id: number) => api.get<ReportResponse>(`/reports/generate/${id}`),
  getSections: (id: number) => api.get<ReportSection[]>(`/reports/generate/${id}/sections`),
  getHtml: (id: number) => `/api/reports/generate/${id}/html`,
  delete: (id: number) => api.delete(`/reports/generate/${id}`),
};

// --- Redirect Manager -------------------------------------------------------

import type { RedirectOut, RedirectStats } from "../types";

export const redirects = {
  list: (websiteId: number, status?: string, limit = 200) =>
    api.get<RedirectOut[]>(`/redirects?website_id=${websiteId}${status ? `&status=${status}` : ""}&limit=${limit}`),
  create: (data: {
    website_id: number; source_url: string; target_url: string;
    status_code?: number; notes?: string;
  }) => api.post<RedirectOut>("/redirects", data),
  get: (id: number) => api.get<RedirectOut>(`/redirects/${id}`),
  update: (id: number, fields: Partial<RedirectOut>) =>
    api.patch<RedirectOut>(`/redirects/${id}`, fields),
  delete: (id: number) => api.delete(`/redirects/${id}`),
  bulkImport: (websiteId: number, redirects: { source: string; target: string; status_code?: number }[], overwrite = false) =>
    api.post<{ imported: number; total_submitted: number }>("/redirects/bulk", { website_id: websiteId, redirects, overwrite }),
  stats: (websiteId: number) => api.get<RedirectStats>(`/redirects/stats?website_id=${websiteId}`),
  chains: (websiteId: number) =>
    api.get<{ id: number; source_url: string; target_url: string; status_code: number; chain_id: number; final_url: string }[]>(`/redirects/chains?website_id=${websiteId}`),
  recordCheck: (id: number, data: { status_code?: number; response_time_ms?: number; final_url?: string; error_message?: string }) =>
    api.post(`/redirects/${id}/check`, data),
  checkHistory: (id: number, limit = 20) =>
    api.get(`/redirects/${id}/history?limit=${limit}`),
  resolveChain: (id: number) => api.post<RedirectOut>(`/redirects/${id}/resolve-chain`),
};

// --- Rank Tracker ----------------------------------------------------------

import type { TrackedKeywordOut, RankSnapshotOut, RankTrackerStats, RankAlertOut, KeywordTrendOut } from "../types";

export const rankTracker = {
  createKeyword: (data: {
    website_id: number; keyword: string;
    target_url?: string; group_name?: string; notes?: string;
  }) => api.post<TrackedKeywordOut>("/rank-tracker/keywords", data),
  listKeywords: (websiteId: number, limit = 200) =>
    api.get<TrackedKeywordOut[]>(`/rank-tracker/keywords?website_id=${websiteId}&limit=${limit}`),
  getKeyword: (id: number) => api.get<TrackedKeywordOut>(`/rank-tracker/keywords/${id}`),
  updateKeyword: (id: number, fields: Partial<TrackedKeywordOut>) =>
    api.patch<TrackedKeywordOut>(`/rank-tracker/keywords/${id}`, fields),
  deleteKeyword: (id: number) => api.delete(`/rank-tracker/keywords/${id}`),
  addSnapshot: (data: {
    keyword_id: number; position?: number; search_volume?: number;
    clicks?: number; impressions?: number; ctr?: number; url?: string;
    snapshot_date: string; search_engine?: string; country?: string; device?: string;
  }) => api.post<RankSnapshotOut>("/rank-tracker/snapshots", data),
  getSnapshots: (keywordId: number, limit = 90) =>
    api.get<RankSnapshotOut[]>(`/rank-tracker/keywords/${keywordId}/snapshots?limit=${limit}`),
  getKeywordTrend: (keywordId: number, days = 30) =>
    api.get<{ snapshot_date: string; position: number | null; clicks: number | null }[]>(`/rank-tracker/keywords/${keywordId}/trend?days=${days}`),
  getStats: (websiteId: number) => api.get<RankTrackerStats>(`/rank-tracker/stats?website_id=${websiteId}`),
  getTrends: (websiteId: number, days = 30) =>
    api.get<KeywordTrendOut[]>(`/rank-tracker/trends?website_id=${websiteId}&days=${days}`),
  getAlerts: (websiteId: number, unreadOnly = false) =>
    api.get<RankAlertOut[]>(`/rank-tracker/alerts?website_id=${websiteId}${unreadOnly ? "&unread_only=true" : ""}`),
  markAlertRead: (alertId: number) => api.post(`/rank-tracker/alerts/${alertId}/read`),
};

// --- SERP A/B Testing -------------------------------------------------------

import type { SERPABTestOut, SERPABTestStats } from "../types";

export const serpABTests = {
  create: (data: {
    website_id: number; page_id: number; name: string;
    control_title: string; control_description: string;
    variant_title: string; variant_description: string;
    min_days?: number; confidence?: number;
  }) => api.post<SERPABTestOut>("/serp-ab-tests", data),
  list: (websiteId: number, status?: string) =>
    api.get<SERPABTestOut[]>(`/serp-ab-tests?website_id=${websiteId}${status ? `&status=${status}` : ""}`),
  get: (id: number) => api.get<SERPABTestOut>(`/serp-ab-tests/${id}`),
  update: (id: number, fields: Partial<SERPABTestOut>) =>
    api.patch<SERPABTestOut>(`/serp-ab-tests/${id}`, fields),
  delete: (id: number) => api.delete(`/serp-ab-tests/${id}`),
  start: (id: number) => api.post<SERPABTestOut>(`/serp-ab-tests/${id}/start`),
  pause: (id: number) => api.post<SERPABTestOut>(`/serp-ab-tests/${id}/pause`),
  resume: (id: number) => api.post<SERPABTestOut>(`/serp-ab-tests/${id}/resume`),
  addSnapshot: (id: number, data: {
    variant: string; snapshot_date: string;
    clicks: number; impressions: number; ctr: number; avg_position: number;
  }) => api.post(`/serp-ab-tests/${id}/snapshots`, data),
  getSnapshots: (id: number) => api.get(`/serp-ab-tests/${id}/snapshots`),
  evaluate: (id: number) => api.post(`/serp-ab-tests/${id}/evaluate`),
  getStats: (websiteId: number) => api.get<SERPABTestStats>(`/serp-ab-tests/stats?website_id=${websiteId}`),
};

// --- SERP Preview ----------------------------------------------------------

import type { SERPPreviewResult, SERPBulkScoreResult } from "../types";

export const serpPreview = {
  preview: (data: {
    title: string; description: string; url: string;
    site_name?: string; date?: string;
  }) => api.post<SERPPreviewResult>("/serp-preview/preview", data),
  previewPage: (pageId: number) =>
    api.get<SERPPreviewResult>(`/serp-preview/page/${pageId}`),
  previewWebsite: (websiteId: number, limit = 50) =>
    api.get<SERPPreviewResult[]>(`/serp-preview/website/${websiteId}?limit=${limit}`),
  updateAndPreview: (pageId: number, title?: string, metaDescription?: string) =>
    api.put<SERPPreviewResult>(`/serp-preview/page/${pageId}${title ? `?title=${encodeURIComponent(title)}` : ""}${metaDescription ? `${title ? "&" : "?"}meta_description=${encodeURIComponent(metaDescription)}` : ""}`),
  bulkScore: (websiteId: number, limit = 200) =>
    api.get<SERPBulkScoreResult>(`/serp-preview/website/${websiteId}/bulk-score?limit=${limit}`),
};

// --- Sitemap Generator -----------------------------------------------------

import type { SitemapOverrideOut } from "../types";

export const sitemapGen = {
  settings: (websiteId: number) =>
    api.get<Record<string, unknown>>(`/sitemap-gen/settings?website_id=${websiteId}`),
  updateSettings: (websiteId: number, fields: Record<string, unknown>) =>
    api.put<Record<string, unknown>>(`/sitemap-gen/settings?website_id=${websiteId}`, fields),
  overrides: (websiteId: number) =>
    api.get<SitemapOverrideOut[]>(`/sitemap-gen/overrides?website_id=${websiteId}`),
  addOverride: (websiteId: number, urlPattern: string, priority?: number, changefreq?: string, include = true) =>
    api.post<SitemapOverrideOut>("/sitemap-gen/overrides", { website_id: websiteId, url_pattern: urlPattern, priority: priority ?? null, changefreq: changefreq ?? null, include }),
  deleteOverride: (id: number) => api.delete(`/sitemap-gen/overrides/${id}`),
  generate: (websiteId: number) =>
    api.get<string>(`/sitemap-gen/generate?website_id=${websiteId}`),
  preview: (websiteId: number) =>
    api.get<{ url_count: number; excluded_count: number; total_pages: number; xml_preview: string }>(`/sitemap-gen/preview?website_id=${websiteId}`),
};

// --- Content Brief Generator ------------------------------------------------

export const contentBriefs = {
  generate: (websiteId: number, targetKeyword: string) =>
    api.post<Record<string, unknown>>("/content-briefs", { website_id: websiteId, target_keyword: targetKeyword }),
  list: (websiteId: number) =>
    api.get<{ id: number; website_id: number; target_keyword: string; primary_keyword: string; search_intent: string | null; target_word_count: number | null; status: string; version: number; created_at: string; updated_at: string }[]>(`/content-briefs?website_id=${websiteId}`),
  get: (id: number) => api.get<Record<string, unknown>>(`/content-briefs/${id}`),
  update: (id: number, fields: Record<string, unknown>) =>
    api.put<Record<string, unknown>>(`/content-briefs/${id}`, fields),
  delete: (id: number) => api.delete(`/content-briefs/${id}`),
  sections: (id: number) => api.get<{ id: number; section_type: string; title: string; content: string }[]>(`/content-briefs/${id}/sections`),
  competitors: (id: number) => api.get<{ id: number; url: string; title: string | null; word_count: number | null; headings: string | null; keyword_density: number | null; media_count: number; has_faq: number; has_schema: number }[]>(`/content-briefs/${id}/competitors`),
  exportMarkdown: (id: number) => `/api/content-briefs/${id}/export`,
  finalize: (id: number) => api.post<Record<string, unknown>>(`/content-briefs/${id}/finalize`),
  sendToPlanner: (id: number) => api.post<Record<string, unknown>>(`/content-briefs/${id}/send-to-planner`),
};

// --- Content Refresh Scheduler ------------------------------------------------

export interface RefreshRule {
  id: number; website_id: number; name: string;
  min_age_days: number; traffic_drop_pct: number;
  staleness_weight: number; traffic_weight: number;
  enabled: number; created_at: string; updated_at: string;
}

export interface RefreshSchedule {
  id: number; website_id: number; page_id: number; rule_id: number | null;
  priority_score: number; priority_date: string | null; reason: string | null;
  suggested_changes: { type: string; priority: string; description: string; reason: string }[] | null;
  status: string; created_at: string; updated_at: string;
}

export interface RefreshHistory {
  id: number; schedule_id: number; page_id: number; action: string;
  changes_made: string | null; clicks_before: number | null; clicks_after: number | null;
  impressions_before: number | null; impressions_after: number | null;
  position_before: number | null; position_after: number | null;
  notes: string | null; created_at: string;
}

export interface RefreshStats {
  total_schedules: number; pending: number; in_progress: number;
  completed: number; skipped: number; avg_priority: number;
}

export const contentRefresh = {
  // Rules
  createRule: (data: { website_id: number; name: string; min_age_days?: number; traffic_drop_pct?: number; staleness_weight?: number; traffic_weight?: number }) =>
    api.post<RefreshRule>("/content-refresh/rules", data),
  listRules: (websiteId: number) => api.get<RefreshRule[]>(`/content-refresh/rules?website_id=${websiteId}`),
  updateRule: (id: number, fields: Partial<RefreshRule>) =>
    api.patch<RefreshRule>(`/content-refresh/rules/${id}`, fields),
  deleteRule: (id: number) => api.delete(`/content-refresh/rules/${id}`),

  // Scan
  scan: (websiteId: number, ruleId?: number) =>
    api.post<{ pages_scanned: number; stale_pages_found: number; schedules_created: number; recommendations: Record<string, unknown>[] }>(
      `/content-refresh/scan?website_id=${websiteId}${ruleId ? `&rule_id=${ruleId}` : ""}`
    ),

  // Schedules
  listSchedules: (websiteId: number, status?: string) =>
    api.get<RefreshSchedule[]>(`/content-refresh/schedule?website_id=${websiteId}${status ? `&status=${status}` : ""}`),
  getSchedule: (id: number) => api.get<RefreshSchedule>(`/content-refresh/schedule/${id}`),
  updateStatus: (id: number, status: string) =>
    api.patch<RefreshSchedule>(`/content-refresh/schedule/${id}/status?status=${status}`),
  skip: (id: number) => api.post<RefreshSchedule>(`/content-refresh/schedule/${id}/skip`),
  complete: (id: number) => api.post<RefreshSchedule>(`/content-refresh/schedule/${id}/complete`),
  deleteSchedule: (id: number) => api.delete(`/content-refresh/schedule/${id}`),

  // History & Stats
  history: (websiteId: number) => api.get<RefreshHistory[]>(`/content-refresh/history?website_id=${websiteId}`),
  stats: (websiteId: number) => api.get<RefreshStats>(`/content-refresh/stats?website_id=${websiteId}`),
};

// --- Search Console File Upload -----------------------------------------------

export const scUpload = {
  upload: (file: File, websiteId: number, importType = "performance") => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("website_id", String(websiteId));
    formData.append("import_type", importType);
    return api.post<{ import_id: number; rows_imported: number; rows_skipped: number; message: string }>(
      "/sc-upload/upload",
      formData as unknown as Record<string, unknown>,
    );
  },
  listImports: (websiteId: number) =>
    api.get<{ id: number; filename: string; status: string; rows_imported: number; created_at: string }[]>(
      `/sc-upload/imports?website_id=${websiteId}`,
    ),
  getImport: (id: number) => api.get<Record<string, unknown>>(`/sc-upload/imports/${id}`),
  stats: (websiteId: number) => api.get<{ total_imports: number; total_rows_imported: number; last_import: string | null }>(
    `/sc-upload/stats?website_id=${websiteId}`,
  ),
};
