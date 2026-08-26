---
name: react-components
description: Build React UI with TypeScript, functional components, Tailwind CSS, and composable game components. Use when creating or modifying React components, pages, hooks, frontend UI, Tailwind styles, or when the user mentions React, TypeScript, or frontend components.
---

# React Components

## Before You Start

1. **Read `AGENTS.md`** at the project root. Follow project-specific frontend rules (i18n, file layout, thin pages) in addition to this skill.
2. Inspect existing `frontend/src/` structure and match established patterns before adding new code.

## Core Rules

When creating React components:

- Use TypeScript.
- Use functional components.
- Prefer composition over large components.
- Use Tailwind.
- Keep components under 200 lines.
- Avoid unnecessary abstractions.
- Create reusable game UI components.

## Project Conventions

| Concern | Rule |
|---------|------|
| Types | TypeScript strictly; avoid `any` |
| Pages | Keep thin — move logic into hooks and services |
| API calls | Dedicated service layer (`services/`), not inline in components |
| User-facing text | i18n keys via `react-i18next` — no hardcoded display strings |
| Reusable UI | `shared/` or `components/` depending on scope |

```tsx
// Good
const { t } = useTranslation();
<h1>{t("game.create.title")}</h1>

// Bad
<h1>Create a new game</h1>
```

## File Layout

```
frontend/src/
├── components/   # feature-specific UI
├── pages/        # route-level, thin wrappers
├── services/     # API clients
├── hooks/        # state and side-effect logic
├── shared/       # reusable UI and utilities
└── locales/      # translation files
```

| Situation | Location |
|-----------|----------|
| Reused across features | `shared/` |
| Specific to one feature | `components/` or colocated with the feature |
| Data fetching / API | `services/` + custom hooks |

## Composition

Split when a component grows or mixes concerns:

```tsx
// Page — orchestration only
export function GameCreatePage() {
  const { form, onSubmit } = useCreateGame();
  return (
    <GameLayout>
      <PartnerNameForm value={form.name} onChange={form.setName} />
      <AvatarBuilder config={form.avatar} onChange={form.setAvatar} />
      <PrimaryButton onClick={onSubmit}>{t("game.create.submit")}</PrimaryButton>
    </GameLayout>
  );
}
```

**Split signals:** file approaches 200 lines, multiple unrelated responsibilities, or repeated JSX blocks.

**Do not split** one-off wrappers or tiny helpers used in a single place — keep them inline.

## Tailwind

- Use utility classes directly on elements; avoid custom CSS unless Tailwind cannot express the style.
- Extract repeated class strings into a component, not a one-off `cn()` helper for a single use.
- Prefer semantic game components (`StatBar`, `OptionCard`, `AvatarPreview`) over copying the same utility clusters.

```tsx
type StatBarProps = {
  label: string;
  value: number;
  max?: number;
};

export function StatBar({ label, value, max = 100 }: StatBarProps) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm text-gray-600">
        <span>{label}</span>
        <span>{value}</span>
      </div>
      <div className="h-2 rounded-full bg-gray-200">
        <div className="h-2 rounded-full bg-indigo-500" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
```

## Reusable Game UI

Favor small, composable primitives for the simulation domain:

| Component type | Examples |
|----------------|----------|
| Layout | `GameLayout`, `Panel`, `Section` |
| Game chrome | `StatBar`, `LifeStageBadge`, `TimelineEntry` |
| Interaction | `OptionCard`, `PrimaryButton`, `AvatarOptionGrid` |
| Feedback | `LoadingState`, `ErrorMessage` |

Build from composition:

```tsx
<OptionCard selected={isSelected} onSelect={onSelect}>
  <OptionCard.Title>{t(option.labelKey)}</OptionCard.Title>
  <OptionCard.Description>{t(option.descriptionKey)}</OptionCard.Description>
</OptionCard>
```

Only add variant props or context when multiple call sites need the same behavior.

## Hooks and Logic

- **Components:** render UI and wire events.
- **Hooks:** form state, derived values, side effects.
- **Services:** HTTP calls and response mapping.

```tsx
// hooks/useCreateGame.ts
export function useCreateGame() {
  const [name, setName] = useState("");
  const createGame = useCallback(async () => {
    return gameService.create({ partnerAName: name });
  }, [name]);
  return { name, setName, createGame };
}
```

## Checklist

- [ ] Read `AGENTS.md` if present
- [ ] Functional component with typed props (no `any`)
- [ ] File under 200 lines; split by composition if larger
- [ ] Tailwind for styling; no unnecessary abstractions
- [ ] User-visible strings use i18n keys
- [ ] API calls in `services/`, not in components
- [ ] Reusable game UI extracted to `shared/` when used in more than one place
- [ ] Page stays thin; logic in hooks
