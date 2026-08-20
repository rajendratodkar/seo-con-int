import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import Reports from "../Reports";

vi.mock("../../services/backend", () => ({
  reports: {
    weekly: vi.fn().mockResolvedValue({
      traffic: { clicks: 100, impressions: 5000 },
      opportunities: 3,
      audit: { keep: 2 },
      findings: [],
    }),
  },
}));

describe("Reports page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders reports page", async () => {
    renderWithProviders(<Reports />);
    await waitFor(() => {
      expect(screen.getByText(/SEO Audit Reports/)).toBeInTheDocument();
    });
  });
});
