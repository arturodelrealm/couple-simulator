import { apiRequest } from "./apiClient";
import type { EventAnswer, EventPresentation } from "./simulationService";

export type QuestionnaireItemStatus = "pending" | "answered" | "skipped";

export type QuestionnaireProgress = {
  answered: number;
  skipped: number;
  total: number;
  complete: boolean;
};

export type QuestionnaireAvatarPreview = {
  question_id: string;
  option_id: string;
  player: "partner_a" | "partner_b" | string;
  attribute: string;
  value: string | number;
};

export type QuestionnaireItem = {
  event_id: string;
  presentation: EventPresentation;
  status: QuestionnaireItemStatus;
  saved_answers: EventAnswer[];
  avatar_previews: QuestionnaireAvatarPreview[];
};

export type Questionnaire = {
  items: QuestionnaireItem[];
  progress: QuestionnaireProgress;
};

export type QuestionnaireEventUpdate = {
  item: QuestionnaireItem;
  progress: QuestionnaireProgress;
};

function questionnairePath(gameId: string): string {
  return `/api/games/${gameId}/partner-a/questionnaire`;
}

function eventPath(gameId: string, eventId: string, action: string): string {
  return `${questionnairePath(gameId)}/events/${eventId}/${action}`;
}

export function getPartnerAQuestionnaire(
  gameId: string,
): Promise<Questionnaire> {
  return apiRequest<Questionnaire>(questionnairePath(gameId));
}

export function savePartnerAQuestionnaireAnswers(
  gameId: string,
  eventId: string,
  answers: EventAnswer[],
): Promise<QuestionnaireEventUpdate> {
  return apiRequest<QuestionnaireEventUpdate>(
    eventPath(gameId, eventId, "answers"),
    {
      method: "PUT",
      body: JSON.stringify({ answers }),
    },
  );
}

export function skipPartnerAQuestionnaireEvent(
  gameId: string,
  eventId: string,
): Promise<QuestionnaireEventUpdate> {
  return apiRequest<QuestionnaireEventUpdate>(
    eventPath(gameId, eventId, "skip"),
    { method: "POST" },
  );
}

export function unskipPartnerAQuestionnaireEvent(
  gameId: string,
  eventId: string,
): Promise<QuestionnaireEventUpdate> {
  return apiRequest<QuestionnaireEventUpdate>(
    eventPath(gameId, eventId, "unskip"),
    { method: "POST" },
  );
}
