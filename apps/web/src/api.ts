import type {
  CoordinationAlert,
  CourtesyAssessment,
  ReplayResult,
  ReviewStatus,
} from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`İstek tamamlanamadı (${response.status}).`);
  }
  return response.json() as Promise<T>;
}

export function replayScenario(scenario: string): Promise<ReplayResult> {
  return request(`/api/v1/replays/${scenario}`, { method: "POST" });
}

export function listAlerts(): Promise<CoordinationAlert[]> {
  return request("/api/v1/alerts");
}

export function submitDecision(
  alertId: string,
  status: Exclude<ReviewStatus, "pending">,
  reason: string,
): Promise<{ status: ReviewStatus }> {
  return request(`/api/v1/alerts/${alertId}/decisions`, {
    method: "POST",
    body: JSON.stringify({ status, reason, reviewer: "moderator" }),
  });
}

export function checkCourtesy(text: string): Promise<CourtesyAssessment> {
  return request("/api/v1/text/courtesy-check", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}
