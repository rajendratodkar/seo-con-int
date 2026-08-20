import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import PageSpeed from "../PageSpeed";

vi.mock("../../services/backend", () => ({
  pageSpeed: { summary: vi.fn().mockResolvedValue({}) },
}));

describe("PageSpeed page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders page speed page", async () => {
    renderWithProviders(<PageSpeed />);
    await waitFor(() => {
      expect(screen.getByText(/Page Speed Insights/)).toBeInTheDocument();
    });
  });
});
