import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import SERPABTesting from "../SERPABTesting";

vi.mock("../../services/backend", () => ({
  serpABTests: {
    list: vi.fn().mockResolvedValue([]),
    getStats: vi.fn().mockResolvedValue({ total: 0, running: 0 }),
  },
}));

describe("SERPABTesting page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders SERP A/B testing page", async () => {
    renderWithProviders(<SERPABTesting />);
    await waitFor(() => {
      expect(screen.getByText(/SERP A\/B Testing/)).toBeInTheDocument();
    });
  });
});
