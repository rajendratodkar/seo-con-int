import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import ContentBriefs from "../ContentBriefs";

vi.mock("../../services/backend", () => ({
  contentBriefs: {
    list: vi.fn().mockResolvedValue([]),
  },
}));

describe("ContentBriefs page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("shows empty state when no website", () => {
    renderWithProviders(<ContentBriefs />, { store: { active: null } });
    expect(screen.getByText("Add a website first.")).toBeInTheDocument();
  });

  it("renders content briefs page", async () => {
    renderWithProviders(<ContentBriefs />);
    await waitFor(() => {
      expect(screen.getByText(/Content Briefs/)).toBeInTheDocument();
    });
  });
});
