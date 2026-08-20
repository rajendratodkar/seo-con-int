import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import RankTracker from "../RankTracker";

vi.mock("../../services/backend", () => ({
  rankTracker: {
    listKeywords: vi.fn().mockResolvedValue([]),
    getStats: vi.fn().mockResolvedValue({ total_keywords: 0, improved: 0, declined: 0 }),
    getTrends: vi.fn().mockResolvedValue([]),
    getAlerts: vi.fn().mockResolvedValue([]),
  },
}));

describe("RankTracker page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders rank tracker page", async () => {
    renderWithProviders(<RankTracker />);
    await waitFor(() => {
      expect(screen.getByText(/Rank Tracker/)).toBeInTheDocument();
    });
  });
});
