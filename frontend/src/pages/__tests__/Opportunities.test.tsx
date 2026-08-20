import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import Opportunities from "../Opportunities";

const mockUseAsync = vi.fn();
vi.mock("../../hooks/useAsync", () => ({
  useAsync: (...args: unknown[]) => mockUseAsync(...args),
}));

vi.mock("../../services/backend", () => ({
  findings: { list: vi.fn(), analyze: vi.fn(), setStatus: vi.fn() },
  opportunities: { list: vi.fn() },
}));

describe("Opportunities page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("shows empty state when no website", () => {
    mockUseAsync.mockReturnValue({ data: null, error: null, loading: false, reload: vi.fn() });
    renderWithProviders(<Opportunities />, { store: { active: null } });
    expect(screen.getByText("Add a website first.")).toBeInTheDocument();
  });

  it("shows loading state", () => {
    mockUseAsync.mockReturnValue({ data: null, error: null, loading: true, reload: vi.fn() });
    renderWithProviders(<Opportunities />);
    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("renders opportunities and findings", () => {
    mockUseAsync
      .mockReturnValueOnce({ data: { items: [{ page_url: "/home", recommendation: "Update title", evidence: "Low CTR", confidence: "high" }] }, error: null, loading: false, reload: vi.fn() })
      .mockReturnValueOnce({ data: { items: [{ id: 1, recommendation: "Fix meta", why: "Missing", rec_type: "rule_based", severity: "warning" }] }, error: null, loading: false, reload: vi.fn() });

    renderWithProviders(<Opportunities />);
    expect(screen.getByText("Opportunities & Findings")).toBeInTheDocument();
    expect(screen.getByText("Update title")).toBeInTheDocument();
    expect(screen.getByText("Fix meta")).toBeInTheDocument();
  });
});
