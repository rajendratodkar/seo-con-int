import { describe, it, expect, beforeEach, vi } from "vitest";
import { deepLinkToRoute, isDesktop, bootstrapBackendToken } from "../desktop";

describe("deepLinkToRoute", () => {
  it("converts sci://drafts to /drafts", () => {
    expect(deepLinkToRoute("sci://drafts")).toBe("/drafts");
  });

  it("converts sci:///websites to /websites", () => {
    expect(deepLinkToRoute("sci:///websites")).toBe("/websites");
  });

  it("preserves query strings", () => {
    expect(deepLinkToRoute("sci://search-console?tab=queries")).toBe("/search-console");
  });

  it("handles paths with slashes", () => {
    expect(deepLinkToRoute("sci://settings/ai")).toBe("/settings/ai");
  });

  it("adds leading slash if missing", () => {
    expect(deepLinkToRoute("sci://drafts")).toBe("/drafts");
  });
});

describe("isDesktop", () => {
  beforeEach(() => {
    delete (window as { __TAURI__?: unknown }).__TAURI__;
  });

  it("returns false when __TAURI__ is not defined", () => {
    expect(isDesktop()).toBe(false);
  });

  it("returns true when __TAURI__ is defined", () => {
    (window as { __TAURI__: unknown }).__TAURI__ = {};
    expect(isDesktop()).toBe(true);
  });
});

describe("bootstrapBackendToken", () => {
  beforeEach(() => {
    delete (window as { __TAURI__?: unknown }).__TAURI__;
    localStorage.clear();
  });

  it("is a no-op outside desktop (no __TAURI__)", async () => {
    await bootstrapBackendToken();
    expect(localStorage.getItem("sci_backend_token")).toBeNull();
  });

  it("does not throw outside desktop", async () => {
    await expect(bootstrapBackendToken()).resolves.toBeUndefined();
  });
});
