import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../../test-utils";
import ContentCalendar from "../ContentCalendar";

vi.mock("../../services/backend", () => ({
  calendar: {
    list: vi.fn().mockResolvedValue([]),
    pipeline: vi.fn().mockResolvedValue({}),
  },
}));

describe("ContentCalendar page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders calendar page", async () => {
    renderWithProviders(<ContentCalendar />);
    await waitFor(() => {
      expect(screen.getByText(/Content Calendar/)).toBeInTheDocument();
    });
  });
});
