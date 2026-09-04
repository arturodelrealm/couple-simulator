import type { EventAnswer } from "../../services/simulationService";

export function partnerAnswerMap(
  partnerAnswers: EventAnswer[] | null | undefined,
): Record<string, string> | null {
  if (partnerAnswers === null || partnerAnswers === undefined) {
    return null;
  }
  const byQuestion: Record<string, string> = {};
  for (const answer of partnerAnswers) {
    byQuestion[answer.question_id] = answer.option_id;
  }
  return byQuestion;
}
