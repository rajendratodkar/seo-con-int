import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import ContentRefresh from "../ContentRefresh";

vi.mock("../../services/backend", () => ({
  contentRefresh: {
    stats: vi.fn().mockResolvedValue({ pending: 0, in_progress: 0, completed: 0, skipped: 0, avg_priority: 0 }),
    listSchedules: vi.fn().mockResolvedValue([]),
    listRules: vi.fn().mockResolvedValue([]),
    history: vi.fn().mockResolvedValue([]),
  },
}));

describe("ContentRefresh page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("shows empty state when no website", () => {
    renderWithProviders(<ContentRefresh />, { store: { active: null } });
    expect(screen.getByText("Add a website first.")).toBeInTheDocument();
  });

  it("renders content refresh page", async () => {
    renderWithProviders(<ContentRefresh />);
    await waitFor(() => {
      expect(screen.getByText(/Content Refresh/)).toBeInTheDocument();
    });
  });
});
