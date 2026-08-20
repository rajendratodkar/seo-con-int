import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import Audit from "../Audit";

const mockUseAsync = vi.fn();
vi.mock("../../hooks/useAsync", () => ({
  useAsync: (...args: unknown[]) => mockUseAsync(...args),
}));

vi.mock("../../services/backend", () => ({
  audit: { run: vi.fn() },
}));

describe("Audit page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows empty state when no website is active", () => {
    mockUseAsync.mockReturnValue({ data: null, error: null, loading: false, reload: vi.fn() });

    renderWithProviders(<Audit />, { store: { active: null } });

    expect(screen.getByText("Add a website first.")).toBeInTheDocument();
  });

  it("shows loading state", () => {
    mockUseAsync.mockReturnValue({ data: null, error: null, loading: true, reload: vi.fn() });

    renderWithProviders(<Audit />);

    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("shows error state", () => {
    mockUseAsync.mockReturnValue({ data: null, error: "Server error", loading: false, reload: vi.fn() });

    renderWithProviders(<Audit />);

    expect(screen.getByText("Server error")).toBeInTheDocument();
  });

  it("shows empty state when no pages to audit", () => {
    mockUseAsync.mockReturnValue({
      data: { items: [], summary: {} },
      error: null,
      loading: false,
      reload: vi.fn(),
    });

    renderWithProviders(<Audit />);

    expect(screen.getByText(/No crawled pages to audit/)).toBeInTheDocument();
  });

  it("renders audit results with verdict badges", () => {
    const auditData = {
      items: [
        { page_id: 1, title: "Home", url: "https://example.com/", verdict: "keep", reason: "Good performance", clicks: 150, impressions: 5000 },
        { page_id: 2, title: "Old Post", url: "https://example.com/old", verdict: "refresh", reason: "Declining traffic", clicks: 10, impressions: 200 },
      ],
      summary: { keep: 1, improve: 0, refresh: 1, consolidate: 0, review: 0 },
    };

    mockUseAsync.mockReturnValue({
      data: auditData,
      error: null,
      loading: false,
      reload: vi.fn(),
    });

    renderWithProviders(<Audit />);

    expect(screen.getByText("Content Audit")).toBeInTheDocument();
    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("Old Post")).toBeInTheDocument();
    expect(screen.getByText("Good performance")).toBeInTheDocument();
    expect(screen.getByText("Declining traffic")).toBeInTheDocument();
    expect(screen.getByText("150")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
  });

  it("displays KPI grid with verdict counts", () => {
    const auditData = {
      items: [
        { page_id: 1, title: "Home", url: "https://example.com/", verdict: "keep", reason: "Good", clicks: 10, impressions: 100 },
        { page_id: 2, title: "Old", url: "https://example.com/old", verdict: "refresh", reason: "Stale", clicks: 5, impressions: 50 },
      ],
      summary: { keep: 5, improve: 3, refresh: 2, consolidate: 1, review: 0 },
    };

    mockUseAsync.mockReturnValue({
      data: auditData,
      error: null,
      loading: false,
      reload: vi.fn(),
    });

    const { getAllByText } = renderWithProviders(<Audit />);

    // KPI grid shows counts for each verdict
    expect(getAllByText("5").length).toBeGreaterThanOrEqual(1);
    expect(getAllByText("3").length).toBeGreaterThanOrEqual(1);
    expect(getAllByText("2").length).toBeGreaterThanOrEqual(1);
  });
});
