import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Loading, ErrorBox, Empty, Badge, AiBadge } from "../common";

describe("Loading", () => {
  it("renders loading text", () => {
    render(<Loading />);
    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("has empty class", () => {
    const { container } = render(<Loading />);
    expect(container.firstChild).toHaveClass("empty");
  });
});

describe("ErrorBox", () => {
  it("renders the error message", () => {
    render(<ErrorBox message="Something went wrong" />);
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("has error-box class", () => {
    const { container } = render(<ErrorBox message="err" />);
    expect(container.firstChild).toHaveClass("error-box");
  });
});

describe("Empty", () => {
  it("renders the provided text", () => {
    render(<Empty text="No data found" />);
    expect(screen.getByText("No data found")).toBeInTheDocument();
  });

  it("has empty class", () => {
    const { container } = render(<Empty text="nothing" />);
    expect(container.firstChild).toHaveClass("empty");
  });
});

describe("Badge", () => {
  it("renders the value text", () => {
    render(<Badge value="completed" />);
    expect(screen.getByText("completed")).toBeInTheDocument();
  });

  it("applies correct tone class for known values", () => {
    const { container } = render(<Badge value="completed" />);
    expect(container.firstChild).toHaveClass("badge", "green");
  });

  it("applies gray for unknown values", () => {
    const { container } = render(<Badge value="unknown_status" />);
    expect(container.firstChild).toHaveClass("badge", "gray");
  });

  it("replaces underscores with spaces", () => {
    render(<Badge value="ai_suggestion" />);
    expect(screen.getByText("ai suggestion")).toBeInTheDocument();
  });

  it("maps critical to red", () => {
    const { container } = render(<Badge value="critical" />);
    expect(container.firstChild).toHaveClass("badge", "red");
  });

  it("maps pending to gray", () => {
    const { container } = render(<Badge value="pending" />);
    expect(container.firstChild).toHaveClass("badge", "gray");
  });
});

describe("AiBadge", () => {
  it("renders AI suggestion text", () => {
    render(<AiBadge />);
    expect(screen.getByText("AI suggestion")).toBeInTheDocument();
  });

  it("has violet badge class", () => {
    const { container } = render(<AiBadge />);
    expect(container.firstChild).toHaveClass("badge", "violet");
  });
});
