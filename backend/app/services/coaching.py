from collections import Counter, defaultdict

from app.models import Match
from app.schemas.coaching import (
    CharacterInsight,
    CoachingInsights,
    MatchupInsights,
    MatchupRecord,
    MatchupTrend,
    MistakePattern,
    PatternInsights,
    PerformanceInsight,
    PracticePriority,
    Recommendation,
    StreakInsight,
    Trend,
)
from app.services import coaching_thresholds as thresholds


def build_coaching_insights(matches: list[Match]) -> CoachingInsights:
    chronological_matches = chronological(matches)
    performance = build_performance_insight(chronological_matches)
    streaks = build_streak_insight(chronological_matches)
    character = build_character_insight(chronological_matches)
    matchups = build_matchup_insights(chronological_matches)
    patterns = build_pattern_insights(chronological_matches)

    return CoachingInsights(
        total_matches=len(chronological_matches),
        performance=performance,
        streaks=streaks,
        character=character,
        matchups=matchups,
        patterns=patterns,
        recommendations=build_recommendations(performance, matchups, patterns),
    )


def chronological(matches: list[Match]) -> list[Match]:
    return sorted(matches, key=lambda match: (match.played_on, getattr(match, "id", 0)))


def build_performance_insight(matches: list[Match]) -> PerformanceInsight:
    recent_5 = matches[-thresholds.RECENT_5_MATCHES :]
    recent_10 = matches[-thresholds.RECENT_10_MATCHES :]
    previous_10 = matches[-(thresholds.RECENT_10_MATCHES + thresholds.PREVIOUS_10_MATCHES) : -thresholds.RECENT_10_MATCHES]
    recent_10_rate = win_rate(recent_10) if len(recent_10) == thresholds.RECENT_10_MATCHES else None
    previous_10_rate = win_rate(previous_10) if len(previous_10) == thresholds.PREVIOUS_10_MATCHES else None

    return PerformanceInsight(
        overall_win_rate=win_rate(matches) if matches else None,
        recent_5_win_rate=win_rate(recent_5) if len(recent_5) == thresholds.RECENT_5_MATCHES else None,
        recent_10_win_rate=recent_10_rate,
        previous_10_win_rate=previous_10_rate,
        performance_trend=trend_from_rates(recent_10_rate, previous_10_rate, thresholds.PERFORMANCE_TREND_THRESHOLD),
        matches_analyzed=len(matches),
        trend_sample_size=len(recent_10) + len(previous_10) if recent_10_rate is not None and previous_10_rate is not None else 0,
        trend_threshold=thresholds.PERFORMANCE_TREND_THRESHOLD,
    )


def build_streak_insight(matches: list[Match]) -> StreakInsight:
    longest_win_streak = 0
    longest_losing_streak = 0
    current_win_streak = 0
    current_losing_streak = 0

    for match in matches:
        if match.result == "win":
            current_win_streak += 1
            current_losing_streak = 0
        else:
            current_losing_streak += 1
            current_win_streak = 0

        longest_win_streak = max(longest_win_streak, current_win_streak)
        longest_losing_streak = max(longest_losing_streak, current_losing_streak)

    return StreakInsight(
        longest_win_streak=longest_win_streak,
        longest_losing_streak=longest_losing_streak,
        current_streak_type=current_streak_type(matches),
        current_streak_count=current_streak_count(matches),
    )


def build_character_insight(matches: list[Match]) -> CharacterInsight:
    character_counts: Counter[str] = Counter(match.player_character for match in matches)
    if not character_counts:
        return CharacterInsight(most_played_character=None, matches=0)
    character, count = character_counts.most_common(1)[0]
    return CharacterInsight(most_played_character=character, matches=count)


