import { useCallback, useMemo, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
// Root component: website store + all routes (pages are lazy-free by design)
import { AppShell } from "../layouts/AppShell";
import { WebsiteStoreContext } from "../stores/websiteStore";
import { useAsync } from "../hooks/useAsync";
import { websites } from "../services/backend";
import type { Website } from "../types";

import Dashboard from "../pages/Dashboard";
import Websites from "../pages/Websites";
import SearchConsolePage from "../pages/SearchConsole";
import Content from "../pages/Content";
import Keywords from "../pages/Keywords";
import Opportunities from "../pages/Opportunities";
import Audit from "../pages/Audit";
import Ideas from "../pages/Ideas";
import Research from "../pages/Research";
import ArticlePlanner from "../pages/ArticlePlanner";
import Drafts from "../pages/Drafts";
import References from "../pages/References";
import Reports from "../pages/Reports";
import ABTesting from "../pages/ABTesting";
import Analytics from "../pages/Analytics";
import Backlinks from "../pages/Backlinks";
import Competitors from "../pages/Competitors";
import ContentCalendar from "../pages/ContentCalendar";
import ContentRewriter from "../pages/ContentRewriter";
import KeywordClusters from "../pages/KeywordClusters";
import Monitoring from "../pages/Monitoring";
import PageSpeed from "../pages/PageSpeed";
import SchemaMarkup from "../pages/SchemaMarkup";
import SEOChecklist from "../pages/SEOChecklist";
import SitemapGenerator from "../pages/SitemapGenerator";
import SERPPreview from "../pages/SERPPreview";
import SERPABTesting from "../pages/SERPABTesting";
import Redirects from "../pages/Redirects";
import RankTracker from "../pages/RankTracker";
import ContentBriefs from "../pages/ContentBriefs";
import ContentRefresh from "../pages/ContentRefresh";
import Settings from "../pages/Settings";

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
    </WebsiteStoreContext.Provider>
  );
}
