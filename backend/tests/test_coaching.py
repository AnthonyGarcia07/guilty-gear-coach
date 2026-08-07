from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

from app.services.coaching import build_coaching_insights


def make_match(
    result: str,
    match_id: int,
    *,
    player: str = "Bridget",
    opponent: str = "Ky Kiske",
    played_on: date | None = None,
    owner_id: int = 1,
    mistakes: list[str] | None = None,
    practice_next: str | None = None,
):
    played_on = played_on or date(2026, 7, 1) + timedelta(days=match_id)
    return SimpleNamespace(
        id=match_id,
        owner_id=owner_id,
        player_character=player,
        opponent_character=opponent,
        result=result,
        played_on=played_on,
        rank_floor="Gold",
        duration_seconds=120,
        rounds_won=None,
        rounds_lost=None,
        first_to=None,
        notes=None,
        mistake_tags=mistakes or [],
        strength_tags=[],
        reason_for_loss=None,
        practice_next=practice_next,
        replay_filename=None,
        created_at=datetime(2026, 7, 1, tzinfo=timezone.utc) + timedelta(days=match_id),
        updated_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
    )


def results_history(results: list[str]):
    return [make_match(result, index + 1) for index, result in enumerate(results)]


def test_recent_5_and_recent_10_performance_windows():
    insights = build_coaching_insights(results_history(["loss"] * 5 + ["win"] * 5))

    assert insights.performance.overall_win_rate == 50.0
    assert insights.performance.recent_5_win_rate == 100.0
    assert insights.performance.recent_10_win_rate == 50.0
    assert insights.performance.previous_10_win_rate is None
    assert insights.performance.performance_trend is None


def test_previous_vs_recent_trend_improving():
    insights = build_coaching_insights(results_history(["loss"] * 6 + ["win"] * 4 + ["win"] * 8 + ["loss"] * 2))

    assert insights.performance.previous_10_win_rate == 40.0
    assert insights.performance.recent_10_win_rate == 80.0
    assert insights.performance.performance_trend == "improving"


def test_previous_vs_recent_trend_declining():
    insights = build_coaching_insights(results_history(["win"] * 8 + ["loss"] * 2 + ["loss"] * 7 + ["win"] * 3))

    assert insights.performance.previous_10_win_rate == 80.0
    assert insights.performance.recent_10_win_rate == 30.0
    assert insights.performance.performance_trend == "declining"


def test_previous_vs_recent_trend_stable_inside_threshold():
    insights = build_coaching_insights(results_history(["win"] * 5 + ["loss"] * 5 + ["win"] * 6 + ["loss"] * 4))

    assert insights.performance.previous_10_win_rate == 50.0
    assert insights.performance.recent_10_win_rate == 60.0
    assert insights.performance.performance_trend == "stable"


def test_insufficient_history_does_not_claim_trend():
    insights = build_coaching_insights(results_history(["win", "loss", "win", "loss"]))

    assert insights.performance.recent_5_win_rate is None
    assert insights.performance.recent_10_win_rate is None
    assert insights.performance.previous_10_win_rate is None
    assert insights.performance.performance_trend is None


def test_repeated_mistake_detection_uses_loss_tags():
    matches = [
        make_match("loss", 1, mistakes=["missed anti-air", "meter spend"]),
        make_match("loss", 2, mistakes=[" missed anti-air "]),
        make_match("win", 3, mistakes=["missed anti-air"]),
        make_match("loss", 4, mistakes=["burst timing"]),
    ]

    insights = build_coaching_insights(matches)

    assert insights.patterns.top_mistake is not None
    assert insights.patterns.top_mistake.tag == "missed anti-air"
    assert insights.patterns.top_mistake.count == 2
    assert insights.patterns.top_mistake.losses_analyzed == 3


def test_recent_loss_mistake_detection_includes_percentage():
    matches = [
        make_match("loss", 1, mistakes=["missed anti-air"]),
        make_match("loss", 2, mistakes=["missed anti-air"]),
        make_match("loss", 3, mistakes=["corner escape"]),
        make_match("loss", 4, mistakes=["missed anti-air"]),
    ]

    mistake = build_coaching_insights(matches).patterns.recent_loss_mistakes[0]

    assert mistake.tag == "missed anti-air"
    assert mistake.count == 3
    assert mistake.losses_analyzed == 4
    assert mistake.percentage_of_recent_losses == 75.0


def test_practice_priority_frequency_uses_exact_normalized_duplicates():
    matches = [
        make_match("loss", 1, practice_next=" Anti-air practice "),
        make_match("loss", 2, practice_next="anti-air practice"),
        make_match("loss", 3, practice_next="Punish practice"),
    ]

    priority = build_coaching_insights(matches).patterns.practice_priorities[0]

    assert priority.practice_next == "anti-air practice"
    assert priority.count == 2


def test_matchup_sample_size_threshold_and_strong_weak_detection():
    matches = [
        make_match("win", 1, opponent="May"),
        make_match("win", 2, opponent="May"),
        make_match("win", 3, opponent="May"),
        make_match("loss", 4, opponent="Slayer"),
        make_match("loss", 5, opponent="Slayer"),
        make_match("win", 6, opponent="Slayer"),
        make_match("loss", 7, opponent="Axl Low"),
    ]

    matchups = build_coaching_insights(matches).matchups

    assert matchups.minimum_sample_size == 3
    assert matchups.strongest_qualified_matchup is not None
    assert matchups.strongest_qualified_matchup.opponent_character == "May"
    assert matchups.weakest_qualified_matchup is not None
    assert matchups.weakest_qualified_matchup.opponent_character == "Slayer"
    assert [matchup.opponent_character for matchup in matchups.matchups_needing_more_data] == ["Axl Low"]


