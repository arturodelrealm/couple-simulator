export type ApiSuccess<T> = { data: T };
export type ApiErrorDetail = { code: string; message: string; field?: string };
export type ApiError = { errors: ApiErrorDetail[] };

export class ApiClientError extends Error {
  readonly code: string;
  readonly field?: string;

  constructor(code: string, message: string, field?: string) {
    super(message);
    this.code = code;
    this.field = field;
  }
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function parseResponse<T>(response: Response): Promise<T> {
  const body = (await response.json()) as ApiSuccess<T> | ApiError;

  if (!response.ok) {
    const errors = "errors" in body ? body.errors : [];
    const first = errors[0];
    throw new ApiClientError(
      first?.code ?? "UNKNOWN_ERROR",
      first?.message ?? "Request failed",
      first?.field,
    );
  }

  return (body as ApiSuccess<T>).data;
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  return parseResponse<T>(response);
}
