import { render, type RenderOptions } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { ThemeProvider } from "./stores/themeStore";
import { WebsiteStoreContext, type WebsiteStore } from "./stores/websiteStore";
import type { Website } from "./types";

/* ------------------------------------------------------------------ */
/*  Default mock values                                                */
/* ------------------------------------------------------------------ */

export const MOCK_WEBSITE: Website = {
  id: 1,
  name: "Test Site",
  url: "https://example.com",
  platform: "wordpress",
  sitemap_url: null,
  status: "active",
  created_at: "2026-01-01T00:00:00",
};

export const MOCK_WEBSITES: Website[] = [MOCK_WEBSITE];

const DEFAULT_STORE: WebsiteStore = {
  websites: MOCK_WEBSITES,
  active: MOCK_WEBSITE,
  loading: false,
  error: null,
  setActive: () => {},
  refresh: async () => {},
};

/* ------------------------------------------------------------------ */
/*  Custom render with all providers                                   */
/* ------------------------------------------------------------------ */

interface CustomRenderOptions extends Omit<RenderOptions, "wrapper"> {
  store?: Partial<WebsiteStore>;
  route?: string;
}

export function renderWithProviders(
  ui: React.ReactElement,
  options: CustomRenderOptions = {},
) {
  const { store = {}, route = "/", ...renderOptions } = options;
  const storeValue = { ...DEFAULT_STORE, ...store };

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <ThemeProvider>
        <WebsiteStoreContext.Provider value={storeValue}>
          <BrowserRouter>
            {children}
          </BrowserRouter>
        </WebsiteStoreContext.Provider>
      </ThemeProvider>
    );
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions });
}
