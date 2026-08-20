/** Active website store — pages read the selected website from here, not the URL. */
import { createContext, useContext } from "react";
import type { Website } from "../types";

export interface WebsiteStore {
  websites: Website[];
  active: Website | null;
  /** True while the initial website list is being fetched. */
  loading: boolean;
  /** Set when the website list fetch failed (e.g. backend unreachable). */
  error: string | null;
  setActive: (website: Website | null) => void;
  refresh: () => Promise<void>;
}

export const WebsiteStoreContext = createContext<WebsiteStore>({
  websites: [],
  active: null,
  loading: true,
  error: null,
  setActive: () => undefined,
  refresh: async () => undefined,
});

export const useWebsiteStore = () => useContext(WebsiteStoreContext);
