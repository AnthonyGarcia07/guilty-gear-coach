import { matchHistorySearch, parseMatchHistoryParams } from "./matchHistoryPagination";

const fallbackMatchHistoryPath = "/matches";
const safeOrigin = "http://guilty-gear-coach.local";

export function matchHistoryReturnPath(search: string) {
  const params = parseMatchHistoryParams(search);
  return `${fallbackMatchHistoryPath}${matchHistorySearch(params.page, params.sort)}`;
}

export function safeMatchHistoryReturnPath(value: unknown) {
  if (typeof value !== "string" || !value.startsWith("/") || value.startsWith("//")) {
    return fallbackMatchHistoryPath;
  }

  try {
    const url = new URL(value, safeOrigin);
    if (url.origin !== safeOrigin || url.pathname !== fallbackMatchHistoryPath) {
      return fallbackMatchHistoryPath;
    }

    return matchHistoryReturnPath(url.search);
  } catch {
    return fallbackMatchHistoryPath;
  }
}

export function getMatchHistoryReturnFromState(state: unknown) {
  if (!state || typeof state !== "object" || !("returnTo" in state)) {
    return fallbackMatchHistoryPath;
  }

  return safeMatchHistoryReturnPath((state as { returnTo?: unknown }).returnTo);
}
