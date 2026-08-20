import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import KeywordClusters from "../KeywordClusters";

vi.mock("../../services/backend", () => ({
  keywordClusters: { list: vi.fn().mockResolvedValue([]) },
}));

describe("KeywordClusters page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders clusters page", async () => {
    renderWithProviders(<KeywordClusters />);
    await waitFor(() => {
      expect(screen.getByText(/Keyword Clusters/)).toBeInTheDocument();
    });
  });
});
