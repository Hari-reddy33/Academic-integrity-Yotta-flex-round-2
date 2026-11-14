const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function apiRequest<T>(
  path: string,
  token: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export async function authenticate(email: string, password: string): Promise<string> {
  const payload = new URLSearchParams({ username: email, password });
  const response = await fetch(`${API_URL}/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: payload,
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.detail ?? "Sign-in failed");
  return result.access_token as string;
}
