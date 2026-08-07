from math import ceil
from typing import Literal

from sqlalchemy import Select

from app.models import Match

MatchSort = Literal["recently_played", "last_updated", "oldest_played"]

DEFAULT_MATCH_PAGE = 1
DEFAULT_MATCH_PAGE_SIZE = 20
MAX_MATCH_PAGE_SIZE = 100
DEFAULT_MATCH_SORT: MatchSort = "recently_played"


def total_pages(total_items: int, page_size: int) -> int:
    return max(1, ceil(total_items / page_size))


def offset_for_page(page: int, page_size: int) -> int:
    return (page - 1) * page_size


def apply_match_history_sort(statement: Select, sort: MatchSort) -> Select:
    if sort == "last_updated":
        return statement.order_by(Match.updated_at.desc(), Match.id.desc())
    if sort == "oldest_played":
        return statement.order_by(Match.played_on.asc(), Match.id.asc())
    return statement.order_by(Match.played_on.desc(), Match.id.desc())


def sort_match_records(matches: list[Match], sort: MatchSort) -> list[Match]:
    if sort == "last_updated":
        return sorted(matches, key=lambda match: (match.updated_at, match.id), reverse=True)
    if sort == "oldest_played":
        return sorted(matches, key=lambda match: (match.played_on, match.id))
    return sorted(matches, key=lambda match: (match.played_on, match.id), reverse=True)


def paginate_match_records(matches: list[Match], page: int, page_size: int, sort: MatchSort = DEFAULT_MATCH_SORT) -> tuple[list[Match], int, int]:
    sorted_matches = sort_match_records(matches, sort)
    pages = total_pages(len(sorted_matches), page_size)
    requested_page = min(page, pages)
    offset = offset_for_page(requested_page, page_size)
    return sorted_matches[offset : offset + page_size], requested_page, pages
