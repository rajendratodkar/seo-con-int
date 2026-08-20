import { describe, it, expect, vi, beforeEach } from "vitest";
import { track, installCrashReporter } from "../telemetry";

// Mock the diagnostics module
vi.mock("../backend", () => ({
  diagnostics: {
    track: vi.fn().mockResolvedValue({ ok: true }),
    crash: vi.fn().mockResolvedValue({ ok: true }),
  },
}));

import { diagnostics } from "../backend";

describe("track", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("calls diagnostics.track with event and detail", async () => {
    track("page_view", "/dashboard");

    expect(diagnostics.track).toHaveBeenCalledWith("page_view", "/dashboard");
  });

  it("calls diagnostics.track with null detail when omitted", () => {
    track("action");

    expect(diagnostics.track).toHaveBeenCalledWith("action", undefined);
  });

  it("does not throw when tracking fails", async () => {
    (diagnostics.track as ReturnType<typeof vi.fn>).mockRejectedValue(new Error("network"));

    expect(() => track("page_view", "/test")).not.toThrow();
  });
});

describe("installCrashReporter", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("installs error event listener", () => {
    const addSpy = vi.spyOn(window, "addEventListener");

    installCrashReporter(() => "/test-route");

    expect(addSpy).toHaveBeenCalledWith("error", expect.any(Function));
    expect(addSpy).toHaveBeenCalledWith("unhandledrejection", expect.any(Function));

    addSpy.mockRestore();
  });

  it("reports crashes to diagnostics on window error", () => {
    installCrashReporter(() => "/dashboard");

    const error = new Error("test crash");
    window.dispatchEvent(new ErrorEvent("error", { message: "test crash", error }));

    expect(diagnostics.crash).toHaveBeenCalledWith(
      "test crash",
      error.stack,
      "/dashboard",
    );
  });

  it("reports unhandled rejections to diagnostics", () => {
    installCrashReporter(() => "/settings");

    const reason = new Error("unhandled promise");
    const event = new PromiseRejectionEvent("unhandledrejection", {
      promise: Promise.resolve(),
      reason,
      cancelable: false,
    });
    Object.defineProperty(event, "promise", { value: Promise.resolve() });
    window.dispatchEvent(event);

    expect(diagnostics.crash).toHaveBeenCalledWith(
      "Unhandled rejection: unhandled promise",
      reason.stack,
      "/settings",
    );
  });

  it("does not throw if diagnostics.crash fails", () => {
    (diagnostics.crash as ReturnType<typeof vi.fn>).mockRejectedValue(new Error("fail"));

    installCrashReporter(() => "/route");

    expect(() => {
      window.dispatchEvent(new ErrorEvent("error", { message: "boom" }));
    }).not.toThrow();
  });
});
