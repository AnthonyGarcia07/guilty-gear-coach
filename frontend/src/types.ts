export type Result = "win" | "loss";

export interface User {
  id: number;
  email: string;
  username: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Match {
  id: number;
  player_character: string;
  opponent_character: string;
  result: Result;
  played_on: string;
  rank_floor?: string | null;
  duration_seconds?: number | null;
  rounds_won?: number | null;
  rounds_lost?: number | null;
  first_to?: number | null;
  notes?: string | null;
  mistake_tags: string[];
  strength_tags: string[];
  reason_for_loss?: string | null;
  practice_next?: string | null;
  replay_filename?: string | null;
  created_at: string;
  updated_at: string;
}

export type MatchInput = Omit<Match, "id" | "created_at" | "updated_at">;

export interface CharacterWinRate {
  opponent_character: string;
  matches: number;
  wins: number;
  win_rate: number;
}

export interface TagCount {
  label: string;
  count: number;
}

export interface DashboardStats {
  total_matches: number;
  wins: number;
  losses: number;
  win_rate: number;
  win_rate_by_opponent: CharacterWinRate[];
  most_common_mistake_tags: TagCount[];
  most_common_reason_for_loss: TagCount | null;
  recent_matches: Match[];
}

export interface CoachingInsights {
  overallWinRate: number;
  longest_win_streak: number;
  longest_losing_streak: number;
  current_streak_type: "win" | "loss" | null;
  current_streak_count: number;
  mostPlayedCharacter: string | null;
  bestMatchup: string | null;
  worstMatchup: string | null;
  totalMatches: number;
}
