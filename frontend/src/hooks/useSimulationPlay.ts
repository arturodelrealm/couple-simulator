import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router-dom";

import { ApiClientError } from "../services/apiClient";
import { getGame, type Game } from "../services/gameService";
import {
  getCurrentEvent,
  getSimulationRun,
  startSimulationRun,
  submitEventAnswers,
  type ClientAction,
  type CurrentEvent,
  type EventAnswer,
  type QuestionPresentation,
  type SimulationRunDetail,
} from "../services/simulationService";
import { toErrorMessage } from "../shared/errors";
import { getPlayPath } from "../shared/gameNavigation";
import {
  clearCurrentGame,
  saveCurrentGameFromGame,
  saveCurrentRunId,
} from "../shared/gameStorage";
import {
  getOrCreatePartnerBPreferences,
  type PartnerBPreferences,
} from "../shared/play/partnerBPreferences";

export type EventStep =
  "answering" | "submitting" | "event-resolved" | "game-over";

export type PlayDialogueLine = {
  speaker: "partner_a" | "partner_b" | "both";
  text: string;
};

type LoadResult = {
  game: Game;
  run: SimulationRunDetail;
  currentEvent: CurrentEvent | null;
  eventStep: EventStep;
  partnerBPreferences: PartnerBPreferences;
};

function persistSuccessfulLoad(game: Game, runId: string): void {
  saveCurrentGameFromGame(game);
  saveCurrentRunId(runId);
}

function isEndOfRunError(error: unknown): boolean {
  return (
    error instanceof ApiClientError &&
    (error.code === "RUN_FINISHED" || error.code === "NO_ELIGIBLE_EVENTS")
  );
}

function collectAnswers(
  questions: QuestionPresentation[],
  selectedOptions: Record<string, string>,
): EventAnswer[] | null {
  const answers: EventAnswer[] = [];
  for (const question of questions) {
    const optionId = selectedOptions[question.id];
    if (optionId === undefined) {
      return null;
    }
    answers.push({ question_id: question.id, option_id: optionId });
  }
  return answers;
}

function asDialogueSpeaker(value: unknown): PlayDialogueLine["speaker"] {
  if (value === "partner_a" || value === "partner_b" || value === "both") {
    return value;
  }
  return "both";
}

function dialogueFromClientActions(
  actions: ClientAction[],
): PlayDialogueLine[] {
  const lines: PlayDialogueLine[] = [];
  for (const action of actions) {
    if (action.type !== "add_conversation") {
      continue;
    }
    const args = action.args ?? {};
    const text = typeof args.text === "string" ? args.text : "";
    if (text === "") {
      continue;
    }
    lines.push({ speaker: asDialogueSpeaker(args.speaker), text });
  }
  return lines;
}

async function loadSimulationPlay(
  gameId: string,
  runId: string,
): Promise<LoadResult> {
  const [game, run] = await Promise.all([
    getGame(gameId),
    getSimulationRun(gameId, runId),
  ]);
  persistSuccessfulLoad(game, run.run_id);
  const partnerBPreferences = getOrCreatePartnerBPreferences(
    gameId,
    run.state.age,
  );

  if (run.status === "FINISHED") {
    return {
      game,
      run,
      currentEvent: null,
      eventStep: "game-over",
      partnerBPreferences,
    };
  }

  try {
    const currentEvent = await getCurrentEvent(gameId, runId);
    return {
      game,
      run,
      currentEvent,
      eventStep: "answering",
      partnerBPreferences,
    };
  } catch (error) {
    if (isEndOfRunError(error)) {
      return {
        game,
        run,
        currentEvent: null,
        eventStep: "game-over",
        partnerBPreferences,
      };
    }
    throw error;
  }
}

