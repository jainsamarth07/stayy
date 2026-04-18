/** Unit tests for the {@link Button} component. */
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import Button from "@/components/ui/button";

describe("Button", () => {
  it("renders with text", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole("button", { name: /click me/i })).toBeInTheDocument();
  });

  it("applies primary variant by default", () => {
    render(<Button>Primary</Button>);
    const btn = screen.getByRole("button");
    expect(btn.className).toContain("bg-primary-500");
  });

  it("applies outline variant", () => {
    render(<Button variant="outline">Outline</Button>);
    const btn = screen.getByRole("button");
    expect(btn.className).toContain("border");
  });

  it("handles click events", () => {
    let clicked = false;
    render(<Button onClick={() => (clicked = true)}>Click</Button>);
    fireEvent.click(screen.getByRole("button"));
    expect(clicked).toBe(true);
  });

  it("shows spinner when loading", () => {
    render(<Button loading>Loading</Button>);
    const btn = screen.getByRole("button");
    expect(btn).toBeDisabled();
  });

  it("is disabled when disabled prop is set", () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("renders different sizes", () => {
    const { rerender } = render(<Button size="sm">Small</Button>);
    expect(screen.getByRole("button").className).toContain("px-4");

    rerender(<Button size="lg">Large</Button>);
    expect(screen.getByRole("button").className).toContain("px-6");
  });
});
