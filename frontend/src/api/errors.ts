export interface NormalizedApiError {
  message: string;
  fieldErrors: Record<string, string>;
}

const defaultMessage = "Unable to update match.";
const objectStringMessage = "[object Object]";

export class ApiError extends Error {
  status: number;
  fieldErrors: Record<string, string>;

  constructor(status: number, message: unknown, fieldErrors: Record<string, unknown> = {}) {
    const normalizedMessage = normalizeMessage(message, defaultMessage);
    super(normalizedMessage);
    this.name = "ApiError";
    this.status = status;
    this.fieldErrors = normalizeFieldErrors(fieldErrors);
  }
}

export function normalizeUnknownError(error: unknown, fallback = defaultMessage): NormalizedApiError {
  if (error instanceof ApiError) {
    return {
      message: normalizeMessage(error.message, fallback),
      fieldErrors: normalizeFieldErrors(error.fieldErrors)
    };
  }

  if (error instanceof Error) {
    return {
      message: normalizeMessage(error.message, fallback),
      fieldErrors: {}
    };
  }

  if (isRecord(error)) {
    return normalizeErrorPayload(error, fallback);
  }

  return {
    message: normalizeMessage(error, fallback),
    fieldErrors: {}
  };
}

export function normalizeErrorPayload(payload: unknown, fallback = defaultMessage): NormalizedApiError {
  if (payload == null || payload === "") {
    return { message: fallback, fieldErrors: {} };
  }

  if (isRecord(payload) && "detail" in payload) {
    return normalizeDetail(payload.detail, fallback);
  }

  return {
    message: normalizeMessage(payload, fallback),
    fieldErrors: {}
  };
}

export async function normalizeErrorResponse(response: Response, fallback = defaultMessage): Promise<NormalizedApiError> {
  const text = await response.text().catch(() => "");
  if (!text.trim()) {
    return { message: fallback, fieldErrors: {} };
  }

  try {
    return normalizeErrorPayload(JSON.parse(text), fallback);
  } catch {
    return {
      message: normalizeMessage(text, fallback),
      fieldErrors: {}
    };
  }
}

function normalizeDetail(detail: unknown, fallback: string): NormalizedApiError {
  if (Array.isArray(detail)) {
    const messages: string[] = [];
    const fieldErrors: Record<string, string> = {};

    for (const item of detail) {
      if (isRecord(item)) {
        const message = normalizePydanticMessage(item.msg, fallback);
        messages.push(message);

        const fieldName = fieldNameFromLocation(item.loc);
        if (fieldName && !fieldErrors[fieldName]) {
          fieldErrors[fieldName] = message;
        }
      } else {
        messages.push(normalizeMessage(item, fallback));
      }
    }

    return {
      message: messages.length ? messages.join(" ") : fallback,
      fieldErrors: normalizeFieldErrors(fieldErrors)
    };
  }

  if (isRecord(detail)) {
    for (const key of ["message", "error", "detail", "msg"]) {
      if (key in detail) {
        const message = normalizeMessage(detail[key], "");
        if (message) {
          return { message, fieldErrors: {} };
        }
      }
    }
    return { message: fallback, fieldErrors: {} };
  }

  return {
    message: normalizeMessage(detail, fallback),
    fieldErrors: {}
  };
}

function normalizePydanticMessage(value: unknown, fallback: string): string {
  return normalizeMessage(value, fallback).replace(/^Value error,\s*/i, "");
}

function normalizeMessage(value: unknown, fallback: string): string {
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (trimmed && trimmed !== objectStringMessage) return trimmed;
    return fallback;
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return `${value}`;
  }

  return fallback;
}

function normalizeFieldErrors(errors: Record<string, unknown>): Record<string, string> {
  return Object.entries(errors).reduce<Record<string, string>>((normalized, [field, message]) => {
    const cleanMessage = normalizeMessage(message, "");
    if (cleanMessage) {
      normalized[field] = cleanMessage;
    }
    return normalized;
  }, {});
}

function fieldNameFromLocation(loc: unknown): string | null {
  if (!Array.isArray(loc)) return null;
  const field = loc.filter((part): part is string => typeof part === "string" && part !== "body").pop();
  return field ?? null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