def test_most_played_matchup_and_matchup_with_most_losses():
    matches = [
        make_match("loss", 1, opponent="Slayer"),
        make_match("loss", 2, opponent="Slayer"),
        make_match("win", 3, opponent="Slayer"),
        make_match("loss", 4, opponent="May"),
        make_match("win", 5, opponent="May"),
    ]

    matchups = build_coaching_insights(matches).matchups

    assert matchups.most_played_matchup is not None
    assert matchups.most_played_matchup.opponent_character == "Slayer"
    assert matchups.matchup_with_most_losses is not None
    assert matchups.matchup_with_most_losses.opponent_character == "Slayer"


def test_recent_matchup_improvement_and_decline():
    improving = [
        make_match("loss", 1, opponent="Slayer"),
        make_match("loss", 2, opponent="Slayer"),
        make_match("loss", 3, opponent="Slayer"),
        make_match("win", 4, opponent="Slayer"),
        make_match("win", 5, opponent="Slayer"),
        make_match("win", 6, opponent="Slayer"),
    ]
    declining = [
        make_match("win", 1, opponent="May"),
        make_match("win", 2, opponent="May"),
        make_match("win", 3, opponent="May"),
        make_match("loss", 4, opponent="May"),
        make_match("loss", 5, opponent="May"),
        make_match("loss", 6, opponent="May"),
    ]

    improving_trend = build_coaching_insights(improving).matchups.recent_matchup_trends[0]
    declining_trend = build_coaching_insights(declining).matchups.recent_matchup_trends[0]

    assert improving_trend.opponent_character == "Slayer"
    assert improving_trend.trend == "improving"
    assert declining_trend.opponent_character == "May"
    assert declining_trend.trend == "declining"


def test_recommendation_prioritization_and_evidence():
    matches = [
        make_match("loss", 1, opponent="Slayer", mistakes=["missed anti-air"], practice_next="anti-air practice"),
        make_match("loss", 2, opponent="Slayer", mistakes=["missed anti-air"], practice_next="anti-air practice"),
        make_match("loss", 3, opponent="Slayer", mistakes=["missed anti-air"], practice_next="defense"),
        make_match("loss", 4, opponent="Slayer", mistakes=["missed anti-air"], practice_next="defense"),
        make_match("win", 5, opponent="Slayer"),
        make_match("loss", 6, opponent="Slayer"),
    ]

    recommendations = build_coaching_insights(matches).recommendations

    assert recommendations[0].type == "repeated_mistake"
    assert recommendations[0].priority == "high"
    assert recommendations[0].evidence["tag"] == "missed anti-air"
    assert any(recommendation.type == "weak_matchup" for recommendation in recommendations)
    assert len(recommendations) <= 5


def test_empty_history_and_one_match_are_safe():
    empty = build_coaching_insights([])
    one = build_coaching_insights([make_match("win", 1)])

    assert empty.performance.overall_win_rate is None
    assert empty.streaks.current_streak_type is None
    assert empty.recommendations == []
    assert one.performance.overall_win_rate == 100.0
    assert one.streaks.current_streak_type == "win"
    assert one.matchups.weakest_qualified_matchup is None


def test_chronological_order_same_date_and_updated_at_are_handled():
    older_edited_match = make_match("win", 1, played_on=date(2026, 7, 1))
    older_edited_match.updated_at = datetime(2026, 8, 30, tzinfo=timezone.utc)
    same_day_second = make_match("win", 2, played_on=date(2026, 7, 1))
    later_loss = make_match("loss", 3, played_on=date(2026, 7, 2))

    insights = build_coaching_insights([later_loss, older_edited_match, same_day_second])

    assert insights.streaks.longest_win_streak == 2
    assert insights.streaks.current_streak_type == "loss"
    assert insights.streaks.current_streak_count == 1


def test_account_isolation_when_callers_pass_user_scoped_matches():
    account_a = [
        make_match("loss", 1, owner_id=1, opponent="Slayer", mistakes=["missed anti-air"]),
        make_match("loss", 2, owner_id=1, opponent="Slayer", mistakes=["missed anti-air"]),
        make_match("loss", 3, owner_id=1, opponent="Slayer", mistakes=["missed anti-air"]),
    ]
    account_b = [
        make_match("win", 4, owner_id=2, opponent="May"),
        make_match("win", 5, owner_id=2, opponent="May"),
        make_match("win", 6, owner_id=2, opponent="May"),
    ]

    a_insights = build_coaching_insights(account_a)
    b_insights = build_coaching_insights(account_b)

    assert a_insights.patterns.top_mistake is not None
    assert a_insights.patterns.top_mistake.tag == "missed anti-air"
    assert a_insights.matchups.weakest_qualified_matchup is not None
    assert a_insights.matchups.weakest_qualified_matchup.opponent_character == "Slayer"
    assert b_insights.patterns.top_mistake is None
    assert b_insights.matchups.strongest_qualified_matchup is not None
    assert b_insights.matchups.strongest_qualified_matchup.opponent_character == "May"
