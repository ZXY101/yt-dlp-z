const FALLBACK_MESSAGE = "Something went wrong. Please try again.";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

interface ValidationIssue {
  msg?: unknown;
}

function validationMessage(issues: ValidationIssue[]) {
  const messages = issues.map((issue) => issue.msg).filter((msg) => typeof msg === "string");
  return messages.length > 0 ? messages.join(" ") : FALLBACK_MESSAGE;
}

/** Turns a FastAPI error body (`{ detail: string | ValidationIssue[] }`) into a sentence. */
export function errorMessage(body: unknown): string {
  if (typeof body !== "object" || body === null || !("detail" in body)) {
    return FALLBACK_MESSAGE;
  }
  const { detail } = body;
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return validationMessage(detail as ValidationIssue[]);
  }
  return FALLBACK_MESSAGE;
}

export function describeError(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return FALLBACK_MESSAGE;
}
