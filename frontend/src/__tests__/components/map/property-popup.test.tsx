/**
 * @module property-popup.test
 * @description Tests for the PropertyPopup map card component.
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import PropertyPopup from "@/components/property/map/property-popup";
import type { Property } from "@/types";

const mockProperty: Property = {
  id: "prop-1",
  host_id: "host-1",
  title: "Cozy Beach House",
  description: "A beautiful beachfront property with stunning ocean views and modern amenities.",
  city: "Goa",
  address: "123 Beach Road, Panaji",
  latitude: 15.4909,
  longitude: 73.8278,
  price_per_night: 3500,
  max_guests: 4,
  amenities: ["WiFi", "Pool"],
  is_active: true,
  hourly_enabled: false,
  images: [
    { id: "img-1", image_url: "/test-image.jpg", is_primary: true, sort_order: 0 },
  ],
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const mockPropertyHourly: Property = {
  ...mockProperty,
  id: "prop-2",
  hourly_enabled: true,
  hourly_config: {
    id: "hc-1",
    hourly_price: 500,
    min_hours: 1,
    max_hours: 8,
    available_from: "08:00",
    available_to: "22:00",
  },
};

describe("PropertyPopup", () => {
  it("renders property title, city, and price", () => {
    render(<PropertyPopup property={mockProperty} onClose={vi.fn()} />);

    expect(screen.getByText("Cozy Beach House")).toBeInTheDocument();
    expect(screen.getByText(/Goa/)).toBeInTheDocument();
    expect(screen.getByText("₹3,500")).toBeInTheDocument();
    expect(screen.getByText("night")).toBeInTheDocument();
  });

  it("renders description (truncated)", () => {
    render(<PropertyPopup property={mockProperty} onClose={vi.fn()} />);

    expect(screen.getByText(/beautiful beachfront/)).toBeInTheDocument();
  });

  it("renders guest count", () => {
    render(<PropertyPopup property={mockProperty} onClose={vi.fn()} />);

    expect(screen.getByText(/Up to 4 guests/)).toBeInTheDocument();
  });

  it("renders the property image", () => {
    render(<PropertyPopup property={mockProperty} onClose={vi.fn()} />);

    const img = screen.getByAltText("Cozy Beach House");
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute("src", "/test-image.jpg");
  });

  it("renders placeholder when no images", () => {
    const noImg = { ...mockProperty, images: [] };
    render(<PropertyPopup property={noImg} onClose={vi.fn()} />);

    const img = screen.getByAltText("Cozy Beach House");
    expect(img).toHaveAttribute("src", "/placeholder-property.svg");
  });

  it("shows hourly badge and hourly price when enabled", () => {
    render(<PropertyPopup property={mockPropertyHourly} onClose={vi.fn()} />);

    expect(screen.getByText("Hourly")).toBeInTheDocument();
    expect(screen.getByText(/₹500\/hr/)).toBeInTheDocument();
  });

  it("does not show hourly badge when disabled", () => {
    render(<PropertyPopup property={mockProperty} onClose={vi.fn()} />);

    expect(screen.queryByText("Hourly")).not.toBeInTheDocument();
  });

  it("calls onClose when close button clicked", () => {
    const onClose = vi.fn();
    render(<PropertyPopup property={mockProperty} onClose={onClose} />);

    fireEvent.click(screen.getByLabelText("Close popup"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("links to the property detail page", () => {
    render(<PropertyPopup property={mockProperty} onClose={vi.fn()} />);

    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/properties/prop-1");
  });

  it("has the correct test id", () => {
    render(<PropertyPopup property={mockProperty} onClose={vi.fn()} />);

    expect(screen.getByTestId("property-popup")).toBeInTheDocument();
  });
});
