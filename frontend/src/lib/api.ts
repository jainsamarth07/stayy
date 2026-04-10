/**
 * API client for StayNest backend.
 *
 * Handles JWT token management and request/response interceptors.
 */

import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "@/stores/auth-store";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// Request interceptor — attach BetterAuth session token as Bearer
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    const { sessionToken } = useAuthStore.getState();
    if (sessionToken) {
      config.headers.Authorization = `Bearer ${sessionToken}`;
    }
  }
  return config;
});

// Response interceptor — redirect to login on 401 (avoid infinite loop)
api.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    const axiosError = error as { response?: { status: number } };
    if (
      axiosError.response?.status === 401 &&
      typeof window !== "undefined" &&
      !window.location.pathname.startsWith("/auth/")
    ) {
      window.location.href = "/auth/login";
    }
    return Promise.reject(error);
  }
);

export default api;

/**
 * Extract a human-readable error message from an Axios error or generic error.
 */
export function getApiError(err: unknown): string {
  if (err && typeof err === "object" && "response" in err) {
    const axiosErr = err as { response?: { data?: { detail?: string } } };
    const detail = axiosErr.response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  if (err instanceof Error) return err.message;
  return "An unexpected error occurred";
}

// ---------- Profile (non-auth user profile data) ----------
/** Profile API methods — auth itself is handled by BetterAuth. */
export const profileApi = {
  get: () => api.get("/auth/me"),
  update: (data: { full_name?: string; phone?: string }) =>
    api.put("/auth/me", data),
};

// ---------- Properties ----------
/** Property CRUD, image upload, and hourly-config API methods. */
export const propertyApi = {
  search: (params?: Record<string, unknown>) =>
    api.get("/properties", { params }),

  getById: (id: string) => api.get(`/properties/${id}`),

  create: (data: Record<string, unknown>) => api.post("/properties", data),

  update: (id: string, data: Record<string, unknown>) =>
    api.put(`/properties/${id}`, data),

  delete: (id: string) => api.delete(`/properties/${id}`),

  uploadImage: (id: string, file: File, isPrimary = false) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post(`/properties/${id}/images?is_primary=${isPrimary}`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  configureHourly: (id: string, data: Record<string, unknown>) =>
    api.put(`/properties/${id}/hourly`, data),
};

// ---------- Bookings ----------
/** Booking lifecycle API methods (create, list, status, cancel). */
export const bookingApi = {
  create: (data: Record<string, unknown>) => api.post("/bookings", data),
  list: (page = 1) => api.get("/bookings", { params: { page } }),
  getById: (id: string) => api.get(`/bookings/${id}`),
  updateStatus: (id: string, status: string) =>
    api.put(`/bookings/${id}/status`, { status }),
  cancel: (id: string) => api.post(`/bookings/${id}/cancel`),
};

// ---------- Messaging ----------
/** Messaging API methods for conversations and messages. */
export const messageApi = {
  startConversation: (data: { property_id: string; message: string }) =>
    api.post("/conversations", data),
  listConversations: (page = 1) =>
    api.get("/conversations", { params: { page } }),
  getConversation: (conversationId: string) =>
    api.get(`/conversations/${conversationId}`),
  getMessages: (conversationId: string, page = 1) =>
    api.get(`/conversations/${conversationId}/messages`, { params: { page } }),
  sendMessage: (conversationId: string, content: string) =>
    api.post(`/conversations/${conversationId}/messages`, { content }),
  markRead: (messageId: string) => api.put(`/messages/${messageId}/read`),
};

// ---------- Reviews ----------
/** Review submission and retrieval API methods. */
export const reviewApi = {
  create: (data: { booking_id: string; rating: number; comment?: string }) =>
    api.post("/reviews", data),
  listByProperty: (propertyId: string, page = 1) =>
    api.get(`/reviews/property/${propertyId}`, { params: { page } }),
  hostReviews: (page = 1) =>
    api.get("/reviews/host", { params: { page } }),
};

// ---------- Memberships ----------
/** Membership plan browsing, subscription, and cancellation API methods. */
export const membershipApi = {
  getPlans: () => api.get("/memberships/plans"),
  subscribe: (planType: string, paymentToken: string) =>
    api.post("/memberships/subscribe", {
      plan_type: planType,
      payment_token: paymentToken,
    }),
  getCurrent: () => api.get("/memberships/current"),
  cancel: () => api.put("/memberships/cancel"),
};

// ---------- Admin ----------
/** Admin dashboard and management API methods. */
export const adminApi = {
  dashboard: () => api.get("/admin/dashboard"),
  listUsers: (page = 1) => api.get("/admin/users", { params: { page } }),
  listProperties: (page = 1) =>
    api.get("/admin/properties", { params: { page } }),
  listBookings: (page = 1) =>
    api.get("/admin/bookings", { params: { page } }),
  listMemberships: (page = 1) =>
    api.get("/admin/memberships", { params: { page } }),
  toggleUserStatus: (userId: string) =>
    api.put(`/admin/users/${userId}/status`),
};
