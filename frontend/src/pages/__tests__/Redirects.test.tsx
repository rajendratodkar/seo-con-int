import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import Redirects from "../Redirects";

vi.mock("../../services/backend", () => ({
  redirects: {
    list: vi.fn().mockResolvedValue([]),
    stats: vi.fn().mockResolvedValue({ total: 5, active: 3, chains: 1 }),
  },
}));

describe("Redirects page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders redirects page", async () => {
    renderWithProviders(<Redirects />);
    await waitFor(() => {
      expect(screen.getByText(/Redirect Manager/)).toBeInTheDocument();
    });
  });
});
