import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { ChoiceCard } from "../components/play/ChoiceCard";
import { CoupleHeader } from "../components/play/CoupleHeader";
import { DialogueBubble } from "../components/play/DialogueBubble";
import { EventCard } from "../components/play/EventCard";
import { EventContinueButton } from "../components/play/EventContinueButton";
import { GameOverScreen } from "../components/play/GameOverScreen";
import { HouseholdPanel } from "../components/play/HouseholdPanel";
import { LifeStoryPanel } from "../components/play/LifeStoryPanel";
import { NextQuestionButton } from "../components/play/NextQuestionButton";
import { PlayLayout } from "../components/play/PlayLayout";
import { StatsBar, type StatsBarValues } from "../components/play/StatsBar";
import { useSimulationPlay } from "../hooks/useSimulationPlay";
import type { SimulationState } from "../services/simulationService";
import { isGameReadyToPlay } from "../shared/gameNavigation";
import { resolvePlayPartnerB } from "../shared/play/resolvePlayPartnerB";
import { translateContent } from "../shared/play/translateContent";
import { ErrorMessage } from "../shared/ui/ErrorMessage";
import { LoadingState } from "../shared/ui/LoadingState";

function statsFromState(state: SimulationState): StatsBarValues {
  return {
    compatibility: state.compatibility,
    finances: state.finances,
    children: state.children,
    quality_of_life: state.quality_of_life,
    wellness: state.wellness,
  };
}

export function PlayPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const {
    gameId,
    game,
    run,
    currentEvent,
    eventStep,
    currentQuestion,
    selectedOptionId,
    hasMoreQuestions,
    dialogue,
    isLoading,
    error,
    errorCode,
    actionError,
    isContinuing,
    isPlayingAgain,
    selectOption,
    goToNextQuestion,
    continueToNextEvent,
    playAgain,
  } = useSimulationPlay();

  useEffect(() => {
    if (!game || !gameId) {
      return;
    }
    if (!isGameReadyToPlay(game)) {
      navigate(`/games/${gameId}/player-a`, { replace: true });
    }
  }, [game, gameId, navigate]);

  if (isLoading) {
    return (
      <PlayLayout>
        <LoadingState message={t("common.loading")} />
      </PlayLayout>
    );
  }

  if (error || !game || !run || !gameId) {
    const showSetupLink = Boolean(gameId && errorCode === "GAME_NOT_READY");
    return (
      <PlayLayout>
        <div className="space-y-4">
          <ErrorMessage message={error ?? t("errors.gameNotFound")} />
          {showSetupLink ? (
            <Link
              to={`/games/${gameId}/player-a`}
              className="text-sm font-medium text-indigo-600 hover:text-indigo-700"
            >
              {t("game.play.errors.goToSetup")}
            </Link>
          ) : (
            <Link
              to="/lobby"
              className="text-sm font-medium text-indigo-600 hover:text-indigo-700"
            >
              {t("game.nav.backToLobby")}
            </Link>
          )}
        </div>
      </PlayLayout>
    );
  }

  const stats = statsFromState(run.state);
  const partnerAName = game.partner_a.name ?? "";
  const partnerB = resolvePlayPartnerB(game, run.state.age);
  const partnerBName = partnerB.nameFromApi ?? t("game.play.partnerB");
  const partnerBAge = partnerB.displayAge;

  if (eventStep === "game-over") {
    return (
      <GameOverScreen
        partnerAName={partnerAName}
        partnerBName={partnerBName}
        partnerAAge={run.state.age}
        partnerBAge={partnerBAge}
        stats={stats}
        timeline={run.timeline}
        onPlayAgain={() => {
          void playAgain();
        }}
        playAgainDisabled={isPlayingAgain}
        errorMessage={actionError}
      />
    );
  }

  const showChoices = eventStep === "answering" || eventStep === "submitting";
  const choicesDisabled = eventStep !== "answering";

  return (
    <PlayLayout progressFillPercent={Math.min(100, run.events_played * 20)}>
      <CoupleHeader
        partnerAName={partnerAName}
        partnerAAvatar={game.partner_a.avatar_config ?? {}}
        partnerASeed={gameId}
        partnerBAvatar={partnerB.avatarConfig}
        partnerBSeed={partnerB.seed}
        partnerBName={partnerBName}
        lifeStage={run.state.life_stage}
        age={run.state.age}
        partnerBDisplayAge={partnerB.displayAge}
        childrenCount={run.state.children}
      />
      <StatsBar values={stats} />
      <HouseholdPanel housing={run.state.housing} mascot={run.state.mascot} />
      {actionError ? <ErrorMessage message={actionError} /> : null}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_300px] lg:items-start">
        {currentEvent ? (
          <EventCard
            title={translateContent(currentEvent.event.title)}
            description={
              currentEvent.event.description
                ? translateContent(currentEvent.event.description)
                : null
            }
          >
            {showChoices && currentQuestion ? (
              <>
                <p className="text-sm font-medium text-slate-700">
                  {t("game.play.choicesPrompt")}
                </p>
                <p className="text-sm leading-relaxed text-slate-600">
                  {translateContent(currentQuestion.text)}
                </p>
                {currentQuestion.options.map((option, index) => (
                  <ChoiceCard
                    key={option.id}
                    index={index}
                    text={translateContent(option.text)}
                    selected={selectedOptionId === option.id}
                    disabled={choicesDisabled}
                    onSelect={() => selectOption(option.id)}
                  />
                ))}
                {hasMoreQuestions ? (
                  <NextQuestionButton
                    onClick={goToNextQuestion}
                    disabled={choicesDisabled || selectedOptionId === null}
                  />
                ) : null}
              </>
            ) : null}
            {eventStep === "event-resolved" ? (
              <>
                {dialogue.map((line, index) => (
                  <DialogueBubble
                    key={`${line.speaker}-${index}`}
                    speaker={line.speaker}
                    text={line.text}
                    partnerAName={partnerAName}
                    partnerBName={partnerBName}
                  />
                ))}
                <EventContinueButton
                  onClick={() => {
                    void continueToNextEvent();
                  }}
                  disabled={isContinuing}
                />
              </>
            ) : null}
          </EventCard>
        ) : (
          <LoadingState message={t("common.loading")} />
        )}
        <LifeStoryPanel timeline={run.timeline} stats={stats} />
      </div>
    </PlayLayout>
  );
}
