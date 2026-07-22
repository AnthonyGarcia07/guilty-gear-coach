import type { AuthResponse, CoachingInsights, DashboardStats, Match, MatchInput, User } from "../types";
import { ApiError, normalizeErrorResponse } from "./errors";

const API_URL = (import.meta.env.VITE_API_URL || "/api").replace(/\/$/, "");

export { ApiError } from "./errors";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("ggc_token");
  const customHeaders = (options.headers ?? {}) as Record<string, string>;
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...customHeaders
    }
  });

  if (!response.ok) {
    const parsed = await normalizeErrorResponse(response);
    throw new ApiError(response.status, parsed.message, parsed.fieldErrors);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const api = {
  signup: (payload: { email: string; username: string; password: string }) =>
    request<AuthResponse>("/auth/signup", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload: { email: string; password: string }) =>
    request<AuthResponse>("/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  me: () => request<User>("/users/me"),
  stats: () => request<DashboardStats>("/stats/dashboard"),
  coachingInsights: () => request<CoachingInsights>("/coaching/insights"),
  listMatches: () => request<Match[]>("/matches"),
  getMatch: (id: string) => request<Match>(`/matches/${id}`),
  createMatch: (payload: MatchInput) => request<Match>("/matches", { method: "POST", body: JSON.stringify(payload) }),
  updateMatch: (id: number, payload: Partial<MatchInput>) =>
    request<Match>(`/matches/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteMatch: (id: number) => request<void>(`/matches/${id}`, { method: "DELETE" })
};
