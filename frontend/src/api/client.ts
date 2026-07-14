import type { AuthResponse, DashboardStats, Match, MatchInput, User } from "../types";

const API_URL = (import.meta.env.VITE_API_URL || "/api").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

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
    const body = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new ApiError(response.status, body.detail ?? "Request failed");
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
  listMatches: () => request<Match[]>("/matches"),
  getMatch: (id: string) => request<Match>(`/matches/${id}`),
  createMatch: (payload: MatchInput) => request<Match>("/matches", { method: "POST", body: JSON.stringify(payload) }),
  updateMatch: (id: number, payload: Partial<MatchInput>) =>
    request<Match>(`/matches/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteMatch: (id: number) => request<void>(`/matches/${id}`, { method: "DELETE" })
};
