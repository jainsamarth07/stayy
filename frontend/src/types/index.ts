/**
 * @module types
 * @description TypeScript interfaces matching the backend Pydantic schemas.
 * These types are shared across the entire frontend.
 */

/** Represents an authenticated user. */
export interface User {
  id: string;
  email: string;
  full_name: string;
  phone?: string;
  role: "user" | "host" | "admin";
  is_active: boolean;
  created_at: string;
}

/** Host's public profile with business info, verification status, and rating. */
export interface HostProfile {
  id: string;
  user_id: string;
  business_name?: string;
  bio?: string;
  phone_visible: boolean;
  is_verified: boolean;
  avg_rating: number;
  total_reviews: number;
  created_at: string;
}

/** A single image attached to a property listing. */
export interface PropertyImage {
  id: string;
  image_url: string;
  is_primary: boolean;
  sort_order: number;
}

/** Hourly booking configuration for a property. */
export interface HourlyBookingConfig {
  id: string;
  hourly_price: number;
  min_hours: number;
  max_hours: number;
  available_from: string;
  available_to: string;
}

/** A rentable property listing with location, pricing, and images. */
export interface Property {
  id: string;
  host_id: string;
  title: string;
  description: string;
  city: string;
  address: string;
  latitude?: number;
  longitude?: number;
  price_per_night: number;
  max_guests: number;
  amenities?: string[];
  is_active: boolean;
  hourly_enabled: boolean;
  images: PropertyImage[];
  hourly_config?: HourlyBookingConfig;
  created_at: string;
  updated_at: string;
  /** Populated by admin endpoints */
  host_name?: string;
}

/** A confirmed or pending booking between a guest and a property. */
export interface Booking {
  id: string;
  property_id: string;
  guest_id: string;
  host_id: string;
  check_in: string;
  check_out: string;
  total_price: number;
  booking_type: "nightly" | "hourly";
  hours?: number;
  status: "pending" | "confirmed" | "cancelled" | "completed" | "rejected";
  created_at: string;
  updated_at: string;
  /** Populated by admin endpoints */
  property_title?: string;
  guest_name?: string;
}

/** A messaging conversation between a guest and a host about a property. */
export interface Conversation {
  id: string;
  property_id: string;
  guest_id: string;
  host_id: string;
  property_title?: string;
  other_party_name?: string;
  created_at: string;
  updated_at: string;
  last_message?: Message;
  unread_count: number;
}

/** A single message in a conversation. */
export interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  content: string;
  message_type: "text";
  is_read: boolean;
  created_at: string;
}

/** A guest review for a completed booking. */
export interface Review {
  id: string;
  booking_id: string;
  property_id: string;
  reviewer_id: string;
  rating: number;
  comment?: string;
  created_at: string;
}

/** Describes a membership plan tier (Basic, Pro, Premium). */
export interface MembershipPlan {
  plan_type: string;
  label: string;
  price: number;
  max_listings: number;
}

/** An active or historical host membership subscription. */
export interface Membership {
  id: string;
  host_id: string;
  plan_type: string;
  start_date: string;
  end_date: string;
  status: "active" | "cancelled" | "expired" | "past_due";
  auto_renew: boolean;
  amount: number;
  max_listings: number;
  created_at: string;
  updated_at: string;
}

/** Generic paginated API response wrapper. */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
