import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import Monitoring from "../Monitoring";

vi.mock("../../services/backend", () => ({
  monitoring: {
    channels: vi.fn().mockResolvedValue([]),
    rules: vi.fn().mockResolvedValue([]),
    history: vi.fn().mockResolvedValue([]),
    stats: vi.fn().mockResolvedValue({ total_alerts: 0, active_rules: 0 }),
  },
}));

describe("Monitoring page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders monitoring page", async () => {
    renderWithProviders(<Monitoring />);
    await waitFor(() => {
      expect(screen.getByText(/Monitoring & Alerts/)).toBeInTheDocument();
    });
  });
});