def build_matchup_insights(matches: list[Match]) -> MatchupInsights:
    buckets: dict[str, list[Match]] = defaultdict(list)
    for match in matches:
        buckets[match.opponent_character].append(match)

    records = sorted((matchup_record(opponent, bucket) for opponent, bucket in buckets.items()), key=lambda record: (-record.matches, record.opponent_character))
    qualified = [record for record in records if record.qualified]

    strongest = max(qualified, key=lambda record: (record.win_rate, record.matches, record.opponent_character)) if qualified else None
    weakest = min(qualified, key=lambda record: (record.win_rate, -record.matches, record.opponent_character)) if qualified else None
    most_played = max(records, key=lambda record: (record.matches, record.opponent_character)) if records else None
    most_losses = max(records, key=lambda record: (record.losses, record.matches, record.opponent_character)) if records and any(record.losses for record in records) else None

    return MatchupInsights(
        minimum_sample_size=thresholds.MIN_MATCHUP_SAMPLE,
        strongest_qualified_matchup=strongest,
        weakest_qualified_matchup=weakest,
        most_played_matchup=most_played,
        matchup_with_most_losses=most_losses,
        matchups_needing_more_data=[record for record in records if not record.qualified],
        matchup_records=records,
        recent_matchup_trends=build_matchup_trends(buckets),
        best_matchup=strongest.opponent_character if strongest else None,
        worst_matchup=weakest.opponent_character if weakest else None,
    )


def matchup_record(opponent: str, bucket: list[Match]) -> MatchupRecord:
    wins = sum(1 for match in bucket if match.result == "win")
    total = len(bucket)
    return MatchupRecord(
        opponent_character=opponent,
        matches=total,
        wins=wins,
        losses=total - wins,
        win_rate=win_rate(bucket),
        qualified=total >= thresholds.MIN_MATCHUP_SAMPLE,
    )


def build_matchup_trends(buckets: dict[str, list[Match]]) -> list[MatchupTrend]:
    trends: list[MatchupTrend] = []
    for opponent, bucket in buckets.items():
        ordered_bucket = chronological(bucket)
        if len(ordered_bucket) < thresholds.MIN_MATCHUP_TREND_TOTAL:
            continue
        recent = ordered_bucket[-thresholds.RECENT_MATCHUP_WINDOW :]
        previous = ordered_bucket[:-thresholds.RECENT_MATCHUP_WINDOW]
        if len(previous) < thresholds.RECENT_MATCHUP_WINDOW:
            continue
        recent_rate = win_rate(recent)
        previous_rate = win_rate(previous)
        trend = trend_from_rates(recent_rate, previous_rate, thresholds.MATCHUP_TREND_THRESHOLD)
        if trend is None:
            continue
        trends.append(
            MatchupTrend(
                opponent_character=opponent,
                overall_win_rate=win_rate(ordered_bucket),
                recent_win_rate=recent_rate,
                previous_win_rate=previous_rate,
                recent_matches=len(recent),
                previous_matches=len(previous),
                trend=trend,
            )
        )
    return sorted(trends, key=lambda item: (item.trend != "declining", -abs(item.recent_win_rate - item.previous_win_rate), item.opponent_character))


def build_pattern_insights(matches: list[Match]) -> PatternInsights:
    losses = [match for match in matches if match.result == "loss"]
    recent_losses = losses[-thresholds.RECENT_LOSS_WINDOW :]
    overall_mistakes = mistake_patterns(losses, losses)
    recent_loss_mistakes = mistake_patterns(recent_losses, recent_losses)

    return PatternInsights(
        top_mistake=overall_mistakes[0] if overall_mistakes else None,
        overall_mistakes=overall_mistakes[: thresholds.MAX_PATTERN_ITEMS],
        recent_loss_mistakes=recent_loss_mistakes[: thresholds.MAX_PATTERN_ITEMS],
        recent_loss_count=len(recent_losses),
        practice_priorities=practice_priorities(recent_losses)[: thresholds.MAX_PATTERN_ITEMS],
    )


def mistake_patterns(source_matches: list[Match], denominator_matches: list[Match]) -> list[MistakePattern]:
    counter: Counter[str] = Counter()
    for match in source_matches:
        counter.update(normalize_text(tag) for tag in match.mistake_tags if normalize_text(tag))

    losses_analyzed = len(denominator_matches)
    patterns = [
        MistakePattern(
            tag=tag,
            count=count,
            losses_analyzed=losses_analyzed,
            percentage_of_recent_losses=round((count / losses_analyzed) * 100, 1) if losses_analyzed else None,
        )
        for tag, count in counter.most_common()
        if count >= thresholds.MIN_REPEATED_MISTAKE_COUNT
    ]
    return sorted(patterns, key=lambda item: (-item.count, item.tag))


def practice_priorities(losses: list[Match]) -> list[PracticePriority]:
    counter: Counter[str] = Counter()
    for match in losses:
        normalized = normalize_text(match.practice_next)
        if normalized:
            counter.update([normalized])

    return [
        PracticePriority(practice_next=practice, count=count, losses_analyzed=len(losses))
        for practice, count in counter.most_common()
        if count >= thresholds.MIN_REPEATED_PRACTICE_COUNT
    ]


