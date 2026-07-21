from datetime import date
from types import SimpleNamespace

from app.services.stats import build_dashboard_stats


def make_match(opponent: str, result: str, mistakes: list[str], reason: str | None = None):
    return SimpleNamespace(
        id=1,
        player_character="Sol Badguy",
        opponent_character=opponent,
        result=result,
        played_on=date(2026, 7, 8),
        rank_floor="Diamond",
        duration_seconds=120,
        notes=None,
        mistake_tags=mistakes,
        strength_tags=[],
        reason_for_loss=reason,
        practice_next=None,
        replay_filename=None,
        created_at=date(2026, 7, 8),
        updated_at=date(2026, 7, 8),
    )


def test_dashboard_stats_surface_actionable_patterns():
    stats = build_dashboard_stats(
        [
            make_match("Ky Kiske", "loss", ["corner escape", "meter spend"], "lost neutral in corner"),
            make_match("Ky Kiske", "win", ["meter spend"]),
            make_match("May", "loss", ["anti-air"], "missed anti-airs"),
        ]
    )

    assert stats.total_matches == 3
    assert stats.win_rate == 33.3
    assert stats.win_rate_by_opponent[0].opponent_character == "Ky Kiske"
    assert stats.most_common_mistake_tags[0].label == "meter spend"
    assert stats.most_common_reason_for_loss is not None
