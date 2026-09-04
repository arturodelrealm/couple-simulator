import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";

import { ApiClientError } from "../services/apiClient";
import { getGame, type Game } from "../services/gameService";
import {
  getPartnerAQuestionnaire,
  savePartnerAQuestionnaireAnswers,
  skipPartnerAQuestionnaireEvent,
  unskipPartnerAQuestionnaireEvent,
  type Questionnaire,
  type QuestionnaireItem,
} from "../services/partnerAQuestionnaireService";
import type { EventAnswer } from "../services/simulationService";
import { toErrorMessage } from "../shared/errors";
import {
  clearCurrentGame,
  saveCurrentGameFromGame,
} from "../shared/gameStorage";
import { applyQuestionnaireAvatarPreviews } from "../shared/play/applyQuestionnaireAvatarPreviews";
import { resolvePlayPartnerB } from "../shared/play/resolvePlayPartnerB";

function firstPendingIndex(items: QuestionnaireItem[]): number {
  const pending = items.findIndex((item) => item.status === "pending");
  return pending >= 0 ? pending : 0;
}

function answersFromSelections(
  item: QuestionnaireItem,
  selections: Record<string, string>,
): EventAnswer[] | null {
  const answers: EventAnswer[] = [];
  for (const question of item.presentation.questions) {
    const optionId = selections[question.id];
    if (optionId === undefined) {
      return null;
    }
    answers.push({ question_id: question.id, option_id: optionId });
  }
  return answers;
}

function selectionsFromItem(item: QuestionnaireItem): Record<string, string> {
  const next: Record<string, string> = {};
  for (const answer of item.saved_answers) {
    next[answer.question_id] = answer.option_id;
  }
  return next;
}

