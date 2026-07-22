from datetime import date, datetime, timezone
from types import SimpleNamespace

from app.services.coaching import build_coaching_insights


def make_match(player: str, opponent: str, result: str, played_on: date, match_id: int, owner_id: int = 1):
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
        mistake_tags=[],
        strength_tags=[],
        reason_for_loss=None,
        practice_next=None,
        replay_filename=None,
        created_at=datetime(2026, 7, match_id, tzinfo=timezone.utc),
        updated_at=datetime(2026, 7, 20, tzinfo=timezone.utc),
    )


def assert_streaks(results: list[str], longest_wins: int, longest_losses: int, current_type: str | None, current_count: int):
    matches = [
        make_match("Bridget", "Ky Kiske" if index % 2 == 0 else "Slayer", result, date(2026, 7, index + 1), index + 1)
        for index, result in enumerate(results)
    ]

    insights = build_coaching_insights(matches)

    assert insights.longest_win_streak == longest_wins
    assert insights.longest_losing_streak == longest_losses
    assert insights.current_streak_type == current_type
    assert insights.current_streak_count == current_count


def test_coaching_insights_are_deterministic_from_match_history():
    insights = build_coaching_insights(
        [
            make_match("Bridget", "Ky Kiske", "win", date(2026, 7, 1), 1),
            make_match("Bridget", "Ky Kiske", "win", date(2026, 7, 2), 2),
            make_match("Bridget", "Slayer", "loss", date(2026, 7, 3), 3),
            make_match("Sol Badguy", "Slayer", "loss", date(2026, 7, 4), 4),
            make_match("Bridget", "May", "win", date(2026, 7, 5), 5),
            make_match("Bridget", "May", "win", date(2026, 7, 6), 6),
            make_match("Bridget", "May", "win", date(2026, 7, 7), 7),
        ]
    )

    assert insights.totalMatches == 7
    assert insights.overallWinRate == 71.4
    assert insights.longest_win_streak == 3
    assert insights.longest_losing_streak == 2
    assert insights.current_streak_type == "win"
    assert insights.current_streak_count == 3
    assert insights.mostPlayedCharacter == "Bridget"
    assert insights.bestMatchup == "May"
    assert insights.worstMatchup == "Slayer"


def test_alternating_results_have_longest_streaks_of_one():
    assert_streaks(["win", "loss", "win", "loss", "win", "loss"], 1, 1, "loss", 1)


def test_three_wins_then_three_losses_tracks_consecutive_streaks():
    assert_streaks(["win", "win", "win", "loss", "loss", "loss"], 3, 3, "loss", 3)


def test_mixed_sequence_tracks_current_single_loss():
    assert_streaks(["loss", "loss", "win", "win", "loss"], 2, 2, "loss", 1)


def test_empty_match_history_returns_safe_defaults():
    insights = build_coaching_insights([])

    assert insights.totalMatches == 0
    assert insights.overallWinRate == 0
    assert insights.longest_win_streak == 0
    assert insights.longest_losing_streak == 0
    assert insights.current_streak_type is None
    assert insights.current_streak_count == 0
    assert insights.mostPlayedCharacter is None
    assert insights.bestMatchup is None
    assert insights.worstMatchup is None


def test_single_win_and_single_loss_streaks():
    win_insights = build_coaching_insights([make_match("Bridget", "May", "win", date(2026, 7, 1), 1)])
    loss_insights = build_coaching_insights([make_match("Bridget", "May", "loss", date(2026, 7, 1), 1)])

    assert win_insights.longest_win_streak == 1
    assert win_insights.longest_losing_streak == 0
    assert win_insights.current_streak_type == "win"
    assert win_insights.current_streak_count == 1
    assert loss_insights.longest_win_streak == 0
    assert loss_insights.longest_losing_streak == 1
    assert loss_insights.current_streak_type == "loss"
    assert loss_insights.current_streak_count == 1


def test_same_date_matches_use_id_as_deterministic_secondary_order():
    insights = build_coaching_insights(
        [
            make_match("Bridget", "Ky Kiske", "loss", date(2026, 7, 1), 3),
            make_match("Bridget", "Ky Kiske", "win", date(2026, 7, 1), 1),
            make_match("Bridget", "Ky Kiske", "win", date(2026, 7, 1), 2),
        ]
    )

    assert insights.longest_win_streak == 2
    assert insights.current_streak_type == "loss"
    assert insights.current_streak_count == 1


def test_updated_at_does_not_affect_gameplay_chronology():
    older_edited_match = make_match("Bridget", "Ky Kiske", "win", date(2026, 7, 1), 1)
    older_edited_match.updated_at = datetime(2026, 7, 30, tzinfo=timezone.utc)
    newer_match = make_match("Bridget", "Slayer", "loss", date(2026, 7, 2), 2)

    insights = build_coaching_insights([newer_match, older_edited_match])

    assert insights.longest_win_streak == 1
    assert insights.longest_losing_streak == 1
    assert insights.current_streak_type == "loss"
    assert insights.current_streak_count == 1


def test_callers_can_pass_only_one_account_matches_for_isolated_streaks():
    account_one_matches = [
        make_match("Bridget", "May", "win", date(2026, 7, 1), 1, owner_id=1),
        make_match("Bridget", "May", "win", date(2026, 7, 2), 2, owner_id=1),
    ]
    account_two_matches = [
        make_match("Sol Badguy", "May", "loss", date(2026, 7, 1), 3, owner_id=2),
        make_match("Sol Badguy", "May", "loss", date(2026, 7, 2), 4, owner_id=2),
    ]

    account_one = build_coaching_insights(account_one_matches)
    account_two = build_coaching_insights(account_two_matches)

    assert account_one.current_streak_type == "win"
    assert account_one.current_streak_count == 2
    assert account_two.current_streak_type == "loss"
    assert account_two.current_streak_count == 2
