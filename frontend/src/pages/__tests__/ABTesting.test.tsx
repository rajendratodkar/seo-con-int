import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import ABTesting from "../ABTesting";

const mockUseAsync = vi.fn();
vi.mock("../../hooks/useAsync", () => ({
  useAsync: (...args: unknown[]) => mockUseAsync(...args),
}));

vi.mock("../../services/backend", () => ({
  abTests: { list: vi.fn() },
}));

describe("ABTesting page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("shows loading state", () => {
    mockUseAsync.mockReturnValue({ data: null, error: null, loading: true, reload: vi.fn() });
    renderWithProviders(<ABTesting />);
    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("shows empty state when no tests", () => {
    mockUseAsync.mockReturnValue({ data: [], error: null, loading: false, reload: vi.fn() });
    renderWithProviders(<ABTesting />);
    expect(screen.getByText(/No A\/B tests/)).toBeInTheDocument();
  });

  it("renders A/B tests page", () => {
    mockUseAsync.mockReturnValue({ data: [{ id: 1, name: "Title Test", status: "running" }], error: null, loading: false, reload: vi.fn() });
    renderWithProviders(<ABTesting />);
    expect(screen.getByText(/A\/B Testing/)).toBeInTheDocument();
    expect(screen.getByText("Title Test")).toBeInTheDocument();
  });
});
