import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import SEOChecklist from "../SEOChecklist";

vi.mock("../../services/backend", () => ({
  seoChecklist: { list: vi.fn().mockResolvedValue([]) },
}));

describe("SEOChecklist page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders checklist page", async () => {
    renderWithProviders(<SEOChecklist />);
    await waitFor(() => {
      expect(screen.getByText(/SEO Checklist/)).toBeInTheDocument();
    });
  });
});
