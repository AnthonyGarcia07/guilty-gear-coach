export type Result = "win" | "loss";
export type MatchSort = "recently_played" | "last_updated" | "oldest_played";
export type ReplaySourceType = "replay_file" | "video" | "external_reference";

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

export interface Replay {
  id: number;
  match_id: number;
  source_type: ReplaySourceType;
  original_filename?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReplayCreateInput {
  source_type: ReplaySourceType;
  original_filename?: string | null;
}

export type ReplayUpdateInput = Partial<ReplayCreateInput>;

export interface MatchListResponse {
  items: Match[];
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  sort: MatchSort;
}

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
  total_matches: number;
  performance: {
    overall_win_rate: number | null;
    recent_5_win_rate: number | null;
    recent_10_win_rate: number | null;
    previous_10_win_rate: number | null;
    performance_trend: "improving" | "declining" | "stable" | null;
    matches_analyzed: number;
    trend_sample_size: number;
    trend_threshold: number;
  };
  streaks: {
    longest_win_streak: number;
    longest_losing_streak: number;
    current_streak_type: "win" | "loss" | null;
    current_streak_count: number;
  };
  character: {
    most_played_character: string | null;
    matches: number;
  };
  matchups: {
    minimum_sample_size: number;
    strongest_qualified_matchup: MatchupInsight | null;
    weakest_qualified_matchup: MatchupInsight | null;
    most_played_matchup: MatchupInsight | null;
    matchup_with_most_losses: MatchupInsight | null;
    matchups_needing_more_data: MatchupInsight[];
    matchup_records: MatchupInsight[];
    recent_matchup_trends: MatchupTrend[];
    best_matchup: string | null;
    worst_matchup: string | null;
  };
  patterns: {
    top_mistake: MistakePattern | null;
    overall_mistakes: MistakePattern[];
    recent_loss_mistakes: MistakePattern[];
    recent_loss_count: number;
    practice_priorities: PracticePriority[];
  };
  recommendations: CoachingRecommendation[];
}

export interface MatchupInsight {
  opponent_character: string;
  matches: number;
  wins: number;
  losses: number;
  win_rate: number;
  qualified: boolean;
}

export interface MatchupTrend {
  opponent_character: string;
  overall_win_rate: number;
  recent_win_rate: number;
  previous_win_rate: number;
  recent_matches: number;
  previous_matches: number;
  trend: "improving" | "declining" | "stable";
}

export interface MistakePattern {
  tag: string;
  count: number;
  losses_analyzed: number;
  percentage_of_recent_losses: number | null;
}

export interface PracticePriority {
  practice_next: string;
  count: number;
  losses_analyzed: number;
}

export interface CoachingRecommendation {
  type: string;
  priority: "high" | "medium" | "low";
  title: string;
  message: string;
  evidence: Record<string, unknown>;
  sample_size: number;
}
