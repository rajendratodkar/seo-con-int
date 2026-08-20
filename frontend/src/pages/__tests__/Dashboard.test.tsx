import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import Dashboard from "../Dashboard";

const mockUseAsync = vi.fn();
vi.mock("../../hooks/useAsync", () => ({
  useAsync: (...args: unknown[]) => mockUseAsync(...args),
}));

vi.mock("../../services/backend", () => ({
  health: vi.fn(),
  reports: { weekly: vi.fn() },
}));

describe("Dashboard page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state while health check is pending", () => {
    // First call = health (loading), second = weekly
    mockUseAsync
      .mockReturnValueOnce({ data: null, error: null, loading: true, reload: vi.fn() })
      .mockReturnValueOnce({ data: null, error: null, loading: true, reload: vi.fn() });

    renderWithProviders(<Dashboard />);

    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("shows error when backend is unreachable", () => {
    mockUseAsync
      .mockReturnValueOnce({ data: { status: "ok", database: "ok", version: "0.1.0" }, error: null, loading: false, reload: vi.fn() })
      .mockReturnValueOnce({ data: null, error: "Connection refused", loading: false, reload: vi.fn() });

    renderWithProviders(<Dashboard />);

    expect(screen.getByText(/Connection refused/)).toBeInTheDocument();
  });

  it("renders health status in subtitle", () => {
    mockUseAsync
      .mockReturnValueOnce({ data: { status: "ok", database: "ok", version: "0.1.0" }, error: null, loading: false, reload: vi.fn() })
      .mockReturnValueOnce({ data: null, error: null, loading: true, reload: vi.fn() });

    renderWithProviders(<Dashboard />);

    expect(screen.getByText(/Backend ok · database ok · v0.1.0/)).toBeInTheDocument();
  });

  it("renders KPI cards with weekly data", () => {
    mockUseAsync
      .mockReturnValueOnce({ data: { status: "ok", database: "ok", version: "0.1.0" }, error: null, loading: false, reload: vi.fn() })
      .mockReturnValueOnce({
        data: {
          traffic: { clicks: 1234, impressions: 56789, clicks_delta: 120, impressions_delta: -500 },
          opportunities: 8,
          audit: { keep: 5, improve: 2 },
          findings: [],
        },
        error: null,
        loading: false,
        reload: vi.fn(),
      });

    renderWithProviders(<Dashboard />);

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("1,234")).toBeInTheDocument();
    expect(screen.getByText("56,789")).toBeInTheDocument();
    expect(screen.getByText("8")).toBeInTheDocument();
  });

  it("shows audit verdicts section", () => {
    mockUseAsync
      .mockReturnValueOnce({ data: { status: "ok", database: "ok", version: "0.1.0" }, error: null, loading: false, reload: vi.fn() })
      .mockReturnValueOnce({
        data: {
          traffic: { clicks: 0, impressions: 0 },
          opportunities: 0,
          audit: { keep: 3, improve: 1, refresh: 2 },
          findings: [],
        },
        error: null,
        loading: false,
        reload: vi.fn(),
      });

    renderWithProviders(<Dashboard />);

    expect(screen.getByText("Content audit verdicts")).toBeInTheDocument();
  });

  it("shows findings table when findings exist", () => {
    mockUseAsync
      .mockReturnValueOnce({ data: { status: "ok", database: "ok", version: "0.1.0" }, error: null, loading: false, reload: vi.fn() })
      .mockReturnValueOnce({
        data: {
          traffic: { clicks: 0, impressions: 0 },
          opportunities: 0,
          audit: {},
          findings: [
            { severity: "high", rec_type: "technical", n: 5 },
            { severity: "low", rec_type: "content", n: 12 },
          ],
        },
        error: null,
        loading: false,
        reload: vi.fn(),
      });

    renderWithProviders(<Dashboard />);

    expect(screen.getByText("Open findings")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
  });
});
