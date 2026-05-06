---
name: Components Library
description: shadcn/ui-derived UI primitives, layout shells, and molecules in lumi-web-v2/src/components/.
type: architecture
tags: [web, components]
---

# Components Library

Everything visual in `lumi-web-v2` is composed from `src/components/`. Five subdirectories, in rough order of how often you'll touch them:

- `ui/` — 48 base primitives + 18 nested folders (e.g. `ui/dataTable/`, `ui/multiStep/`, `ui/calendar/`). These are mostly shadcn/ui components vendored into the repo, then customised. Examples: `button.tsx`, `card.tsx`, `tabs.tsx`, `dialog.tsx`, `dataTable/`, `notification/`. This is the canonical place to look before writing any new UI.
- `layout/` — 10 entries: `pageContainer.tsx`, `pageFooter.tsx`, `contentColumn.tsx`, `notAuthorised.tsx`, `errorFallback.tsx`, `skeletonList.tsx`, plus the `navbar/`, `pinboard/` and `elementHeader/` molecules. These are the page-shell wrappers — every authenticated route is wrapped in a `PageContainer` from here.
- `molecules/` — 34 composite components built on top of the primitives. Things like `cards/collapsibleCardBasic.tsx`, `lists/recentsList.tsx`, `addMembers/`, `markdownEditor/`, `video/`, `wellPlate/`, `externalDataPanel/`. If a piece of UI is bigger than a primitive but isn't a full page section, it belongs here.
- `util/` — 5 non-visual helpers: `autoRouter.tsx` (auth-aware redirect), `globalContextTree.tsx` (the QueryClient + auth + websocket + posthog provider stack), `authMask.tsx`, `scroller.tsx`, `accessibilityFunctions.ts`.
- `debug/` — single file, `debugViewportInfo.tsx`, a corner overlay that prints the active Tailwind breakpoint during development.

## shadcn/ui setup

`lumi-web-v2/components.json` configures the shadcn generator: `style: default`, `tailwind.baseColor: slate`, `cssVariables: true`, `aliases.components: @/components`, `aliases.utils: @/lib/tools` (so generated components import `cn` from there). New primitives are pulled in with `yarn dlx shadcn-ui@latest add <component>` — `lumi-web-v2/CLAUDE.md` is explicit that this is `yarn dlx`, never `npx`. Output lands in `src/components/ui/`, after which it's free to be edited in place.

## Tailwind v4 + CVA

Variant-heavy primitives use `class-variance-authority`. `src/components/ui/button.tsx` is the cleanest reference: a `cva()` call defines `variant` (default / destructive / outline / secondary / ghost / link / compressedIcon), `size` (a dozen options including `iconXSm` through `floatingActionWithIcon`), and an `outline: circle` toggle, then `Button` and `LinkButton` consume those variants. `pageContainer.tsx` shows the same pattern at the layout level. Tailwind v4 is wired through `@tailwindcss/postcss`; tokens like `type-h1`, `v-stack`, `h-stack`, `content-width-max` are project-wide custom utilities.

## Storybook

84 `*.stories.tsx` files are co-located alongside their components (e.g. `ui/loading/loading.stories.tsx`, `ui/_stories/dialog.stories.tsx`). `.storybook/main.ts` globs `../src/**/*.stories.@(js|jsx|ts|tsx)` and resolves the `@/` alias to `src/`. Run `yarn storybook` for a local 6006 instance; the `@storybook/addon-designs` addon is installed so stories can deep-link to Figma frames. Stories are required for new UI primitives (per `lumi-web-v2/CLAUDE.md`).

## Where to add new things

`lumi-web-v2/CLAUDE.md` codifies the rule: for primitives, **always reuse `components/ui/`** before reaching for raw HTML. A `<Button>` is never a `<button>`; a card is never a hand-rolled `<div>`. When you do need something new:

- If it's a generic primitive (a new variant of an existing one, or a brand-new atomic thing): extend the existing `ui/` component via props/CVA variants first, and only fork a new file if it's fundamentally different.
- If it's a generic composite (used in 2+ places, no domain coupling): add it to `components/molecules/` in the most specific subfolder (`buttons/`, `cards/`, `lists/`, etc.).
- If it's coupled to one route only: keep it in that route's `_components/` folder (e.g. `src/app/(authenticated)/experiment/[experimentId]/live/_components/`).

When unsure, search `src/components/molecules/` first — there's a good chance the thing already exists.

## See also

- [routes.md](routes.md) — the routes that consume these components
- `lumi-web-v2/CLAUDE.md` — full code-style rules (component naming, import order, etc.)
- `lumi-web-v2/docs/styling.md` — Storybook + responsive guide
