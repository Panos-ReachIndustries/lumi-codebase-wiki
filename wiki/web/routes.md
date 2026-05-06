---
name: Web Routes
description: All 38 routes in lumi-web-v2 organised by feature area, with the API domain each one consumes.
type: route-group
tags: [web]
---

# Web Routes

`lumi-web-v2` ships 38 file-based routes via the Next.js App Router. Everything lives under `src/app/` and is split into two route groups: `(authenticated)/` (31 pages, all wrapped by a Navbar + auth-gated layout in `src/app/(authenticated)/layout.tsx`) and the public group at the top level of `src/app/` (7 pages — login, password reset, accept-invite, the two org-creation flows, the user-cam stream setup page, and the empty `/` redirect handler). Pages are thin server components that `await props.params` and forward to a `"use client"` `main.tsx`; data fetching is done via the TanStack Query hooks in `src/api/<domain>/`.

Below: one section per route slug, in the order they appear in the graph.

## overview

`src/app/(authenticated)/overview/page.tsx` — the landing page after login (the `/` route's `AutoRedirect` sends authenticated users here by default; see `src/components/util/autoRouter.tsx`). The page renders three cards: Favourites, Recent Work, and the Activity Stream. It pulls data via `src/api/user` (favourites, recents) and the activity stream molecule. There's a permissions check on the activity stream — users without `VIEW_ACTIVITY` see a `<PermissionsAlert>` instead. The `WelcomeSplash` component fires on first load. Multi-organisation users see a small badge with the currently selected org name from `useAuth().userState.selectedOrg`.

## lab-ops

`src/app/(authenticated)/lab-ops/page.tsx` — the LabOps dashboard. A single `<Card>` containing a `DevicesDataTable` with a list/grid `ViewToggle`. Permission-gated on `VIEW_DEVICES`; falls back to `<PermissionsAlert>` otherwise. Data comes from `src/api/devices/useGetDeviceList`. Treat this as the lab-wide "what cameras are out there" view; the per-device deep-dive is the [`device`](#device) route.

## notifications-dashboard

`src/app/(authenticated)/notifications-dashboard/page.tsx` — paginated notifications inbox with a left list / right viewer split. Uses `src/api/notifications/useGetNotifications`, `useMarkAsRead`, `useMarkAllAsRead`. Each notification is run through `getNotificationDisplayContent` (in `src/components/ui/notification/`) to produce a typed render object. Pagination uses a `nextToken` cursor; `Load Older Notifications` triggers `refetch`. Selecting a notification auto-marks it read.

## notebook

`src/app/(authenticated)/notebook/page.tsx` — the operator's "Notebook Dashboard". Three stacked data tables: `ProjectsDataTable`, `ProtocolsDataTable`, and `NotebookProtocolsDataTable` (gated behind `featureFlags.v2ProtocolsEnabled`). This page is the entry point for creating new projects/protocols/experiments — most "back" buttons across the app return here. API hooks come from `src/api/projects`, `src/api/protocols`, and `src/api/notebookProtocols`.

## organisation

`src/app/(authenticated)/organisation/page.tsx` — org-admin settings. Three tabs (Files, Users, Devices) using the shadcn `<Tabs>` primitive, each backed by its own data table (`src/app/(authenticated)/organisation/tabs/{files,users,devices}/`). Users tab is gated on `MANAGE_USERS`, devices on `VIEW_DEVICES`, files behind `featureFlags.organisationFilesDataTableEnabled`. Hooks from `src/api/organisation/` (member list) and `src/api/devices/`.

## profile

`src/app/(authenticated)/profile/page.tsx` — the per-user account screen. Pulls the current user via `src/api/user/useUserDetails`. Forms (each their own component): avatar, name, phone number + verification, password, MFA setup, communication preferences, and an "Onboarding" reset button driven by `src/hooks/useOnboardingProgress`. The phone-verification form posts a one-time code via `VerifyPhoneNumberForm`. Almost no permission gates — anyone authenticated can edit their own profile.

## assist

`src/app/(authenticated)/assist/page.tsx` — landing page for AI assist features. Renders an `AgentLauncher` plus either the new `Moments` panel or a `LegacyMoments` fallback (depending on `featureFlags.imageMomentsEnabled`). Calls `useAssistDashboardTour()` for the onboarding overlay. The launcher routes to `/moment/new` or `/moment/image/new` depending on the agent kind.

## project

- `src/app/(authenticated)/project/new/page.tsx`
- `src/app/(authenticated)/project/[projectId]/page.tsx`

`new` is a single-page React Hook Form + Zod flow that posts `useCreateProject` (from `src/api/projects/`) and on success routes to `/project/<id>`. `inviteValidationSchema`/`newProjectValidationSchemaWithUniqueReference` enforce a unique project reference via `useCheckForRefUniqueness`. The detail page fetches via `useGetProject`, hydrates `ProjectOverviewPageHeader` + `ProjectOverviewTabs`, and lists experiments via `ExperimentsDataTable`. Both pages are gated on `MANAGE_PROJECTS` (create) and `VIEW_PROJECTS` (view); access also depends on project membership. See [api/projects](api-domains/projects.md).

## experiment

- `src/app/(authenticated)/experiment/new/page.tsx`
- `src/app/(authenticated)/experiment/[experimentId]/page.tsx`
- `src/app/(authenticated)/experiment/[experimentId]/live/page.tsx`
- `src/app/(authenticated)/experiment/[experimentId]/device-selection/page.tsx`

Heaviest route in the app. `new` is a 2-step `<MultiStep>` wizard (inputs → select-protocol) that calls `useCreateExperiment` from `src/api/experiments/`. The overview page uses `useGetExperiment` and tabs between Overview and Results, with permission checks via `getExperimentPageSettings`. `device-selection` mounts after creation: it pulls `useGetDeviceList`, `useAddInternalResources`, and on confirm calls `useUpdateExperimentStatus({status: live})` to flip the experiment from pending to live.

`live/page.tsx` is the workhorse — see `src/app/(authenticated)/experiment/[experimentId]/live/main.tsx`. It mounts a `<Pinboard>` of widgets (devices, monitors, notepad, resources, comments) wired through `useExperimentData` (which calls `useGetExperiment`, `useGetExperimentStatus`, `useUpdateExperimentStatus`) and `useExperimentLayout`. Voice control (`useVoiceControl`), the global date-time provider, and per-widget "AI agent" creation all live here. The status feed is sourced from `arbiter v2` via the gateway WebSocket — that's the `PROTOCOL_ARBITER_STATUS_TOPIC` subscription that drives the live experiment indicator. See [api/experiments](api-domains/experiments.md).

## workspace

- `src/app/(authenticated)/workspace/new/page.tsx`
- `src/app/(authenticated)/workspace/[workspaceId]/page.tsx`
- `src/app/(authenticated)/workspace/[workspaceId]/live/page.tsx`
- `src/app/(authenticated)/workspace/[workspaceId]/device-selection/page.tsx`

Workspaces are the experiment cousin used for ad-hoc / non-protocol-driven captures. `new` has two flows behind `featureFlags.newWorkspaceFlowEnabled`: a draft-then-finalise flow (uses `useCreateWorkspaceDraft` + `useFinaliseWorkspace`) and a single-step `useCreateWorkspace`. The draft flow lets the user attach references, external links, and clipped data tables before publishing. The detail page (`useGetWorkspace`) has four tabs — Overview, Data, Live, Replayer — switched via `WORKSPACE_TABS`. `live/main.tsx` mirrors the experiment Pinboard architecture (same `useWorkspaceData` + `useWorkspaceLayout` pattern, same `<Pinboard>` widget host, same voice-control wiring), but adds a `WellPlatePolygonOverlay` and a Lumi-Live section. `device-selection` mirrors the experiment one. See [api/workspaces](api-domains/workspaces.md).

## record

- `src/app/(authenticated)/record/new/page.tsx`
- `src/app/(authenticated)/record/[recordId]/page.tsx`

A record is a notebook entry attached to a project (and optionally a protocol). `new` is a 4-step `<MultiStep>` wizard (Details → External Data → References → Notes) that uses `useCreateRecordDraft` then `useCreateRecord` (`src/api/records/`). Step 2 hosts the `useClippedTables` hook for clipping XLSX ranges via the `externalDataPanel` molecule. The detail page calls `useGetRecord`, `useGetRecordFiles`, `useGetRecordDataTables`, renders a `MarkdownEditor` for notes, and a `ReferencesCard` for cross-links to projects/protocols.

## device

`src/app/(authenticated)/device/[deviceId]/page.tsx` — single-device deep-dive: live + archive video player, comment thread, AI-agent panel, media gallery, and (for user-cam devices) a setup alert. The data orchestration lives in `useDevicePlayerData` (`src/api/devices/useGetDevice` + `useGetVideoManifest` + `useGetYearlyManifest`) and `useAiAgentsData` (`src/api/aiAgents/`). The page subscribes to the gateway WebSocket via `useMessageWebSocket` to react to `videoStreamStatus` change notifications and refetch device info on connect/disconnect. Yearly manifests are fetched once per year, video manifests per date. Backend mapping: `useGetDevice` → `monitor_relay` (Go service in Lumi-AI-Continuous), and the yearly/video manifests resolve to signed S3 URLs that point at the device's archive bucket. See [api/devices](api-domains/devices.md) — that's the exemplar API domain.

## protocol

- `src/app/(authenticated)/protocol/new/page.tsx`
- `src/app/(authenticated)/protocol/[protocolId]/page.tsx`
- `src/app/(authenticated)/protocol/v2/new/page.tsx`
- `src/app/(authenticated)/protocol/v2/[protocolId]/page.tsx`
- `src/app/(authenticated)/protocol/v2/selectAndPreview/page.tsx`

Two generations of protocol live side-by-side. The v1 `new` page uses `gatewayRoutes.protocol.convert` over a websocket (`useWebsocket`) to track an OCR/parse pipeline and routes to `/protocol-version/<id>` on completion, optionally auto-attaching to an experiment via `useUpdateExperiment`. The v1 detail page lists immutable versions in a `DataTable` with `useCreateProtocolVersion` for new drafts. The v2 flow uses `src/api/notebookProtocols/` (`useGetNotebookProtocol`, `useGetNotebookProtocolVersion`) and switches the parse-progress notifications over to the unified `messages` websocket via `useMessageWebSocket`. `selectAndPreview` is a small picker page that lets a user choose a notebook protocol + version and open it in a `<ProtocolModal>` for preview. Permission-gated on `VIEW_PROTOCOLS`/`MANAGE_PROTOCOLS`. See [api/protocols](api-domains/protocols.md) and [api/notebookProtocols](api-domains/notebookProtocols.md).

## protocol-version

`src/app/(authenticated)/protocol-version/[versionId]/page.tsx` — the v1 protocol-version editor / viewer. Pulls `useGetProtocolVersion` from `src/api/protocols/`. Gated on `VIEW_PROTOCOLS`; if the version is still a draft and the user isn't the author, the page falls back to a `<NotAuthorised>` panel with the "draft not version author" copy. Hosts the `useProtocolTour` onboarding tour. The actual editor body lives in `_components/Content.tsx`.

## moment

- `src/app/(authenticated)/moment/new/page.tsx`
- `src/app/(authenticated)/moment/[momentType]/[momentId]/page.tsx`
- `src/app/(authenticated)/moment/image/new/page.tsx`
- `src/app/(authenticated)/moment/image/[imageAiAgentType]/[imageMomentId]/page.tsx`

A "moment" is an AI-agent-driven capture — either a video moment (live or archive) or a single image moment. The video `new` page is a multi-step `<WizardProvider>` flow (select-agent → video-type → device(s) → optional archive-date-range → agent-specific setup → title); state is split across `useMomentWizardState`, `useMomentWizardOperations`, and `useMomentWizardDeviceSetup`. The dynamic agent-setup step is generated per agent kind via `SetupAgentStep`. The detail page (`[momentType]/[momentId]`) is the playback + analytics view: `useGetMoment` from `src/api/moments/`, AI-agent autostop banner, alerts, a floating timeline, a sidebar of devices, and a results-context provider. The image-moment flow is much smaller: `SelectAgent → NameImageMoment` and `useCreateImageMoment` from `src/api/imageMoments/`. Backend mapping: video moments resolve to records in arbiter and the AI-agents service; image moments live in `aiSingular`. See [api/moments](api-domains/moments.md), [api/imageMoments](api-domains/imageMoments.md), [api/aiAgents](api-domains/aiAgents.md), [api/aiSingular](api-domains/aiSingular.md).

## public

The seven unauthenticated pages live directly under `src/app/`:

- `src/app/page.tsx` — empty render; `AutoRedirect` (`src/components/util/autoRouter.tsx`) routes the user to `/login` or `/overview` based on auth state.
- `src/app/login/page.tsx` — email/password + MFA. Reads an `impersonationCode` query param so admins can drop into an account; `LoginForm` and `MfaForm` live next to it.
- `src/app/login/reset/page.tsx` — splits between `RequestReset` (no `?code`) and `ResetPassword` (with `?code`).
- `src/app/accept-invite/page.tsx` — validates an invite code via `useValidateAccessCode` and either registers a new user (`useAcceptInvite`) or joins an existing user to the org (`useJoinOrganisation`).
- `src/app/create-starter-org/page.tsx` and `src/app/create-pro-org/page.tsx` — the two paid-tier signup flows; both use `useValidateAccessCode` plus the corresponding org-creation hook in `src/api/user/`.
- `src/app/stream/page.tsx` — the user-cam pairing screen. Mounts `UserCamAuth` until a code+config is collected, then `UserCamSetUp`. The `(authenticated)` layout redirect explicitly skips this path so a logged-in user can still pair a phone camera.

These pages mount under `src/app/unauthenticatedLayout.tsx`; see `src/consts/unauthenticatedRoutes.ts` for the exact list `AutoRedirect` checks.

## See also

- [API domains index](api-domains/) — every `src/api/<domain>/` folder has a wiki page
- [Kubb pipeline](kubb-pipeline.md) — how `src/types/generated/` ends up powering the hooks the routes call
- `src/app/(authenticated)/layout.tsx` and `src/app/unauthenticatedLayout.tsx` — the two layout shells
