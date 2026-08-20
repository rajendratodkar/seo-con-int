import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import SERPPreview from "../SERPPreview";

vi.mock("../../services/backend", () => ({
  serpPreview: {
    bulkScore: vi.fn().mockResolvedValue({ items: [], average_score: 0, total_pages: 0 }),
  },
}));

describe("SERPPreview page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders SERP preview page", async () => {
    renderWithProviders(<SERPPreview />);
    await waitFor(() => {
      expect(screen.getByText(/SERP Preview/)).toBeInTheDocument();
    });
  });
});
