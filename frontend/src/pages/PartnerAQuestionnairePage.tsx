import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { ChoiceCard } from "../components/play/ChoiceCard";
import { CoupleHeader } from "../components/play/CoupleHeader";
import { EventCard } from "../components/play/EventCard";
import { NextQuestionButton } from "../components/play/NextQuestionButton";
import { PlayLayout } from "../components/play/PlayLayout";
import { QuestionnaireEventNav } from "../components/questionnaire/QuestionnaireEventNav";
import { usePartnerAQuestionnaire } from "../hooks/usePartnerAQuestionnaire";
import { translateContent } from "../shared/play/translateContent";
import { ErrorMessage } from "../shared/ui/ErrorMessage";
import { LoadingState } from "../shared/ui/LoadingState";
import { PrimaryButton } from "../shared/ui/PrimaryButton";

export function PartnerAQuestionnairePage() {
  const { t } = useTranslation();
  const {
    gameId,
    questionnaire,
    currentItem,
    currentQuestion,
    selectedOptionId,
    progressDone,
    progressTotal,
    isComplete,
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
  } = usePartnerAQuestionnaire();

  if (isLoading) {
    return (
      <PlayLayout>
        <LoadingState message={t("common.loading")} />
      </PlayLayout>
    );
  }

  if (error || !questionnaire || !gameId) {
    const showSetupLink = Boolean(gameId && errorCode === "GAME_NOT_READY");
    return (
      <PlayLayout>
        <div className="space-y-4">
          <ErrorMessage message={error ?? t("errors.gameNotFound")} />
          {showSetupLink ? (
            <Link
              to={`/games/${gameId}/player-a`}
              className="text-sm font-medium text-sky-700 hover:text-sky-800"
            >
              {t("game.play.errors.goToSetup")}
            </Link>
          ) : (
            <Link
              to="/lobby"
              className="text-sm font-medium text-sky-700 hover:text-sky-800"
            >
              {t("game.nav.backToLobby")}
            </Link>
          )}
        </div>
      </PlayLayout>
    );
  }

  return (
    <PlayLayout contentClassName="mx-auto max-w-3xl space-y-5 px-6 py-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="font-display text-2xl font-extrabold text-slate-800">
            {t("game.questionnaire.title")}
          </h1>
          <p className="text-sm text-slate-600">
            {t("game.questionnaire.progress", {
              current: progressDone,
              total: progressTotal,
            })}
          </p>
        </div>
      </div>
      {actionError ? <ErrorMessage message={actionError} /> : null}
      {gameId ? (
        <CoupleHeader
          partnerAName={contentParams.partnerAName}
          partnerAAvatar={partnerAAvatar}
          partnerASeed={gameId}
          partnerBAvatar={partnerBAvatar}
          partnerBSeed={partnerBIdentity?.seed ?? `${gameId}-partner-b`}
          partnerBName={contentParams.partnerBName}
          lifeStage="youth"
          age={22}
          partnerBDisplayAge={partnerBIdentity?.displayAge ?? 22}
          childrenCount={0}
        />
      ) : null}
      {isComplete ? (
        <div className="rounded-3xl border border-slate-200 bg-white px-6 py-5">
          <p className="font-display text-lg font-bold text-slate-800">
            {t("game.questionnaire.complete")}
          </p>
          <p className="mt-1 text-sm text-slate-600">
            {t("game.questionnaire.completeHint")}
          </p>
        </div>
      ) : null}
      <QuestionnaireEventNav
        items={questionnaire.items}
        currentEventId={currentItem?.event_id ?? null}
        onSelect={openEvent}
      />
      {currentItem && currentQuestion ? (
        <EventCard
          title={translateContent(
            currentItem.presentation.title,
            contentParams,
          )}
          eventId={currentItem.event_id}
          description={
            currentItem.presentation.description
              ? translateContent(
                  currentItem.presentation.description,
                  contentParams,
                )
              : null
          }
        >
          <p className="text-sm font-medium text-slate-700">
            {t("game.questionnaire.choicesPrompt")}
          </p>
          <p className="text-sm leading-relaxed text-slate-600">
            {translateContent(currentQuestion.text, contentParams)}
          </p>
          {currentQuestion.options.map((option, index) => (
            <ChoiceCard
              key={option.id}
              index={index}
              text={translateContent(option.text, contentParams)}
              selected={selectedOptionId === option.id}
              disabled={isSaving}
              onSelect={() => selectOption(option.id)}
            />
          ))}
          <NextQuestionButton
            onClick={goToNextQuestion}
            disabled={isSaving || selectedOptionId === null}
            label={
              hasMoreQuestions ? undefined : t("game.questionnaire.saveAnswers")
            }
          />
          <div className="flex flex-col gap-2 sm:flex-row">
            {currentItem.status === "skipped" ? (
              <PrimaryButton
                onClick={() => {
                  void unskipEvent();
                }}
                disabled={isSaving}
                className="w-full"
              >
                {t("game.questionnaire.unskipEvent")}
              </PrimaryButton>
            ) : (
              <PrimaryButton
                onClick={() => {
                  void skipEvent();
                }}
                disabled={isSaving}
                className="w-full bg-slate-500 hover:bg-slate-600"
              >
                {t("game.questionnaire.skipEvent")}
              </PrimaryButton>
            )}
          </div>
        </EventCard>
      ) : null}
    </PlayLayout>
  );
}
