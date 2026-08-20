/** Shared TS types mirroring backend schemas (snake_case, Rule: pages never invent shapes). */

export interface Website {
  id: number;
  name: string;
  url: string;
  platform: string;
  sitemap_url: string | null;
  status: string;
  created_at: string;
}

export interface Page {
  id: number;
  website_id: number;
  url: string;
  title: string | null;
  meta_description: string | null;
  status_code: number | null;
  crawl_status: string;
  last_crawled_at: string | null;
}

export interface Paged<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface Finding {
  id: number;
  website_id: number;
  page_id: number | null;
  recommendation: string;
  why: string;
  evidence: string;
  confidence: string;
  severity: string;
  rec_type: string; // data_based | rule_based | ai_suggestion
  status: string;
}

export interface ResearchSource {
  id: number;
  source_type: string;
  url: string | null;
  title: string | null;
  availability_status: string; // full | metadata_only | pending — always shown as badge
  extraction_status: string;
  error_message: string | null;
}

export interface ContentIdea {
  id: number;
  website_id: number | null;
  source_type: string | null;
  title: string;
  description: string | null;
  status: string;
  score: number | null;
}

export interface ArticlePlan {
  id: number;
  website_id: number | null;
  idea_id: number | null;
  title: string;
  search_intent: string | null;
  status: string;
  outline: string | null;
  questions: string | null;
}

export interface ReferenceDoc {
  id: number;
  category: string;
  title: string;
  url: string | null;
}

export interface SeoRule {
  id: number;
  rule_code: string;
  name: string;
  category: string;
  severity: string;
  enabled: number;
  reference_id: number | null;
}

export interface AuditRow {
  page_id: number;
  url: string;
  title: string | null;
  verdict: "keep" | "improve" | "refresh" | "consolidate" | "review";
  reason: string;
  clicks: number;
  impressions: number;
}

export interface Opportunity {
  page_url: string;
  recommendation: string;
  why: string;
  evidence: string;
  confidence: string;
}

export interface AiProvider {
  id: number;
  provider: string;
  display_name: string;
  model: string | null;
  is_default: boolean;
  enabled: boolean;
  has_api_key: boolean;
}

export interface Discussion {
  id: number;
  topic: string;
  status: string;
  created_at: string;
}

export interface Keyword {
  id: number;
  keyword: string;
  search_intent: string | null;
  group_name: string | null;
  source: string;
}

export interface DraftSummary {
  id: number;
  plan_id: number;
  version: number;
  status: string;
  ai_provider: string | null;
  plan_title: string;
  created_at: string;
}

export interface ArticleDraft extends DraftSummary {
  content: string;
  content_path: string | null;
  ai_model: string | null;
}

export interface PublishConfig {
  target: string;
  site_url?: string;
  user?: string;
  has_app_password?: boolean;
  repo?: string;
  branch?: string;
  path_template?: string;
  has_token?: boolean;
}

export interface PublishResult {
  target: string;
  action: string;
  log_id: number;
  remote_id: string | number | null;
  remote_url: string | null;
  note?: string;
  path?: string;
  branch?: string;
}

export interface PublishLog {
  id: number;
  draft_id: number;
  target: string;
  action: string;
  status: string;
  remote_id: string | null;
  remote_url: string | null;
  error: string | null;
  created_at: string;
}

// --- Monitoring & Alerts --------------------------------------------------

