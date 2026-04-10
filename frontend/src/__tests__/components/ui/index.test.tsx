/** Unit tests for shared UI primitives (Badge, Avatar, Spinner, Card). */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Badge, Avatar, Spinner, Card } from "@/components/ui/index";

describe("Badge", () => {
  it("renders text", () => {
    render(<Badge>Active</Badge>);
    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("applies success variant", () => {
    render(<Badge variant="success">Online</Badge>);
    expect(screen.getByText("Online").className).toContain("green");
  });

  it("applies error variant", () => {
    render(<Badge variant="error">Failed</Badge>);
    expect(screen.getByText("Failed").className).toContain("red");
  });
});

describe("Avatar", () => {
  it("renders fallback initials when no src", () => {
    render(<Avatar fallback="John Doe" />);
    expect(screen.getByText("JD")).toBeInTheDocument();
  });

  it("renders image when src is provided", () => {
    render(<Avatar src="https://example.com/pic.jpg" fallback="Jane" />);
    const img = screen.getByRole("img");
    expect(img).toBeInTheDocument();
  });
});

describe("Spinner", () => {
  it("renders an animated element", () => {
    const { container } = render(<Spinner />);
    const spinner = container.querySelector(".animate-spin");
    expect(spinner).toBeInTheDocument();
  });
});

describe("Card", () => {
  it("renders children", () => {
    render(<Card><p>Card content</p></Card>);
    expect(screen.getByText("Card content")).toBeInTheDocument();
  });
});
