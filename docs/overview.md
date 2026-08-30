# Couple Life Simulator — Product Overview

## What it is

**Couple Life Simulator** is a life-simulation game for couples, initially built for a bachelor/bachelorette party.

## Core flow

1. **Partner A** answers a set of life situations beforehand; answers are persisted.
2. **Partner B** later joins the game, creates an avatar, and plays through the same situations.
3. Each choice updates the couple's simulation state.
4. Partner B's answers are compared against Partner A's stored answers.
5. The simulation advances through life stages over time.
6. At the end, the app shows final stats, compatibility, a timeline, and a summary of the couple's story.

## V1 priorities

- End-to-end playable flow
- Backend persistence
- Friendly frontend
- Configurable DiceBear avatars (controlled subset of options)
- Visible simulation state during play
- Timeline / history
- Content extensibility without heavy code changes

## Design principles

1. **Vertical slice first.** Ship a working end-to-end flow before building the full game.
2. **Functionality before polish.** Animations and visual polish come after the core game loop works.
3. **Keep it simple in V1.** Basic match/mismatch compatibility is enough; no complex conflict-resolution engine yet.
4. **Avoid excessive granularity.** Use life stages with a reduced set of representative events, not year-by-year simulation.

## When working on the game

### Events and questions

- **Events are data-driven.** Event content and behavior come from configuration, not hardcoded logic.
- **Questions belong to events.** A question is always part of an event, never standalone.
- **Events may contain multiple questions.** A player answers all questions in an event before the event is resolved.
- **Outcomes are determined after all event questions are answered.** Individual answers may accumulate internal variables; the final outcome is evaluated only once the event is complete.

### Rules and data

- **Avoid hardcoded event logic.** Do not implement per-event `if/else` branches in application code.
- **Prefer configurable rules.** Conditions, effects, and outcomes should be defined as data and evaluated by a generic engine.
- **Preserve all player answers.** Store every answer independently of the outcome. Rules may change later without losing historical responses.

### Outcomes and timeline

- **The backend decides the result of an event.** The frontend displays the result; it does not compute it.
- **Event results may be non-deterministic.** The same answers can lead to different outcomes when randomness or weighted rules are configured.
- **Timeline events are generated from outcomes.** Do not create timeline entries separately from event resolution.
- **A single event result may trigger multiple actions on the frontend**, for example:
  - Update simulation stats (compatibility, finances, etc.)
  - Show narrative feedback or comments near the avatars
  - Change avatar appearance or stage-specific avatar guides
  - Add an entry to the timeline

The backend should return a structured list of actions so the frontend can render each one appropriately.

## Current milestone: MVP 0 (extended)

The first production goal validates end-to-end connectivity between frontend, backend, and database — now with a **game lobby** and unified Partner A setup.

### Core flow

```text
/  →  recover current match or go to lobby
Lobby  →  create match (match_name + couple mode)  |  join by match_name
Player A setup  →  name + sex + avatar (create or edit)
Confirmation  →  match summary; return to lobby at any time
```

### Done when

- A match can be created with a unique, human-readable `match_name`.
- Partner A setup collects **name, sex, and avatar** in a single form.
- Match state persists in the API and recovers on refresh (`localStorage` + `GET /api/games/{id}`).
- Another browser or device can join the same match by `match_name`.
- Partner A data can be edited after initial setup.
- UI strings are translatable (English and Spanish locale files).

See [game lobby spec](specs/game-lobby-and-player-a-setup.md) for the full acceptance criteria and API contract.

### Legacy MVP 0 flow (replaced)

The original slice (`/create` → name only → avatar → confirm) is superseded by the lobby flow. Old routes redirect to the new screens for compatibility.

## Further reading

- [Backlog and milestone breakdown](backlog/backlog_simulador_vida_pareja.md) — full product backlog, domain model, and phased implementation plan.
- [Game engine design](specs/game-engine-design.md) — standalone engine architecture, domain model, game loop, and open questions (draft).
- [Engine package skeleton](specs/couple-simulator-engine-package-skeleton.md) — directory layout, modules, and implementation order.
- [Event content model](specs/game-event-content-model.md) — events, questions, conditions, action templates (draft).
- [Rules evaluator implementation plan](specs/rules-evaluator-implementation-plan.md) — phased plan for the standalone `rules_evaluator` package (ConditionExpr, tests, engine integration).
- [Rules evaluator plan prompt](specs/rules-evaluator-implementation-plan-prompt.md) — prompt used to generate the implementation plan above.
- [Game lobby spec](specs/game-lobby-and-player-a-setup.md) — lobby, match name, and Player A setup (implemented).
- [AGENTS.md](../AGENTS.md) — technical conventions for agents and contributors.
- [development-workflow.md](development-workflow.md) — step-by-step workflow for agents.
- [engineering-baseline-backlog.md](backlog/engineering-baseline-backlog.md) — engineering baseline and CI/deployment backlog.
