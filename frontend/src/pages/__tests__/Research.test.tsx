import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import Research from "../Research";

const mockUseAsync = vi.fn();
vi.mock("../../hooks/useAsync", () => ({
  useAsync: (...args: unknown[]) => mockUseAsync(...args),
}));

vi.mock("../../services/backend", () => ({
  research: { list: vi.fn(), add: vi.fn(), remove: vi.fn(), fromFile: vi.fn() },
}));

vi.mock("../../services/telemetry", () => ({
  track: vi.fn(),
}));

describe("Research page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("shows loading state", () => {
    mockUseAsync.mockReturnValue({ data: null, error: null, loading: true, reload: vi.fn() });
    renderWithProviders(<Research />);
    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("shows error state", () => {
    mockUseAsync.mockReturnValue({ data: null, error: "Server error", loading: false, reload: vi.fn() });
    renderWithProviders(<Research />);
    expect(screen.getByText("Server error")).toBeInTheDocument();
  });

  it("shows empty state when no sources", () => {
    mockUseAsync.mockReturnValue({
      data: { items: [], total: 0, page: 1, page_size: 100 },
      error: null, loading: false, reload: vi.fn(),
    });
    renderWithProviders(<Research />);
    expect(screen.getByText("No research sources yet.")).toBeInTheDocument();
  });

  it("renders research sources table with data", () => {
    mockUseAsync.mockReturnValue({
      data: {
        items: [
          { id: 1, title: "SEO Video", url: "https://youtube.com/watch?v=123", source_type: "youtube", availability_status: "full", extraction_status: "completed", error_message: null },
          { id: 2, title: null, url: "https://example.com/article", source_type: "article", availability_status: "metadata_only", extraction_status: "pending", error_message: null },
        ],
        total: 2, page: 1, page_size: 100,
      },
      error: null, loading: false, reload: vi.fn(),
    });
    renderWithProviders(<Research />);
    expect(screen.getByText("Research")).toBeInTheDocument();
    expect(screen.getByText("SEO Video")).toBeInTheDocument();
    expect(screen.getByText("https://example.com/article")).toBeInTheDocument();
  });
});