def build_recommendations(performance: PerformanceInsight, matchups: MatchupInsights, patterns: PatternInsights) -> list[Recommendation]:
    recommendations: list[Recommendation] = []

    if patterns.recent_loss_mistakes:
        mistake = patterns.recent_loss_mistakes[0]
        priority = "high" if mistake.count >= 4 else "medium"
        recommendations.append(
            Recommendation(
                type="repeated_mistake",
                priority=priority,
                title=f"Work on {mistake.tag}",
                message=f"{mistake.tag} appeared in {mistake.count} of your last {mistake.losses_analyzed} losses.",
                evidence={"tag": mistake.tag, "occurrences": mistake.count, "losses_analyzed": mistake.losses_analyzed},
                sample_size=mistake.losses_analyzed,
            )
        )

    weak_matchup = matchups.weakest_qualified_matchup
    if weak_matchup and weak_matchup.losses > weak_matchup.wins:
        recommendations.append(
            Recommendation(
                type="weak_matchup",
                priority="medium" if weak_matchup.matches < 6 else "high",
                title=f"Review your {weak_matchup.opponent_character} matchup",
                message=f"You are {weak_matchup.wins}-{weak_matchup.losses} against {weak_matchup.opponent_character} across {weak_matchup.matches} recorded sets.",
                evidence={"wins": weak_matchup.wins, "losses": weak_matchup.losses, "matches": weak_matchup.matches},
                sample_size=weak_matchup.matches,
            )
        )

    if performance.performance_trend == "declining" and performance.recent_10_win_rate is not None and performance.previous_10_win_rate is not None:
        recommendations.append(
            Recommendation(
                type="performance_trend",
                priority="medium",
                title="Recent results are trending downward",
                message="Your recent 10-match win rate is lower than the previous 10-match window.",
                evidence={"recent_win_rate": performance.recent_10_win_rate, "previous_win_rate": performance.previous_10_win_rate},
                sample_size=performance.trend_sample_size,
            )
        )

    if patterns.practice_priorities:
        practice = patterns.practice_priorities[0]
        recommendations.append(
            Recommendation(
                type="practice_priority",
                priority="low" if practice.count == 2 else "medium",
                title=f"Repeat practice focus: {practice.practice_next}",
                message=f"{practice.practice_next} appeared as your practice focus in {practice.count} recent losses.",
                evidence={"practice_next": practice.practice_next, "occurrences": practice.count, "losses_analyzed": practice.losses_analyzed},
                sample_size=practice.losses_analyzed,
            )
        )

    for trend in matchups.recent_matchup_trends:
        if trend.trend != "improving":
            continue
        recommendations.append(
            Recommendation(
                type="matchup_improvement",
                priority="low",
                title=f"Keep building the {trend.opponent_character} matchup",
                message=f"Your recent win rate against {trend.opponent_character} improved from {trend.previous_win_rate}% to {trend.recent_win_rate}%.",
                evidence={
                    "opponent_character": trend.opponent_character,
                    "recent_win_rate": trend.recent_win_rate,
                    "previous_win_rate": trend.previous_win_rate,
                },
                sample_size=trend.recent_matches + trend.previous_matches,
            )
        )

    priority_order = {"high": 0, "medium": 1, "low": 2}
    type_order = {
        "repeated_mistake": 0,
        "performance_trend": 1,
        "weak_matchup": 2,
        "practice_priority": 3,
        "matchup_improvement": 4,
    }
    return sorted(recommendations, key=lambda item: (priority_order[item.priority], type_order.get(item.type, 99), -item.sample_size))[: thresholds.MAX_RECOMMENDATIONS]


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


def win_rate(matches: list[Match]) -> float:
    if not matches:
        return 0
    wins = sum(1 for match in matches if match.result == "win")
    return round((wins / len(matches)) * 100, 1)


def trend_from_rates(recent_rate: float | None, previous_rate: float | None, threshold: float) -> Trend | None:
    if recent_rate is None or previous_rate is None:
        return None
    difference = recent_rate - previous_rate
    if difference >= threshold:
        return "improving"
    if difference <= -threshold:
        return "declining"
    return "stable"


def normalize_text(value: str | None) -> str:
    return " ".join(value.strip().lower().split()) if value else ""
