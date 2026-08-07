import type { MatchSort } from "../types";

export const defaultMatchSort: MatchSort = "recently_played";
export const defaultMatchPage = 1;
export const defaultMatchPageSize = 20;

export function parseMatchHistoryParams(search: string) {
  const params = new URLSearchParams(search);
  const page = Number(params.get("page") ?? defaultMatchPage);
  const sort = params.get("sort");

  return {
    page: Number.isInteger(page) && page >= 1 ? page : defaultMatchPage,
    sort: isMatchSort(sort) ? sort : defaultMatchSort
  };
}

export function matchHistorySearch(page: number, sort: MatchSort) {
  const params = new URLSearchParams();
  if (page > defaultMatchPage) params.set("page", String(page));
  if (sort !== defaultMatchSort) params.set("sort", sort);
  const query = params.toString();
  return query ? `?${query}` : "";
}

export function sortChangeSearch(sort: MatchSort) {
  return matchHistorySearch(defaultMatchPage, sort);
}

export function paginationItems(currentPage: number, totalPages: number): Array<number | "..."> {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }

  const pages = new Set([1, 2, totalPages - 1, totalPages, currentPage - 1, currentPage, currentPage + 1]);
  const boundedPages = Array.from(pages).filter((page) => page >= 1 && page <= totalPages).sort((a, b) => a - b);
  const items: Array<number | "..."> = [];

  for (const page of boundedPages) {
    const previous = items[items.length - 1];
    if (typeof previous === "number" && page - previous > 1) {
      items.push("...");
    }
    items.push(page);
  }

  return items;
}

function isMatchSort(value: string | null): value is MatchSort {
  return value === "recently_played" || value === "last_updated" || value === "oldest_played";
}
