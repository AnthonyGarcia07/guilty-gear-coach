from collections import Counter, defaultdict

from app.models import Match
from app.schemas.stats import CharacterWinRate, DashboardStats, TagCount


def build_dashboard_stats(matches: list[Match]) -> DashboardStats:
    total = len(matches)
    wins = sum(1 for match in matches if match.result == "win")
    losses = total - wins
    opponent_buckets: dict[str, list[Match]] = defaultdict(list)
    mistakes: Counter[str] = Counter()
    loss_reasons: Counter[str] = Counter()

    for match in matches:
        opponent_buckets[match.opponent_character].append(match)
        mistakes.update(tag.strip() for tag in match.mistake_tags if tag.strip())
        if match.result == "loss" and match.reason_for_loss:
            loss_reasons.update([match.reason_for_loss.strip()])

    by_opponent = []
    for opponent, bucket in opponent_buckets.items():
        bucket_wins = sum(1 for match in bucket if match.result == "win")
        by_opponent.append(
            CharacterWinRate(
                opponent_character=opponent,
                matches=len(bucket),
                wins=bucket_wins,
                win_rate=round((bucket_wins / len(bucket)) * 100, 1),
            )
        )

    common_reason = loss_reasons.most_common(1)
    return DashboardStats(
        total_matches=total,
        wins=wins,
        losses=losses,
        win_rate=round((wins / total) * 100, 1) if total else 0,
        win_rate_by_opponent=sorted(by_opponent, key=lambda item: item.matches, reverse=True),
        most_common_mistake_tags=[TagCount(label=label, count=count) for label, count in mistakes.most_common(6)],
        most_common_reason_for_loss=TagCount(label=common_reason[0][0], count=common_reason[0][1]) if common_reason else None,
        recent_matches=matches[:6],
    )