export function useSimulationPlay() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { gameId, runId } = useParams<{ gameId: string; runId: string }>();
  const [game, setGame] = useState<Game | null>(null);
  const [run, setRun] = useState<SimulationRunDetail | null>(null);
  const [currentEvent, setCurrentEvent] = useState<CurrentEvent | null>(null);
  const [eventStep, setEventStep] = useState<EventStep>("answering");
  const [questionIndex, setQuestionIndex] = useState(0);
  const [selectedOptions, setSelectedOptions] = useState<
    Record<string, string>
  >({});
  const [resolution, setResolution] = useState<ClientAction[] | null>(null);
  const [gameFinished, setGameFinished] = useState(false);
  const [partnerBPreferences, setPartnerBPreferences] =
    useState<PartnerBPreferences | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [isContinuing, setIsContinuing] = useState(false);
  const [isPlayingAgain, setIsPlayingAgain] = useState(false);
  const submitInFlightRef = useRef(false);
  const continueInFlightRef = useRef(false);

  const applyLoadFailure = useCallback(
    (err: unknown) => {
      if (err instanceof ApiClientError && err.code === "GAME_NOT_FOUND") {
        clearCurrentGame();
      }
      setGame(null);
      setRun(null);
      setCurrentEvent(null);
      setPartnerBPreferences(null);
      setError(toErrorMessage(err, t));
      setErrorCode(err instanceof ApiClientError ? err.code : null);
    },
    [t],
  );

  const refetch = useCallback(async () => {
    if (!gameId || !runId) {
      setError(t("errors.gameNotFound"));
      setErrorCode(null);
      setGame(null);
      setRun(null);
      setCurrentEvent(null);
      setPartnerBPreferences(null);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    setErrorCode(null);
    setActionError(null);
    try {
      const loaded = await loadSimulationPlay(gameId, runId);
      setGame(loaded.game);
      setRun(loaded.run);
      setCurrentEvent(loaded.currentEvent);
      setEventStep(loaded.eventStep);
      setQuestionIndex(0);
      setSelectedOptions({});
      setResolution(null);
      setGameFinished(loaded.eventStep === "game-over");
      setPartnerBPreferences(loaded.partnerBPreferences);
      submitInFlightRef.current = false;
    } catch (err) {
      applyLoadFailure(err);
    } finally {
      setIsLoading(false);
    }
  }, [applyLoadFailure, gameId, runId, t]);

  useEffect(() => {
    void refetch();
  }, [refetch]);

  const submitCollectedAnswers = useCallback(
    async (options: Record<string, string>) => {
      if (
        !gameId ||
        !runId ||
        !currentEvent ||
        eventStep !== "answering" ||
        submitInFlightRef.current
      ) {
        return;
      }
      const answers = collectAnswers(currentEvent.event.questions, options);
      if (answers === null) {
        return;
      }

      submitInFlightRef.current = true;
      setEventStep("submitting");
      setActionError(null);
      try {
        const submitted = await submitEventAnswers(
          gameId,
          runId,
          currentEvent.event.event_id,
          answers,
        );
        try {
          const updatedRun = await getSimulationRun(gameId, runId);
          setRun(updatedRun);
        } catch {
          setRun((prev) =>
            prev
              ? {
                  ...prev,
                  status: submitted.status,
                  state: submitted.state,
                  events_played: submitted.events_played,
                }
              : prev,
          );
        }
        setResolution(submitted.client_actions);
        setGameFinished(
          submitted.game_finished || submitted.status === "FINISHED",
        );
        setEventStep("event-resolved");
      } catch (err) {
        if (err instanceof ApiClientError && err.code === "GAME_NOT_FOUND") {
          clearCurrentGame();
        }
        submitInFlightRef.current = false;
        setActionError(toErrorMessage(err, t));
        setEventStep("answering");
      }
    },
    [currentEvent, eventStep, gameId, runId, t],
  );

  const selectOption = useCallback(
    (optionId: string) => {
      if (eventStep !== "answering" || !currentEvent) {
        return;
      }
      const questions = currentEvent.event.questions;
      const question = questions[questionIndex];
      if (!question) {
        return;
      }
      const nextOptions = { ...selectedOptions, [question.id]: optionId };
      setSelectedOptions(nextOptions);
      const isLastQuestion = questionIndex + 1 >= questions.length;
      if (isLastQuestion) {
        void submitCollectedAnswers(nextOptions);
      }
    },
    [
      currentEvent,
      eventStep,
      questionIndex,
      selectedOptions,
      submitCollectedAnswers,
    ],
  );

  const goToNextQuestion = useCallback(() => {
    if (eventStep !== "answering" || !currentEvent) {
      return;
    }
    const questions = currentEvent.event.questions;
    const question = questions[questionIndex];
    if (!question || selectedOptions[question.id] === undefined) {
      return;
    }
    setQuestionIndex((index) =>
      index + 1 < questions.length ? index + 1 : index,
    );
  }, [currentEvent, eventStep, questionIndex, selectedOptions]);

  const submitAnswers = useCallback(() => {
    void submitCollectedAnswers(selectedOptions);
  }, [selectedOptions, submitCollectedAnswers]);

  const continueToNextEvent = useCallback(async () => {
    if (
      !gameId ||
      !runId ||
      eventStep !== "event-resolved" ||
      continueInFlightRef.current
    ) {
      return;
    }

    continueInFlightRef.current = true;
    setIsContinuing(true);
    setActionError(null);
    try {
      if (gameFinished || run?.status === "FINISHED") {
        setEventStep("game-over");
        return;
      }

      const nextEvent = await getCurrentEvent(gameId, runId);
      const updatedRun = await getSimulationRun(gameId, runId);
      setRun(updatedRun);
      setCurrentEvent(nextEvent);
      setQuestionIndex(0);
      setSelectedOptions({});
      setResolution(null);
      submitInFlightRef.current = false;
      setEventStep("answering");
    } catch (err) {
      if (isEndOfRunError(err)) {
        try {
          const updatedRun = await getSimulationRun(gameId, runId);
          setRun(updatedRun);
        } catch {
          // Keep the last known run; still transition to game-over.
        }
        setEventStep("game-over");
        return;
      }
      if (err instanceof ApiClientError && err.code === "GAME_NOT_FOUND") {
        clearCurrentGame();
      }
      setActionError(toErrorMessage(err, t));
    } finally {
      continueInFlightRef.current = false;
      setIsContinuing(false);
    }
  }, [eventStep, gameFinished, gameId, run?.status, runId, t]);

  const playAgain = useCallback(async () => {
    if (!gameId || isPlayingAgain) {
      return;
    }
    setIsPlayingAgain(true);
    setActionError(null);
    try {
      const created = await startSimulationRun(gameId);
      saveCurrentRunId(created.run_id);
      navigate(getPlayPath(gameId, created.run_id));
    } catch (err) {
      if (err instanceof ApiClientError && err.code === "GAME_NOT_FOUND") {
        clearCurrentGame();
      }
      setActionError(toErrorMessage(err, t));
      setIsPlayingAgain(false);
    }
  }, [gameId, isPlayingAgain, navigate, t]);

  const questions = currentEvent?.event.questions ?? [];
  const currentQuestion = questions[questionIndex];
  const selectedOptionId = currentQuestion
    ? (selectedOptions[currentQuestion.id] ?? null)
    : null;
  const hasMoreQuestions = questionIndex + 1 < questions.length;
  const dialogue = dialogueFromClientActions(resolution ?? []);

  return {
    gameId,
    game,
    run,
    currentEvent,
    eventStep,
    questionIndex,
    currentQuestion,
    selectedOptionId,
    hasMoreQuestions,
    resolution,
    dialogue,
    partnerBPreferences,
    isLoading,
    error,
    errorCode,
    actionError,
    isContinuing,
    isPlayingAgain,
    refetch,
    selectOption,
    goToNextQuestion,
    submitAnswers,
    continueToNextEvent,
    playAgain,
  };
}
