import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import SchemaMarkup from "../SchemaMarkup";

vi.mock("../../services/backend", () => ({
  schemas: {
    types: vi.fn().mockResolvedValue({ types: ["Article", "FAQPage", "HowTo"] }),
  },
}));

describe("SchemaMarkup page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders schema markup page", async () => {
    renderWithProviders(<SchemaMarkup />);
    await waitFor(() => {
      expect(screen.getByText(/Schema Markup Builder/)).toBeInTheDocument();
    });
  });
});
