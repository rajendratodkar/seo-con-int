import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import Competitors from "../Competitors";

// Mock backend APIs directly — no useAsync mock needed
vi.mock("../../services/backend", () => ({
  competitors: {
    list: vi.fn().mockResolvedValue([]),
    gapStats: vi.fn().mockResolvedValue({ total_gaps: 0, new_content: 0, improve_existing: 0, quick_win: 0 }),
  },
}));

describe("Competitors page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders competitors page", async () => {
    renderWithProviders(<Competitors />);
    await waitFor(() => {
      expect(screen.getByText(/Competitor Analysis/)).toBeInTheDocument();
    });
  });

  it("shows empty state when no competitors", async () => {
    renderWithProviders(<Competitors />);
    await waitFor(() => {
      expect(screen.getByText(/No competitors/)).toBeInTheDocument();
    });
  });
});
