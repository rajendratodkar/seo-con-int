import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import ArticlePlanner from "../ArticlePlanner";

const mockUseAsync = vi.fn();
vi.mock("../../hooks/useAsync", () => ({
  useAsync: (...args: unknown[]) => mockUseAsync(...args),
}));

vi.mock("../../services/backend", () => ({
  plans: { list: vi.fn(), create: vi.fn(), generateDraft: vi.fn() },
}));

describe("ArticlePlanner page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("shows loading state", () => {
    mockUseAsync.mockReturnValue({ data: null, error: null, loading: true, reload: vi.fn() });
    renderWithProviders(<ArticlePlanner />);
    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("shows error state", () => {
    mockUseAsync.mockReturnValue({ data: null, error: "API error", loading: false, reload: vi.fn() });
    renderWithProviders(<ArticlePlanner />);
    expect(screen.getByText("API error")).toBeInTheDocument();
  });

  it("shows empty state", () => {
    mockUseAsync.mockReturnValue({ data: { items: [], total: 0 }, error: null, loading: false, reload: vi.fn() });
    renderWithProviders(<ArticlePlanner />);
    expect(screen.getByText(/No article plans yet/)).toBeInTheDocument();
  });

  it("renders plans table", () => {
    mockUseAsync.mockReturnValue({
      data: { items: [{ id: 1, title: "SEO Guide", search_intent: "informational", status: "brief_ready" }] },
      error: null, loading: false, reload: vi.fn(),
    });
    renderWithProviders(<ArticlePlanner />);
    expect(screen.getByText("Article Planner")).toBeInTheDocument();
    expect(screen.getByText("SEO Guide")).toBeInTheDocument();
  });
});
