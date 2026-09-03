import { apiRequest } from "./apiClient";

export type SimulationRunStatus = "ACTIVE" | "FINISHED";

export type SimulationLifeStage = "youth" | "adult" | "elderly";

export type SimulationHousingType = "apartment" | "house";

export type SimulationHousingQuality = "bad" | "ok" | "excellent";

export type SimulationHousing = {
  place: string;
  type: SimulationHousingType | string;
  quality: SimulationHousingQuality | string;
};

export type SimulationMascot = {
  species: string;
  name: string;
};

export type SimulationState = {
  age: number;
  compatibility: number;
  finances: number;
  quality_of_life: number;
  children: number;
  wellness: number;
  housing: SimulationHousing;
  mascot: SimulationMascot | null;
  tags: Record<string, unknown>;
  life_stage: SimulationLifeStage | string;
  relationship_status: string;
};

export type SimulationPlayerRole = "partner_a" | "partner_b";

export type StartRunPayload = {
  player_role: SimulationPlayerRole;
  seed?: number;
  max_events?: number;
};

export type SimulationRunCreated = {
  run_id: string;
  player_role: string;
  status: SimulationRunStatus | string;
  state: SimulationState;
  events_played: number;
};

export type TimelineEntry = {
  title: string;
  category: string;
  age: number;
  description: string | null;
};

export type SimulationAnswer = {
  event_id: string;
  question_id: string;
  option_id: string;
};

export type SimulationRunDetail = SimulationRunCreated & {
  timeline: TimelineEntry[];
  answers: SimulationAnswer[];
  current_event_id: string | null;
  rng_seed: number;
  run_number: number;
};

export type SimulationRunSummary = {
  run_id: string;
  player_role: string;
  status: SimulationRunStatus | string;
  created_at: string | null;
  run_number: number;
};

export type Pagination = {
  page: number;
  per_page: number;
  total: number;
};

export type SimulationRunList = {
  items: SimulationRunSummary[];
  pagination: Pagination;
};

export type ListSimulationRunsParams = {
  status?: SimulationRunStatus;
  player_role?: SimulationPlayerRole;
  page?: number;
  per_page?: number;
};

export type OptionPresentation = {
  id: string;
  text: string;
};

export type QuestionPresentation = {
  id: string;
  text: string;
  options: OptionPresentation[];
};

export type EventPresentation = {
  event_id: string;
  title: string;
  description: string | null;
  questions: QuestionPresentation[];
};

export type CurrentEvent = {
  run_id: string;
  event: EventPresentation;
};

export type EventAnswer = {
  question_id: string;
  option_id: string;
};

export type ClientAction = {
  type: string;
  args?: Record<string, unknown>;
};

export type SubmitEventAnswersResult = {
  run_id: string;
  status: SimulationRunStatus | string;
  state: SimulationState;
  events_played: number;
  client_actions: ClientAction[];
  game_finished: boolean;
};

const DEFAULT_START_RUN_PAYLOAD: StartRunPayload = {
  player_role: "partner_a",
};

function runsCollectionPath(gameId: string): string {
  return `/api/games/${gameId}/simulation/runs`;
}

function runResourcePath(gameId: string, runId: string): string {
  return `${runsCollectionPath(gameId)}/${runId}`;
}

export function startSimulationRun(
  gameId: string,
  body: StartRunPayload = DEFAULT_START_RUN_PAYLOAD,
): Promise<SimulationRunCreated> {
  return apiRequest<SimulationRunCreated>(runsCollectionPath(gameId), {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getSimulationRun(
  gameId: string,
  runId: string,
): Promise<SimulationRunDetail> {
  return apiRequest<SimulationRunDetail>(runResourcePath(gameId, runId));
}

export function getCurrentEvent(
  gameId: string,
  runId: string,
): Promise<CurrentEvent> {
  return apiRequest<CurrentEvent>(
    `${runResourcePath(gameId, runId)}/events/current`,
  );
}

export function listSimulationRuns(
  gameId: string,
  params?: ListSimulationRunsParams,
): Promise<SimulationRunList> {
  const search = new URLSearchParams();
  if (params?.status !== undefined) {
    search.set("status", params.status);
  }
  if (params?.player_role !== undefined) {
    search.set("player_role", params.player_role);
  }
  if (params?.page !== undefined) {
    search.set("page", String(params.page));
  }
  if (params?.per_page !== undefined) {
    search.set("per_page", String(params.per_page));
  }
  const query = search.toString();
  const suffix = query === "" ? "" : `?${query}`;
  return apiRequest<SimulationRunList>(
    `${runsCollectionPath(gameId)}${suffix}`,
  );
}

export function submitEventAnswers(
  gameId: string,
  runId: string,
  eventId: string,
  answers: EventAnswer[],
): Promise<SubmitEventAnswersResult> {
  return apiRequest<SubmitEventAnswersResult>(
    `${runResourcePath(gameId, runId)}/events/${eventId}/answers`,
    {
      method: "POST",
      body: JSON.stringify({ answers }),
    },
  );
}
