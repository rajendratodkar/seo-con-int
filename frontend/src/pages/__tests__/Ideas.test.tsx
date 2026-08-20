import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import Ideas from "../Ideas";

const mockUseAsync = vi.fn();
vi.mock("../../hooks/useAsync", () => ({
  useAsync: (...args: unknown[]) => mockUseAsync(...args),
}));

vi.mock("../../services/backend", () => ({
  ideas: { list: vi.fn(), generate: vi.fn(), create: vi.fn(), setStatus: vi.fn() },
}));

describe("Ideas page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("shows loading state", () => {
    mockUseAsync.mockReturnValue({ data: null, error: null, loading: true, reload: vi.fn() });
    renderWithProviders(<Ideas />);
    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("shows error state", () => {
    mockUseAsync.mockReturnValue({ data: null, error: "API error", loading: false, reload: vi.fn() });
    renderWithProviders(<Ideas />);
    expect(screen.getByText("API error")).toBeInTheDocument();
  });

  it("shows empty state when no ideas", () => {
    mockUseAsync.mockReturnValue({
      data: { items: [], total: 0 }, error: null, loading: false, reload: vi.fn(),
    });
    renderWithProviders(<Ideas />);
    expect(screen.getByText(/No ideas yet/)).toBeInTheDocument();
  });

  it("renders ideas table with data", () => {
    mockUseAsync.mockReturnValue({
      data: {
        items: [
          { id: 1, title: "SEO Tips", description: "Best practices", source_type: "manual", score: 0.85, status: "draft" },
          { id: 2, title: "Content Strategy", description: null, source_type: "sc_gap", score: null, status: "approved" },
        ],
        total: 2,
      },
      error: null, loading: false, reload: vi.fn(),
    });
    renderWithProviders(<Ideas />);
    expect(screen.getByText("Content Ideas")).toBeInTheDocument();
    expect(screen.getByText("SEO Tips")).toBeInTheDocument();
    expect(screen.getByText("Content Strategy")).toBeInTheDocument();
    expect(screen.getByText("0.85")).toBeInTheDocument();
  });
});
