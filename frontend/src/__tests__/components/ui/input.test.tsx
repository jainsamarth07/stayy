/** Unit tests for the {@link Input} component. */
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import Input from "@/components/ui/input";

describe("Input", () => {
  it("renders with label", () => {
    render(<Input label="Email" />);
    expect(screen.getByText("Email")).toBeInTheDocument();
  });

  it("renders an input element", () => {
    render(<Input label="Name" placeholder="Your name" />);
    expect(screen.getByPlaceholderText("Your name")).toBeInTheDocument();
  });

  it("shows error message", () => {
    render(<Input label="Email" error="Email is required" />);
    expect(screen.getByText("Email is required")).toBeInTheDocument();
  });

  it("shows helper text", () => {
    render(<Input label="Password" helperText="Must be 8+ characters" />);
    expect(screen.getByText("Must be 8+ characters")).toBeInTheDocument();
  });

  it("calls onChange handler", () => {
    const onChange = vi.fn();
    render(<Input label="Test" onChange={onChange} />);
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "hello" } });
    expect(onChange).toHaveBeenCalled();
  });

  it("applies error styling when error is present", () => {
    render(<Input label="Email" error="Required" />);
    const input = screen.getByRole("textbox");
    expect(input.className).toContain("border-red");
  });
});
