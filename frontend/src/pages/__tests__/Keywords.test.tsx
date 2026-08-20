import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import Keywords from "../Keywords";

const mockUseAsync = vi.fn();
vi.mock("../../hooks/useAsync", () => ({
  useAsync: (...args: unknown[]) => mockUseAsync(...args),
}));

vi.mock("../../services/backend", () => ({
  keywords: { list: vi.fn(), create: vi.fn(), remove: vi.fn(), importFromSc: vi.fn() },
}));

describe("Keywords page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("shows empty state when no website is active", () => {
    mockUseAsync.mockReturnValue({ data: null, error: null, loading: false, reload: vi.fn() });
    renderWithProviders(<Keywords />, { store: { active: null } });
    expect(screen.getByText("Add a website first.")).toBeInTheDocument();
  });

  it("shows loading state", () => {
    mockUseAsync.mockReturnValue({ data: null, error: null, loading: true, reload: vi.fn() });
    renderWithProviders(<Keywords />);
    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("shows error state", () => {
    mockUseAsync.mockReturnValue({ data: null, error: "Connection failed", loading: false, reload: vi.fn() });
    renderWithProviders(<Keywords />);
    expect(screen.getByText("Connection failed")).toBeInTheDocument();
  });

  it("shows empty state when no keywords", () => {
    mockUseAsync.mockReturnValue({
      data: { items: [], total: 0, page: 1, page_size: 200 },
      error: null, loading: false, reload: vi.fn(),
    });
    renderWithProviders(<Keywords />);
    expect(screen.getByText("No keywords yet.")).toBeInTheDocument();
  });

  it("renders keywords table with data", () => {
    mockUseAsync.mockReturnValue({
      data: {
        items: [
          { id: 1, keyword: "seo tips", search_intent: "informational", group_name: "seo", source: "manual" },
          { id: 2, keyword: "best tools", search_intent: null, group_name: null, source: "sc_import" },
        ],
        total: 2, page: 1, page_size: 200,
      },
      error: null, loading: false, reload: vi.fn(),
    });
    renderWithProviders(<Keywords />);
    expect(screen.getByText("Keywords")).toBeInTheDocument();
    expect(screen.getByText("seo tips")).toBeInTheDocument();
    expect(screen.getByText("best tools")).toBeInTheDocument();
  });
});
