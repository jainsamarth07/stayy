/** Unit tests for the {@link Modal} component. */
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import Modal from "@/components/ui/modal";

describe("Modal", () => {
  it("does not render when isOpen is false", () => {
    render(
      <Modal isOpen={false} onClose={vi.fn()} title="Test">
        <p>Content</p>
      </Modal>
    );
    expect(screen.queryByText("Test")).not.toBeInTheDocument();
  });

  it("renders when isOpen is true", () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()} title="Test Modal">
        <p>Modal content</p>
      </Modal>
    );
    expect(screen.getByText("Test Modal")).toBeInTheDocument();
    expect(screen.getByText("Modal content")).toBeInTheDocument();
  });

  it("calls onClose when close button is clicked", () => {
    const onClose = vi.fn();
    render(
      <Modal isOpen={true} onClose={onClose} title="Close me">
        <p>Body</p>
      </Modal>
    );
    const closeBtn = screen.getByLabelText("Close");
    fireEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when backdrop is clicked", () => {
    const onClose = vi.fn();
    render(
      <Modal isOpen={true} onClose={onClose} title="Backdrop test">
        <p>Body</p>
      </Modal>
    );
    const backdrop = screen.getByTestId("modal-backdrop");
    fireEvent.click(backdrop);
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
