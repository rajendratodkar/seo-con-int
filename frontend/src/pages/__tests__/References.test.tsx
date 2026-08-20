import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import References from "../References";

const mockUseAsync = vi.fn();
vi.mock("../../hooks/useAsync", () => ({
  useAsync: (...args: unknown[]) => mockUseAsync(...args),
}));

vi.mock("../../services/backend", () => ({
  references: { list: vi.fn(), rules: vi.fn() },
}));

describe("References page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("shows loading state", () => {
    mockUseAsync
      .mockReturnValueOnce({ data: null, error: null, loading: true, reload: vi.fn() })
      .mockReturnValueOnce({ data: null, error: null, loading: true, reload: vi.fn() });

    renderWithProviders(<References />);
    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("shows error when docs fail to load", () => {
    mockUseAsync
      .mockReturnValueOnce({ data: null, error: "Failed to load", loading: false, reload: vi.fn() })
      .mockReturnValueOnce({ data: { items: [] }, error: null, loading: false, reload: vi.fn() });

    renderWithProviders(<References />);
    expect(screen.getByText("Failed to load")).toBeInTheDocument();
  });

  it("renders reference documents and SEO rules", () => {
    mockUseAsync
      .mockReturnValueOnce({
        data: { items: [{ id: 1, category: "google", title: "Search Quality Guidelines", url: "https://example.com" }] },
        error: null, loading: false, reload: vi.fn(),
      })
      .mockReturnValueOnce({
        data: { items: [{ id: 1, rule_code: "SEO-001", name: "Title length", category: "technical", severity: "warning" }] },
        error: null, loading: false, reload: vi.fn(),
      });

    renderWithProviders(<References />);
    expect(screen.getByText("References & SEO Rules")).toBeInTheDocument();
    expect(screen.getByText("Search Quality Guidelines")).toBeInTheDocument();
    expect(screen.getByText("Title length")).toBeInTheDocument();
  });
});
