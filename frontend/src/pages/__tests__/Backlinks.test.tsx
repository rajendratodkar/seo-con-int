import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import Backlinks from "../Backlinks";

vi.mock("../../services/backend", () => ({
  backlinks: {
    list: vi.fn().mockResolvedValue([]),
    profile: vi.fn().mockResolvedValue({ total_links: 0, active_links: 0, domains: 0 }),
    changes: vi.fn().mockResolvedValue([]),
  },
}));

describe("Backlinks page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders backlinks page", async () => {
    renderWithProviders(<Backlinks />);
    await waitFor(() => {
      expect(screen.getByText(/Backlink Monitor/)).toBeInTheDocument();
    });
  });
});
