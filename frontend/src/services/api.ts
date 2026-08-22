/** Typed API client. Single fetch wrapper maps the backend error envelope to thrown Errors. */
import { isDesktop } from "./desktop";

// The backend is always local. In the browser `npm run dev` proxies /api to it;
// in the packaged app the page lives on tauri.localhost, so we must call the
// absolute backend address instead of a relative path.
const BASE = isDesktop() ? "http://127.0.0.1:8317/api" : "/api";

/** Absolute backend URL for a given path (used for window.open / downloads). */
export function apiUrl(path: string): string {
  return `${BASE}${path}`;
}

export class ApiError extends Error {
  code: string;
  status: number;
  constructor(code: string, message: string, status: number) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("sci_backend_token") ?? "";
  const response = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { "X-Backend-Token": token } : {}),
      ...(options.headers ?? {}),
    },
  });
  const text = await response.text();
  let body: unknown = null;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    body = { raw: text };
  }
  if (!response.ok) {
    const err = (body as { error?: { code?: string; message?: string } })?.error;
    throw new ApiError(err?.code ?? "http.error", err?.message ?? `HTTP ${response.status}`, response.status);
  }
  return body as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body: body === undefined ? undefined : JSON.stringify(body) }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: body === undefined ? undefined : JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

/**
 * POST a FormData body (file uploads). The browser sets the multipart
 * Content-Type with its boundary; we must NOT override it with JSON. The token
 * and absolute desktop base URL are still applied.
 */
export async function uploadFile<T>(path: string, formData: FormData): Promise<T> {
  const token = localStorage.getItem("sci_backend_token") ?? "";
  const response = await fetch(apiUrl(path), {
    method: "POST",
    body: formData,
    headers: token ? { "X-Backend-Token": token } : undefined,
  });
  const text = await response.text();
  let body: unknown = null;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    body = { raw: text };
  }
  if (!response.ok) {
    const err = (body as { error?: { code?: string; message?: string } })?.error;
    throw new ApiError(err?.code ?? "http.error", err?.message ?? `HTTP ${response.status}`, response.status);
  }
  return body as T;
}