export function usePartnerAQuestionnaire() {
  const { t } = useTranslation();
  const { gameId } = useParams<{ gameId: string }>();
  const [game, setGame] = useState<Game | null>(null);
  const [questionnaire, setQuestionnaire] = useState<Questionnaire | null>(
    null,
  );
  const [eventIndex, setEventIndex] = useState(0);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [selections, setSelections] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const applyQuestionnaire = useCallback(
    (next: Questionnaire, preferredEventId?: string) => {
      setQuestionnaire(next);
      const preferredIndex =
        preferredEventId !== undefined
          ? next.items.findIndex((item) => item.event_id === preferredEventId)
          : -1;
      const index =
        preferredIndex >= 0 ? preferredIndex : firstPendingIndex(next.items);
      const item = next.items[index];
      setEventIndex(index);
      setQuestionIndex(0);
      setSelections(item ? selectionsFromItem(item) : {});
    },
    [],
  );

  useEffect(() => {
    if (!gameId) {
      setError(t("errors.gameNotFound"));
      setIsLoading(false);
      return;
    }

    let cancelled = false;
    void (async () => {
      setIsLoading(true);
      setError(null);
      setErrorCode(null);
      try {
        const [loadedGame, loadedQuestionnaire] = await Promise.all([
          getGame(gameId),
          getPartnerAQuestionnaire(gameId),
        ]);
        if (cancelled) {
          return;
        }
        saveCurrentGameFromGame(loadedGame);
        setGame(loadedGame);
        applyQuestionnaire(loadedQuestionnaire);
      } catch (err) {
        if (cancelled) {
          return;
        }
        if (err instanceof ApiClientError && err.code === "GAME_NOT_FOUND") {
          clearCurrentGame();
        }
        if (err instanceof ApiClientError) {
          setErrorCode(err.code);
        }
        setError(toErrorMessage(err, t));
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [applyQuestionnaire, gameId, t]);

  const currentItem = questionnaire?.items[eventIndex] ?? null;
  const questions = currentItem?.presentation.questions ?? [];
  const currentQuestion = questions[questionIndex] ?? null;
  const hasMoreQuestions = questionIndex < questions.length - 1;
  const selectedOptionId = currentQuestion
    ? (selections[currentQuestion.id] ?? null)
    : null;

  const partnerBIdentity = useMemo(() => {
    if (!game) {
      return null;
    }
    return resolvePlayPartnerB(game, 22, null);
  }, [game]);

  const partnerAAvatar = useMemo(
    () =>
      applyQuestionnaireAvatarPreviews(
        game?.partner_a.avatar_config ?? {},
        currentItem?.avatar_previews ?? [],
        selections,
        "partner_a",
      ),
    [currentItem, game, selections],
  );
  const partnerBAvatar = useMemo(
    () =>
      applyQuestionnaireAvatarPreviews(
        partnerBIdentity?.avatarConfig ?? {},
        currentItem?.avatar_previews ?? [],
        selections,
        "partner_b",
      ),
    [currentItem, partnerBIdentity, selections],
  );

  const progressDone = questionnaire
    ? questionnaire.progress.answered + questionnaire.progress.skipped
    : 0;
  const progressTotal = questionnaire?.progress.total ?? 0;

  const openEvent = useCallback((eventId: string) => {
    setQuestionnaire((current) => {
      if (!current) {
        return current;
      }
      const index = current.items.findIndex(
        (item) => item.event_id === eventId,
      );
      if (index < 0) {
        return current;
      }
      const item = current.items[index];
      setEventIndex(index);
      setQuestionIndex(0);
      setSelections(selectionsFromItem(item));
      setActionError(null);
      return current;
    });
  }, []);

  const persistAnswers = useCallback(async () => {
    if (!gameId || !currentItem) {
      return;
    }
    const answers = answersFromSelections(currentItem, selections);
    if (answers === null) {
      return;
    }
    setIsSaving(true);
    setActionError(null);
    try {
      await savePartnerAQuestionnaireAnswers(
        gameId,
        currentItem.event_id,
        answers,
      );
      const refreshed = await getPartnerAQuestionnaire(gameId);
      applyQuestionnaire(refreshed);
    } catch (err) {
      setActionError(toErrorMessage(err, t));
    } finally {
      setIsSaving(false);
    }
  }, [applyQuestionnaire, currentItem, gameId, selections, t]);

  const goToNextQuestion = useCallback(() => {
    if (!currentQuestion || selectedOptionId === null) {
      return;
    }
    if (hasMoreQuestions) {
      setQuestionIndex((index) => index + 1);
      return;
    }
    void persistAnswers();
  }, [currentQuestion, hasMoreQuestions, persistAnswers, selectedOptionId]);

  const selectOption = useCallback(
    (optionId: string) => {
      if (!currentQuestion) {
        return;
      }
      setSelections((current) => ({
        ...current,
        [currentQuestion.id]: optionId,
      }));
    },
    [currentQuestion],
  );

  const skipEvent = useCallback(async () => {
    if (!gameId || !currentItem) {
      return;
    }
    setIsSaving(true);
    setActionError(null);
    try {
      await skipPartnerAQuestionnaireEvent(gameId, currentItem.event_id);
      const refreshed = await getPartnerAQuestionnaire(gameId);
      applyQuestionnaire(refreshed);
    } catch (err) {
      setActionError(toErrorMessage(err, t));
    } finally {
      setIsSaving(false);
    }
  }, [applyQuestionnaire, currentItem, gameId, t]);

  const unskipEvent = useCallback(async () => {
    if (!gameId || !currentItem) {
      return;
    }
    setIsSaving(true);
    setActionError(null);
    try {
      await unskipPartnerAQuestionnaireEvent(gameId, currentItem.event_id);
      const refreshed = await getPartnerAQuestionnaire(gameId);
      applyQuestionnaire(refreshed, currentItem.event_id);
    } catch (err) {
      setActionError(toErrorMessage(err, t));
    } finally {
      setIsSaving(false);
    }
  }, [applyQuestionnaire, currentItem, gameId, t]);

  const contentParams = useMemo(
    () => ({
      partnerAName: game?.partner_a.name ?? "",
      partnerBName: partnerBIdentity?.nameFromApi ?? t("game.play.partnerB"),
      mascotName: "",
    }),
    [game, partnerBIdentity, t],
  );

  return {
    gameId,
    game,
    questionnaire,
    currentItem,
    currentQuestion,
    questionIndex,
    selectedOptionId,
    progressDone,
    progressTotal,
    isComplete: questionnaire?.progress.complete ?? false,
    hasMoreQuestions,
    isLoading,
    isSaving,
    error,
    errorCode,
    actionError,
    contentParams,
    partnerAAvatar,
    partnerBAvatar,
    partnerBIdentity,
    selectOption,
    goToNextQuestion,
    skipEvent,
    unskipEvent,
    openEvent,
  };
}