export interface AlertChannel {
  id: number;
  name: string;
  channel_type: string; // email | slack | desktop
  enabled: boolean;
  config: Record<string, unknown>;
  last_tested_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface MonitoringRule {
  id: number;
  website_id: number;
  name: string;
  rule_type: string; // ranking_drop | traffic_drop | ctr_drop | new_seo_issue | crawl_error
  enabled: boolean;
  config: Record<string, unknown>;
  channel_ids: number[];
  check_interval: string;
  last_checked_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AlertHistoryEntry {
  id: number;
  rule_id: number;
  channel_id: number;
  severity: string;
  title: string;
  message: string;
  data: Record<string, unknown> | null;
  status: string;
  error_message: string | null;
  sent_at: string;
}

export interface AlertStats {
  total: number;
  by_status: Record<string, number>;
  by_severity: Record<string, number>;
}

// --- A/B Testing ----------------------------------------------------------

export interface ABVariant {
  id: number;
  test_id: number;
  variant_type: string; // control | variant
  title: string | null;
  description: string | null;
}

export interface ABTest {
  id: number;
  website_id: number;
  page_id: number;
  name: string;
  element: string; // title | description | both
  status: string; // draft | running | completed | cancelled
  started_at: string | null;
  completed_at: string | null;
  min_duration_days: number;
  winner: string | null; // control | variant | inconclusive | insufficient_data
  confidence: number | null;
  result_summary: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface ABTestDetail extends ABTest {
  control: ABVariant | null;
  variant: ABVariant | null;
}

// --- Competitor Analysis ---------------------------------------------------

export interface Competitor {
  id: number;
  website_id: number;
  name: string;
  url: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface CompetitorRanking {
  id: number;
  competitor_id: number;
  keyword: string;
  normalized: string;
  position: number;
  url: string | null;
  impressions: number | null;
  source: string;
  snapshot_date: string;
}

export interface ContentGap {
  id: number;
  website_id: number;
  keyword: string;
  competitor_id: number;
  competitor_pos: number;
  competitor_url: string | null;
  our_position: number | null;
  opportunity: string; // new_content | improve_existing | quick_win
  search_volume: number | null;
  priority: number;
  status: string;
  created_at: string;
}

export interface CompetitorSummary {
  competitor: Competitor;
  keyword_count: number;
  avg_position: number | null;
  top_keywords: { keyword: string; position: number; url: string | null }[];
}

export interface GapStats {
  total: number;
  new_content: number;
  improve_existing: number;
  quick_win: number;
}

// --- Keyword Clustering ---------------------------------------------------

export interface ClusterOut {
  id: number;
  website_id: number;
  name: string;
  description: string | null;
  pillar_keyword: string | null;
  keyword_count: number;
  created_at: string;
  updated_at: string;
}

export interface ClusterDetail extends ClusterOut {
  keywords: {
    id: number;
    keyword: string;
    search_volume: number | null;
    position: number | null;
    source: string;
  }[];
}

// --- Schema Markup Builder -------------------------------------------------

export interface SchemaOut {
  id: number;
  page_id: number;
  schema_type: string;
  json_ld: string;
  validation_errors: string | null;
  created_at: string;
  updated_at: string;
}

// --- Content Calendar ------------------------------------------------------

export interface CalendarEvent {
  id: number;
  website_id: number;
  title: string;
  description: string | null;
  event_type: string; // article | review | publish | meeting | deadline
  status: string; // planned | in_progress | review | published | overdue | cancelled
  start_date: string;
  end_date: string | null;
  plan_id: number | null;
  draft_id: number | null;
  priority: string; // low | normal | high | urgent
  color: string | null;
  assignee: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

// --- Backlink Monitor ------------------------------------------------------

export interface BacklinkOut {
  id: number;
  website_id: number;
  source_url: string;
  source_domain: string;
  target_url: string;
  anchor_text: string | null;
  is_nofollow: boolean;
  is_sponsored: boolean;
  domain_authority: number | null;
  page_authority: number | null;
  status: string;
  first_seen: string;
  last_checked: string | null;
  created_at: string;
  updated_at: string;
}

export interface BacklinkChangeOut {
  id: number;
  website_id: number;
  backlink_id: number | null;
  change_type: string;
  source_url: string;
  target_url: string;
  details: Record<string, unknown> | null;
  detected_at: string;
}

export interface BacklinkProfile {
  total_links: number;
  active_links: number;
  lost_links: number;
  broken_links: number;
  unique_domains: number;
  nofollow_count: number;
  sponsored_count: number;
  avg_domain_authority: number | null;
  top_domains: { source_domain: string; links: number; max_da: number | null }[];
  recent_changes: BacklinkChangeOut[];
}

// --- Page Speed Insights ---------------------------------------------------

export interface PageSpeedSnapshotOut {
  id: number;
  website_id: number;
  page_id: number;
  url: string;
  lcp: number | null;
  fid: number | null;
  cls: number | null;
  fcp: number | null;
  ttfb: number | null;
  tti: number | null;
  performance_score: number | null;
  accessibility_score: number | null;
  best_practices_score: number | null;
  seo_score: number | null;
  opportunities: Record<string, unknown>[] | null;
  diagnostics: Record<string, unknown>[] | null;
  source: string;
  checked_at: string;
  created_at: string;
}

// --- Content Rewriter ------------------------------------------------------

export interface RewriteOut {
  id: number;
  website_id: number | null;
  page_id: number | null;
  content_type: string;
  original_text: string;
  context: string | null;
  provider: string | null;
  model: string | null;
  rewrites: string[];
  selected_index: number | null;
  applied: boolean;
  created_at: string;
}

// --- SEO Checklist ---------------------------------------------------------

export interface ChecklistOut {
  id: number;
  website_id: number;
  page_id: number;
  status: string;
  total_items: number;
  done_items: number;
  progress_pct: number;
  created_at: string;
  updated_at: string;
}

export interface ChecklistItemOut {
  id: number;
  checklist_id: number;
  category: string;
  item_text: string;
  status: string;
  finding_id: number | null;
  notes: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface ChecklistDetail extends ChecklistOut {
  items: ChecklistItemOut[];
  page_url: string | null;
  page_title: string | null;
}

// --- Report Generator ------------------------------------------------------

export interface ReportSummary {
  id: number;
  title: string;
  report_type: string;
  format: string;
  status: string;
  period_days: number;
  generated_at: string | null;
  created_at: string;
}

export interface ReportResponse extends ReportSummary {
  website_id: number;
  report_data: string | null;
  file_path: string | null;
  updated_at: string;
}

export interface ReportSection {
  id: number;
  report_id: number;
  section_type: string;
  title: string;
  content: string;
  sort_order: number;
  created_at: string;
}

// --- Redirect Manager -------------------------------------------------------

export interface RedirectOut {
  id: number;
  website_id: number;
  source_url: string;
  target_url: string;
  status_code: number;
  is_active: boolean;
  chain_depth: number;
  hit_count: number;
  last_checked_at: string | null;
  last_status_code: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface RedirectStats {
  total: number;
  active: number;
  inactive: number;
  by_status_code: Record<string, number>;
  chains_detected: number;
  broken_count: number;
  avg_response_time_ms: number | null;
}

// --- Rank Tracker ----------------------------------------------------------

export interface TrackedKeywordOut {
  id: number;
  website_id: number;
  keyword: string;
  target_url: string | null;
  group_name: string | null;
  notes: string | null;
  is_active: boolean;
  current_position: number | null;
  previous_position: number | null;
  position_change: number | null;
  best_position: number | null;
  worst_position: number | null;
  avg_position: number | null;
  created_at: string;
  updated_at: string;
}

export interface RankSnapshotOut {
  id: number;
  keyword_id: number;
  position: number | null;
  previous_position: number | null;
  change: number | null;
  search_volume: number | null;
  clicks: number | null;
  impressions: number | null;
  ctr: number | null;
  url: string | null;
  search_engine: string;
  country: string;
  device: string;
  snapshot_date: string;
  created_at: string;
}

export interface RankTrackerStats {
  total_keywords: number;
  active_keywords: number;
  avg_position: number | null;
  top_10_count: number;
  top_20_count: number;
  top_50_count: number;
  position_improved: number;
  position_dropped: number;
  position_unchanged: number;
  best_keyword: string | null;
  best_position: number | null;
}

export interface RankAlertOut {
  id: number;
  keyword_id: number;
  keyword: string;
  alert_type: string;
  old_position: number | null;
  new_position: number | null;
  change: number | null;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface KeywordTrendOut {
  keyword_id: number;
  keyword: string;
  current_position: number | null;
  trend: string; // improving, declining, stable
  data_points: { snapshot_date: string; position: number | null; clicks: number | null }[];
}

// --- SERP A/B Testing -------------------------------------------------------

export interface SERPABTestOut {
  id: number;
  website_id: number;
  page_id: number;
  name: string;
  status: string;
  control_title: string;
  control_description: string;
  control_clicks: number;
  control_impressions: number;
  control_ctr: number;
  control_avg_position: number;
  variant_title: string;
  variant_description: string;
  variant_clicks: number;
  variant_impressions: number;
  variant_ctr: number;
  variant_avg_position: number;
  winner: string | null;
  confidence: number | null;
  z_score: number | null;
  p_value: number | null;
  lift: number | null;
  min_duration_days: number;
  confidence_level: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface SERPABTestStats {
  total_tests: number;
  running: number;
  completed: number;
  control_wins: number;
  variant_wins: number;
  inconclusive: number;
  avg_lift: number | null;
}

// --- SERP Preview ----------------------------------------------------------

export interface SERPScorePage {
  page_id: number;
  url: string;
  title: string;
  title_length: number;
  description: string;
  description_length: number;
  score: number;
  title_score: number;
  description_score: number;
  url_score: number;
  top_issues: { type: string; text: string }[];
}

export interface SERPBulkScoreResult {
  website: string;
  total_pages: number;
  avg_score: number;
  distribution: {
    excellent: number;
    good: number;
    moderate: number;
    poor: number;
  };
  common_issues: { issue: string; count: number }[];
  pages: SERPScorePage[];
}

export interface SERPScoreTip {
  type: string; // success, info, warning, error
  text: string;
}

export interface SERPScoreBreakdown {
  title: { score: number; max: number };
  description: { score: number; max: number };
  url: { score: number; max: number };
}

export interface SERPPreviewResult {
  title: string;
  truncated_title: string;
  title_length: number;
  title_status: string; // good, warning, too_long
  description: string;
  truncated_description: string;
  description_length: number;
  description_status: string; // good, warning, too_long, too_short
  url: string;
  display_url: string;
  site_name: string | null;
  date: string | null;
  score: number;
  score_breakdown: SERPScoreBreakdown;
  tips: SERPScoreTip[];
}

// --- Sitemap Generator -----------------------------------------------------

export interface SitemapOverrideOut {
  id: number;
  website_id: number;
  url_pattern: string;
  priority: number | null;
  changefreq: string | null;
  include: boolean;
  created_at: string;
}
