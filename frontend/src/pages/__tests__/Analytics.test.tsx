import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import Analytics from "../Analytics";

vi.mock("../../services/backend", () => ({
  reports: {
    analyticsOverview: vi.fn().mockResolvedValue({}),
    trafficTrend: vi.fn().mockResolvedValue([]),
    rankingDistribution: vi.fn().mockResolvedValue({ top_3: 0, pos_4_10: 0, pos_11_20: 0, pos_21_plus: 0 }),
    topPages: vi.fn().mockResolvedValue([]),
    topQueries: vi.fn().mockResolvedValue([]),
  },
}));

describe("Analytics page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders analytics page", async () => {
    renderWithProviders(<Analytics />);
    await waitFor(() => {
      expect(screen.getByText(/Analytics/)).toBeInTheDocument();
    });
  });
});
