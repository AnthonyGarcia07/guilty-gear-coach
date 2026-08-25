import type {
  AuthResponse,
  CoachingInsights,
  DashboardStats,
  Match,
  MatchInput,
  MatchListResponse,
  MatchSort,
  Replay,
  ReplayCreateInput,
  ReplayDownloadUrlResponse,
  ReplayUpdateInput,
  ReplayUploadConfirmResponse,
  ReplayUploadInitInput,
  ReplayUploadInitResponse,
  User
} from "../types";
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
  listMatches: (params: { page?: number; page_size?: number; sort?: MatchSort } = {}) => {
    const search = new URLSearchParams();
    if (params.page) search.set("page", String(params.page));
    if (params.page_size) search.set("page_size", String(params.page_size));
    if (params.sort) search.set("sort", params.sort);
    const query = search.toString();
    return request<MatchListResponse>(`/matches${query ? `?${query}` : ""}`);
  },
  getMatch: (id: string) => request<Match>(`/matches/${id}`),
  createMatch: (payload: MatchInput) => request<Match>("/matches", { method: "POST", body: JSON.stringify(payload) }),
  updateMatch: (id: number, payload: Partial<MatchInput>) =>
    request<Match>(`/matches/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteMatch: (id: number) => request<void>(`/matches/${id}`, { method: "DELETE" }),
  listReplays: (matchId: number) => request<Replay[]>(`/matches/${matchId}/replays`),
  createReplay: (matchId: number, payload: ReplayCreateInput) =>
    request<Replay>(`/matches/${matchId}/replays`, { method: "POST", body: JSON.stringify(payload) }),
  updateReplay: (matchId: number, replayId: number, payload: ReplayUpdateInput) =>
    request<Replay>(`/matches/${matchId}/replays/${replayId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteReplay: (matchId: number, replayId: number) => request<void>(`/matches/${matchId}/replays/${replayId}`, { method: "DELETE" }),
  initializeReplayUpload: (matchId: number, payload: ReplayUploadInitInput) =>
    request<ReplayUploadInitResponse>(`/matches/${matchId}/replays/uploads`, { method: "POST", body: JSON.stringify(payload) }),
  confirmReplayUpload: (matchId: number, replayId: number) =>
    request<ReplayUploadConfirmResponse>(`/matches/${matchId}/replays/${replayId}/confirm-upload`, { method: "POST" }),
  getReplayDownloadUrl: (matchId: number, replayId: number) =>
    request<ReplayDownloadUrlResponse>(`/matches/${matchId}/replays/${replayId}/download-url`, { method: "POST" })
};

export async function uploadReplayFileToStorage(uploadUrl: string, file: File) {
  const response = await fetch(uploadUrl, {
    method: "PUT",
    headers: {
      "Content-Type": "video/mp4"
    },
    body: file
  });

  if (!response.ok) {
    throw new Error("Unable to upload MP4 to storage.");
  }
}
