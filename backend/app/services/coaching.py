from collections import Counter, defaultdict

from app.models import Match
from app.schemas.coaching import CoachingInsights


def build_coaching_insights(matches: list[Match]) -> CoachingInsights:
    chronological_matches = sorted(matches, key=lambda match: (match.played_on, getattr(match, "id", 0)))
    total = len(chronological_matches)
    wins = sum(1 for match in chronological_matches if match.result == "win")
    longest_win_streak = 0
    longest_losing_streak = 0
    current_win_streak = 0
    current_losing_streak = 0
    character_counts: Counter[str] = Counter()
    matchup_buckets: dict[str, list[Match]] = defaultdict(list)

    for match in chronological_matches:
        character_counts.update([match.player_character])
        matchup_buckets[match.opponent_character].append(match)

        if match.result == "win":
            current_win_streak += 1
            current_losing_streak = 0
        else:
            current_losing_streak += 1
            current_win_streak = 0

        longest_win_streak = max(longest_win_streak, current_win_streak)
        longest_losing_streak = max(longest_losing_streak, current_losing_streak)

    matchup_rates = []
    for opponent, bucket in matchup_buckets.items():
        matchup_wins = sum(1 for match in bucket if match.result == "win")
        matchup_rates.append((opponent, matchup_wins / len(bucket), len(bucket)))

    best_matchup = max(matchup_rates, key=lambda item: (item[1], item[2], item[0]))[0] if matchup_rates else None
    worst_matchup = min(matchup_rates, key=lambda item: (item[1], -item[2], item[0]))[0] if matchup_rates else None
    most_played_character = character_counts.most_common(1)[0][0] if character_counts else None

    return CoachingInsights(
        overallWinRate=round((wins / total) * 100, 1) if total else 0,
        longest_win_streak=longest_win_streak,
        longest_losing_streak=longest_losing_streak,
        current_streak_type=current_streak_type(chronological_matches),
        current_streak_count=current_streak_count(chronological_matches),
        mostPlayedCharacter=most_played_character,
        bestMatchup=best_matchup,
        worstMatchup=worst_matchup,
        totalMatches=total,
    )


def current_streak_type(matches: list[Match]) -> str | None:
    if not matches:
        return None
    return matches[-1].result


def current_streak_count(matches: list[Match]) -> int:
    if not matches:
        return 0
    latest_result = matches[-1].result
    streak = 0
    for match in reversed(matches):
        if match.result != latest_result:
            break
        streak += 1
    return streak
