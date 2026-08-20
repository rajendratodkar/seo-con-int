import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useWebsiteStore } from "../stores/websiteStore";
import { UpdatePrompt } from "../components/UpdatePrompt";
import { deepLinkToRoute, getLaunchUrl, listenDeepLink } from "../services/desktop";
import { track } from "../services/telemetry";

const NAV = [
  { to: "/", label: "🏠 Dashboard", end: true },
  { to: "/websites", label: "🌐 Websites" },
  { to: "/search-console", label: "📊 Search Console" },
  { to: "/content", label: "📄 Content" },
  { to: "/keywords", label: "🔑 Keywords" },
  { to: "/opportunities", label: "🎯 Opportunities" },
  { to: "/audit", label: "🔍 Content Audit" },
  { to: "/ideas", label: "💡 Content Ideas" },
  { to: "/research", label: "🔬 Research" },
  { to: "/article-planner", label: "📝 Article Planner" },
  { to: "/drafts", label: "📤 Drafts & Publishing" },
  { to: "/references", label: "📚 References" },
  { to: "/reports", label: "📈 Reports" },
  { to: "/monitoring", label: "🔔 Monitoring" },
  { to: "/ab-testing", label: "🧪 A/B Testing" },
  { to: "/competitors", label: "🏆 Competitors" },
  { to: "/analytics", label: "📊 Analytics" },
  { to: "/keyword-clusters", label: "🧩 Clusters" },
  { to: "/schema-markup", label: "📐 Schema" },
  { to: "/calendar", label: "📅 Calendar" },
  { to: "/backlinks", label: "🔗 Backlinks" },
  { to: "/page-speed", label: "⚡ Page Speed" },
  { to: "/content-rewriter", label: "✨ Rewriter" },
  { to: "/seo-checklist", label: "✅ Checklist" },
  { to: "/sitemap-generator", label: "🗺️ Sitemap" },
  { to: "/serp-preview", label: "🔍 SERP Preview" },
  { to: "/redirects", label: "↗️ Redirects" },
  { to: "/rank-tracker", label: "📈 Rank Tracker" },
  { to: "/serp-ab-testing", label: "🧪 SERP A/B" },
  { to: "/content-briefs", label: "📋 Content Briefs" },
  { to: "/content-refresh", label: "🔄 Refresh" },
];

function useOnlineStatus(): boolean {
  const [online, setOnline] = useState(navigator.onLine);
  useEffect(() => {
    const up = () => setOnline(true);
    const down = () => setOnline(false);
    window.addEventListener("online", up);
    window.addEventListener("offline", down);
    return () => {
      window.removeEventListener("online", up);
      window.removeEventListener("offline", down);
    };
  }, []);
  return online;
}

export function AppShell() {
  const { websites, active, setActive } = useWebsiteStore();
  const location = useLocation();
  const navigate = useNavigate();
  const online = useOnlineStatus();

  // Usage analytics: one page_view per navigation (local only).
  useEffect(() => {
    track("page_view", location.pathname);
  }, [location.pathname]);

  // Deep linking: sci://... opens the matching route (launch + while running).
  useEffect(() => {
    let unsubscribe: () => void = () => undefined;
    getLaunchUrl().then((url) => {
      if (url) navigate(deepLinkToRoute(url));
    });
    listenDeepLink((url) => navigate(deepLinkToRoute(url))).then((fn) => {
      unsubscribe = fn;
    });
    return () => unsubscribe();
  }, [navigate]);

  return (
    <div className="app-shell">
      <nav className="sidebar">
        <h1>SEO Intelligence</h1>
        {!online && (
          <div className="card" style={{ background: "#fff3cd", border: "1px solid #ffc107", fontSize: 12, marginBottom: 8 }}>
            ⚠ Offline — cached data stays usable; sync & crawl need a connection.
          </div>
        )}
        {websites.length > 0 && (
          <select
            value={active?.id ?? ""}
            onChange={(e) => setActive(websites.find((w) => w.id === Number(e.target.value)) ?? null)}
            style={{ width: "100%", marginBottom: 12 }}
          >
            {websites.map((w) => (
              <option key={w.id} value={w.id}>{w.name}</option>
            ))}
          </select>
        )}
        {NAV.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.end} className={({ isActive }) => (isActive ? "active" : "")}>
            {item.label}
          </NavLink>
        ))}
        <div className="divider" />
        <NavLink to="/settings" className={({ isActive }) => (isActive ? "active" : "")}>
          ⚙ Settings
        </NavLink>
      </nav>
      <main className="main">
        <UpdatePrompt />
        <Outlet />
      </main>
    </div>
  );
}
