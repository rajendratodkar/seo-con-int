import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import Content from "../Content";

// Mock useAsync to control data states
const mockUseAsync = vi.fn();
vi.mock("../../hooks/useAsync", () => ({
  useAsync: (...args: unknown[]) => mockUseAsync(...args),
}));

// Mock backend API
vi.mock("../../services/backend", () => ({
  pages: { list: vi.fn() },
}));

import { pages as pagesApi } from "../../services/backend";

describe("Content page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows empty state when no website is active", () => {
    mockUseAsync.mockReturnValue({ data: null, error: null, loading: false, reload: vi.fn() });

    renderWithProviders(<Content />, { store: { active: null } });

    expect(screen.getByText("Add a website first.")).toBeInTheDocument();
  });

  it("shows loading state", () => {
    mockUseAsync.mockReturnValue({ data: null, error: null, loading: true, reload: vi.fn() });

    renderWithProviders(<Content />);

    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("shows error state", () => {
    mockUseAsync.mockReturnValue({ data: null, error: "Connection failed", loading: false, reload: vi.fn() });

    renderWithProviders(<Content />);

    expect(screen.getByText("Connection failed")).toBeInTheDocument();
  });

  it("shows empty state when no pages crawled", () => {
    mockUseAsync.mockReturnValue({
      data: { items: [], total: 0, page: 1, page_size: 50 },
      error: null,
      loading: false,
      reload: vi.fn(),
    });

    renderWithProviders(<Content />);

    expect(screen.getByText(/No pages crawled yet/)).toBeInTheDocument();
  });

  it("renders page table with data", () => {
    const mockPages = [
      { id: 1, title: "Home", url: "https://example.com/", status_code: 200, crawl_status: "completed", last_crawled_at: "2026-01-15T10:30:00", meta_description: "Welcome" },
      { id: 2, title: null, url: "https://example.com/about", status_code: 200, crawl_status: "completed", last_crawled_at: "2026-01-15T10:31:00", meta_description: null },
    ];

    mockUseAsync.mockReturnValue({
      data: { items: mockPages, total: 2, page: 1, page_size: 50 },
      error: null,
      loading: false,
      reload: vi.fn(),
    });

    renderWithProviders(<Content />);

    expect(screen.getByText("Content")).toBeInTheDocument();
    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("https://example.com/")).toBeInTheDocument();
    expect(screen.getByText("https://example.com/about")).toBeInTheDocument();
  });

  it("shows page count in subtitle when pages exist", () => {
    mockUseAsync.mockReturnValue({
      data: {
        items: [{ id: 1, title: "Home", url: "https://example.com/", status_code: 200, crawl_status: "completed", last_crawled_at: null, meta_description: null }],
        total: 42, page: 1, page_size: 50
      },
      error: null,
      loading: false,
      reload: vi.fn(),
    });

    renderWithProviders(<Content />);

    expect(screen.getByText(/42 pages/)).toBeInTheDocument();
  });
});
