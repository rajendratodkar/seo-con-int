import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import SitemapGenerator from "../SitemapGenerator";

vi.mock("../../services/backend", () => ({
  sitemapGen: {
    settings: vi.fn().mockResolvedValue({}),
    overrides: vi.fn().mockResolvedValue([]),
  },
}));

describe("SitemapGenerator page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders sitemap generator page", async () => {
    renderWithProviders(<SitemapGenerator />);
    await waitFor(() => {
      expect(screen.getByText(/Sitemap Generator/)).toBeInTheDocument();
    });
  });
});
