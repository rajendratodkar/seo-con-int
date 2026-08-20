import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { api, ApiError } from "../api";

// Mock fetch globally
const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

function jsonResponse(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function errorResponse(code: string, message: string, status = 400) {
  return jsonResponse({ error: { code, message } }, status);
}

describe("api client", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // --- GET ---

  it("get() sends GET request with correct path", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ ok: true }));

    const result = await api.get<{ ok: boolean }>("/health/");

    expect(mockFetch).toHaveBeenCalledOnce();
    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toBe("/api/health/");
    expect(opts.method).toBeUndefined(); // GET is default
    expect(result).toEqual({ ok: true });
  });

  // --- POST ---

  it("post() sends POST with JSON body", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ id: 1 }));

    const result = await api.post<{ id: number }>("/websites/", { name: "Test" });

    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toBe("/api/websites/");
    expect(opts.method).toBe("POST");
    expect(opts.body).toBe(JSON.stringify({ name: "Test" }));
    expect(result).toEqual({ id: 1 });
  });

  it("post() omits body when undefined", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ ok: true }));

    await api.post("/some/endpoint");

    const [, opts] = mockFetch.mock.calls[0];
    expect(opts.body).toBeUndefined();
  });

  // --- PUT ---

  it("put() sends PUT with JSON body", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ saved: true }));

    await api.put("/settings/config", { key: "value" });

    const [, opts] = mockFetch.mock.calls[0];
    expect(opts.method).toBe("PUT");
    expect(opts.body).toBe(JSON.stringify({ key: "value" }));
  });

  // --- PATCH ---

  it("patch() sends PATCH with JSON body", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ updated: true }));

    await api.patch("/websites/1", { name: "New Name" });

    const [, opts] = mockFetch.mock.calls[0];
    expect(opts.method).toBe("PATCH");
    expect(opts.body).toBe(JSON.stringify({ name: "New Name" }));
  });

  // --- DELETE ---

  it("delete() sends DELETE request", async () => {
    mockFetch.mockResolvedValue(jsonResponse(null));

    await api.delete("/websites/1");

    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toBe("/api/websites/1");
    expect(opts.method).toBe("DELETE");
  });

  // --- Error handling ---

  it("throws ApiError on non-OK response with error envelope", async () => {
    mockFetch.mockResolvedValue(errorResponse("not_found", "Item not found", 404));

    try {
      await api.get("/missing");
      expect.fail("should have thrown");
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      const err = e as ApiError;
      expect(err.code).toBe("not_found");
      expect(err.message).toBe("Item not found");
      expect(err.status).toBe(404);
    }
  });

  it("throws ApiError with default message when error envelope missing", async () => {
    mockFetch.mockResolvedValue(new Response("Server Error", { status: 500 }));

    try {
      await api.get("/crash");
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      const err = e as ApiError;
      expect(err.code).toBe("http.error");
      expect(err.message).toBe("HTTP 500");
      expect(err.status).toBe(500);
    }
  });

  it("handles non-JSON response body", async () => {
    mockFetch.mockResolvedValue(new Response("plain text", { status: 200 }));

    const result = await api.get("/raw");
    expect(result).toEqual({ raw: "plain text" });
  });

  it("handles empty response body", async () => {
    mockFetch.mockResolvedValue(new Response(null, { status: 204 }));

    const result = await api.get("/no-content");
    expect(result).toBeNull();
  });

  // --- Token injection ---

  it("includes X-Backend-Token when set in localStorage", async () => {
    localStorage.setItem("sci_backend_token", "my-secret-token");
    mockFetch.mockResolvedValue(jsonResponse({ ok: true }));

    await api.get("/protected");

    const [, opts] = mockFetch.mock.calls[0];
    expect(opts.headers["X-Backend-Token"]).toBe("my-secret-token");
  });

  it("does not include X-Backend-Token when not set", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ ok: true }));

    await api.get("/public");

    const [, opts] = mockFetch.mock.calls[0];
    expect(opts.headers["X-Backend-Token"]).toBeUndefined();
  });

  it("always sets Content-Type to application/json", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ ok: true }));

    await api.get("/test");

    const [, opts] = mockFetch.mock.calls[0];
    expect(opts.headers["Content-Type"]).toBe("application/json");
  });
});
