import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import ContentRewriter from "../ContentRewriter";

vi.mock("../../services/backend", () => ({
  rewriter: {
    history: vi.fn().mockResolvedValue([]),
  },
}));

describe("ContentRewriter page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders rewriter page", async () => {
    renderWithProviders(<ContentRewriter />);
    await waitFor(() => {
      expect(screen.getByText(/Content Rewriter/)).toBeInTheDocument();
    });
  });
});
