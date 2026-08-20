import React, { Suspense, useCallback, useMemo, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "../layouts/AppShell";
import { WebsiteStoreContext } from "../stores/websiteStore";
import { useAsync } from "../hooks/useAsync";
import { websites } from "../services/backend";
import type { Website } from "../types";

/* ------------------------------------------------------------------ */
/*  Lazy-loaded page components (each becomes its own chunk)           */
/* ------------------------------------------------------------------ */

const Dashboard = React.lazy(() => import("../pages/Dashboard"));
const Websites = React.lazy(() => import("../pages/Websites"));
const SearchConsolePage = React.lazy(() => import("../pages/SearchConsole"));
const Content = React.lazy(() => import("../pages/Content"));
const Keywords = React.lazy(() => import("../pages/Keywords"));
const Opportunities = React.lazy(() => import("../pages/Opportunities"));
const Audit = React.lazy(() => import("../pages/Audit"));
const Ideas = React.lazy(() => import("../pages/Ideas"));
const Research = React.lazy(() => import("../pages/Research"));
const ArticlePlanner = React.lazy(() => import("../pages/ArticlePlanner"));
const Drafts = React.lazy(() => import("../pages/Drafts"));
const References = React.lazy(() => import("../pages/References"));
const Reports = React.lazy(() => import("../pages/Reports"));
const ABTesting = React.lazy(() => import("../pages/ABTesting"));
const Analytics = React.lazy(() => import("../pages/Analytics"));
const Backlinks = React.lazy(() => import("../pages/Backlinks"));
const Competitors = React.lazy(() => import("../pages/Competitors"));
const ContentCalendar = React.lazy(() => import("../pages/ContentCalendar"));
const ContentRewriter = React.lazy(() => import("../pages/ContentRewriter"));
const KeywordClusters = React.lazy(() => import("../pages/KeywordClusters"));
const Monitoring = React.lazy(() => import("../pages/Monitoring"));
const PageSpeed = React.lazy(() => import("../pages/PageSpeed"));
const SchemaMarkup = React.lazy(() => import("../pages/SchemaMarkup"));
const SEOChecklist = React.lazy(() => import("../pages/SEOChecklist"));
const SitemapGenerator = React.lazy(() => import("../pages/SitemapGenerator"));
const SERPPreview = React.lazy(() => import("../pages/SERPPreview"));
const SERPABTesting = React.lazy(() => import("../pages/SERPABTesting"));
const Redirects = React.lazy(() => import("../pages/Redirects"));
const RankTracker = React.lazy(() => import("../pages/RankTracker"));
const ContentBriefs = React.lazy(() => import("../pages/ContentBriefs"));
const ContentRefresh = React.lazy(() => import("../pages/ContentRefresh"));
const Settings = React.lazy(() => import("../pages/Settings"));

/* ------------------------------------------------------------------ */
/*  Loading fallback                                                   */
/* ------------------------------------------------------------------ */

function PageLoading() {
  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "50vh", color: "var(--text-muted)" }}>
      <div style={{ textAlign: "center" }}>
        <div style={{ fontSize: 24, marginBottom: 8 }}>⏳</div>
        <div>Loading…</div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Root component                                                     */
/* ------------------------------------------------------------------ */

export default function App() {
  const { data, error, loading, reload } = useAsync(() => websites.list(), []);
  const [active, setActive] = useState<Website | null>(null);

  const refresh = useCallback(async () => {
    await reload();
  }, [reload]);

  const store = useMemo(
    () => ({
      websites: data?.items ?? [],
      active: active ?? data?.items?.[0] ?? null,
      loading,
      error,
      setActive,
      refresh,
    }),
    [data, active, loading, error, refresh],
  );

  return (
    <WebsiteStoreContext.Provider value={store}>
      <Suspense fallback={<PageLoading />}>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/websites" element={<Websites />} />
            <Route path="/search-console" element={<SearchConsolePage />} />
            <Route path="/content" element={<Content />} />
            <Route path="/keywords" element={<Keywords />} />
            <Route path="/opportunities" element={<Opportunities />} />
            <Route path="/audit" element={<Audit />} />
            <Route path="/ideas" element={<Ideas />} />
            <Route path="/research" element={<Research />} />
            <Route path="/article-planner" element={<ArticlePlanner />} />
            <Route path="/drafts" element={<Drafts />} />
            <Route path="/references" element={<References />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/monitoring" element={<Monitoring />} />
            <Route path="/ab-testing" element={<ABTesting />} />
            <Route path="/competitors" element={<Competitors />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/calendar" element={<ContentCalendar />} />
            <Route path="/keyword-clusters" element={<KeywordClusters />} />
            <Route path="/schema-markup" element={<SchemaMarkup />} />
            <Route path="/backlinks" element={<Backlinks />} />
            <Route path="/content-rewriter" element={<ContentRewriter />} />
            <Route path="/seo-checklist" element={<SEOChecklist />} />
            <Route path="/sitemap-generator" element={<SitemapGenerator />} />
            <Route path="/serp-preview" element={<SERPPreview />} />
            <Route path="/redirects" element={<Redirects />} />
            <Route path="/rank-tracker" element={<RankTracker />} />
            <Route path="/serp-ab-testing" element={<SERPABTesting />} />
            <Route path="/content-briefs" element={<ContentBriefs />} />
            <Route path="/content-refresh" element={<ContentRefresh />} />
            <Route path="/page-speed" element={<PageSpeed />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </Suspense>
    </WebsiteStoreContext.Provider>
  );
}
