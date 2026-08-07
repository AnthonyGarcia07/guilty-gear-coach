from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.core.database import get_db
from app.main import app
from app.services.match_history import (
    DEFAULT_MATCH_PAGE_SIZE,
    DEFAULT_MATCH_SORT,
    MAX_MATCH_PAGE_SIZE,
    offset_for_page,
    paginate_match_records,
    sort_match_records,
    total_pages,
)


def make_match(match_id: int, owner_id: int = 1, played_on: date | None = None, updated_at: datetime | None = None):
    default_played_on = date(2026, 7, 1) + timedelta(days=match_id - 1)
    default_updated_at = datetime(2026, 7, 1, tzinfo=timezone.utc) + timedelta(days=match_id - 1)
    return SimpleNamespace(
        id=match_id,
        owner_id=owner_id,
        played_on=played_on or default_played_on,
        updated_at=updated_at or default_updated_at,
    )


def test_default_sort_is_recently_played():
    assert DEFAULT_MATCH_SORT == "recently_played"


def test_recently_played_ordering_and_same_date_tiebreaker():
    matches = [
        make_match(1, played_on=date(2026, 7, 1)),
        make_match(3, played_on=date(2026, 7, 2)),
        make_match(2, played_on=date(2026, 7, 2)),
    ]

    assert [match.id for match in sort_match_records(matches, "recently_played")] == [3, 2, 1]


def test_last_updated_ordering():
    matches = [
        make_match(1, updated_at=datetime(2026, 7, 1, tzinfo=timezone.utc)),
        make_match(2, updated_at=datetime(2026, 7, 3, tzinfo=timezone.utc)),
        make_match(3, updated_at=datetime(2026, 7, 2, tzinfo=timezone.utc)),
    ]

    assert [match.id for match in sort_match_records(matches, "last_updated")] == [2, 3, 1]


def test_oldest_played_ordering():
    matches = [
        make_match(1, played_on=date(2026, 7, 3)),
        make_match(2, played_on=date(2026, 7, 1)),
        make_match(3, played_on=date(2026, 7, 2)),
    ]

    assert [match.id for match in sort_match_records(matches, "oldest_played")] == [2, 3, 1]


def test_pagination_page_1_and_later_pages():
    matches = [make_match(index) for index in range(1, 46)]

    page_1, current_page_1, pages = paginate_match_records(matches, 1, 20)
    page_3, current_page_3, _ = paginate_match_records(matches, 3, 20)

    assert [match.id for match in page_1] == list(range(45, 25, -1))
    assert [match.id for match in page_3] == [5, 4, 3, 2, 1]
    assert current_page_1 == 1
    assert current_page_3 == 3
    assert pages == 3


def test_total_item_count_total_pages_and_offsets():
    assert total_pages(87, DEFAULT_MATCH_PAGE_SIZE) == 5
    assert total_pages(0, DEFAULT_MATCH_PAGE_SIZE) == 1
    assert offset_for_page(3, 20) == 40


def test_invalid_page_page_size_and_sort_are_rejected_by_api_validation():
    client = TestClient(app)
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1)
    app.dependency_overrides[get_db] = lambda: None
    try:
        assert client.get("/api/matches?page=0").status_code == 422
        assert client.get(f"/api/matches?page_size={MAX_MATCH_PAGE_SIZE + 1}").status_code == 422
        assert client.get("/api/matches?sort=bad").status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_account_isolation_and_pagination_never_leaks_other_users_matches():
    user_one = [make_match(index, owner_id=1) for index in range(1, 26)]
    user_two = [make_match(index, owner_id=2) for index in range(26, 31)]
    scoped_matches = [match for match in user_one + user_two if match.owner_id == 1]

    page, _, pages = paginate_match_records(scoped_matches, 2, 20)

    assert pages == 2
    assert {match.owner_id for match in page} == {1}
    assert [match.id for match in page] == [5, 4, 3, 2, 1]
