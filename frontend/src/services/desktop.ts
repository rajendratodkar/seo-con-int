/** Typed bridge to the Tauri shell. Every call is a no-op outside the desktop app. */

interface TauriGlobal {
  invoke: <T>(command: string, args?: Record<string, unknown>) => Promise<T>;
  event: {
    listen: (name: string, handler: (event: { payload: unknown }) => void) => Promise<() => void>;
  };
}

declare global {
  interface Window {
    __TAURI__?: TauriGlobal;
  }
}

export interface DesktopUpdateInfo {
  available: boolean;
  version: string | null;
  notes: string | null;
}

export function isDesktop(): boolean {
  return typeof window !== "undefined" && window.__TAURI__ !== undefined;
}

// -- backend token ------------------------------------------------------------------

/**
 * Desktop-only: fetch the per-launch backend token from the Tauri shell and
 * store it so every API request carries X-Backend-Token. Must run before the
 * first render; no-op in the browser.
 */
export async function bootstrapBackendToken(): Promise<void> {
  if (!isDesktop()) return;
  try {
    const token = await window.__TAURI__!.invoke<string | null>("get_backend_token");
    if (token) localStorage.setItem("sci_backend_token", token);
  } catch {
    // Shell not ready / command missing — keep whatever token is stored.
  }
}

// -- auto-updates -----------------------------------------------------------------

export async function checkUpdates(): Promise<DesktopUpdateInfo | null> {
  if (!isDesktop()) return null;
  try {
    return await window.__TAURI__!.invoke<DesktopUpdateInfo>("check_updates");
  } catch {
    return null; // unreachable endpoint / unsigned config — never break the UI
  }
}

export async function installUpdate(): Promise<boolean> {
  if (!isDesktop()) return false;
  return window.__TAURI__!.invoke<boolean>("install_update");
}

// -- deep links (sci://) ------------------------------------------------------------

/** Route path encoded in a sci:// URL, e.g. sci://drafts → "/drafts". */
export function deepLinkToRoute(url: string): string {
  const path = url.replace(/^sci:\/\//, "").split("?")[0];
  return path.startsWith("/") ? path : `/${path}`;
}

export async function getLaunchUrl(): Promise<string | null> {
  if (!isDesktop()) return null;
  return window.__TAURI__!.invoke<string | null>("get_launch_url");
}

/** Subscribe to sci:// links while the app is running. Returns an unsubscribe fn. */
export async function listenDeepLink(onLink: (url: string) => void): Promise<() => void> {
  if (!isDesktop()) return () => undefined;
  return window.__TAURI__!.event.listen("deep-link", (event) => {
    if (typeof event.payload === "string") onLink(event.payload);
  });
}

// -- OS keychain --------------------------------------------------------------------

export async function keychainSet(key: string, value: string): Promise<boolean> {
  if (!isDesktop()) return false;
  return window.__TAURI__!.invoke<boolean>("keychain_set", { key, value });
}

export async function keychainGet(key: string): Promise<string | null> {
  if (!isDesktop()) return null;
  return window.__TAURI__!.invoke<string | null>("keychain_get", { key });
}

export async function keychainDelete(key: string): Promise<boolean> {
  if (!isDesktop()) return false;
  return window.__TAURI__!.invoke<boolean>("keychain_delete", { key });
}
