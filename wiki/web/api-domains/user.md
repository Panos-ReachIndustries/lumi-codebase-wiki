---
name: web/api/user
description: Auth, user profile, MFA, phone verification, recents, favourites, onboarding — the largest non-workspaces domain.
type: api-domain
graph_node: web:api:user
sources:
  - { repo: lumi-web-v2, path: src/api/user }
  - { repo: lumi-web-v2, path: src/consts/gatewayRoutes.ts }
tags: [web]
---

# web/api/user

Twenty-nine hooks at `lumi-web-v2/src/api/user/` covering everything tied to the authenticated user identity: auth (login / logout / token refresh), MFA setup and verification, phone-number add/verify, password reset and update, organisation join / switch, profile updates and avatar, terms acceptance, onboarding flags, favourites, recents, and the activity stream parser. It's also the only domain that talks to the **internal** Next.js API routes (rather than the gateway) for login.

## The pattern, in a nutshell

Most hooks follow the standard recipe. The auth ones are the exception — they hit Next.js internal API routes so the server can set httpOnly cookies:

```ts
// src/api/user/useLogin.tsx (paraphrased)
const useLogin = () =>
  useConfiguredMutation<LoginRequest, LoginResponse>({
    getRequestConfig: (request) => ({
      url: internalApiRoutes.user.login,
      method: "POST",
      data: request
    }),
    errorCodeMap,
    isGatewayRequest: false  // <-- bypasses gateway prefix
  });
```

`isGatewayRequest: false` flips the URL builder in `useRemoteData.ts` to skip the `globalConfig.urls.gateway.general` prefix and hit `/api/...` instead — a deliberate choice for any flow that needs to set or read cookies on the same origin.

A profile/data hook looks ordinary:

```ts
// src/api/user/useRecentsList.tsx (paraphrased)
const useRecentsList = () =>
  useConfiguredQuery<GetRecentsResponse>({
    getRequestConfig: () => ({ url: gatewayRoutes.user.recentsList }),
    queryOptions: { staleTime: apiConfig.queryStaleTimes.short }
  });
```

The `recentsList` hook also post-processes the response (filters by allowed element types via `recentableElements`, sorts by `addedAt`) — a reminder that hooks are allowed to shape data, they aren't required to be pass-through.

## What lives in the folder

A representative slice (29 total — `ls lumi-web-v2/src/api/user/` for the rest):

| Group | Hooks |
|-------|-------|
| Auth | `useLogin`, `useLogout`, `useGetAuthToken`, `useValidateAccessCode` |
| MFA | `useInitiateMfa`, `useActivateMfa`, `useVerifyMfa` |
| Password | `useRequestPasswordReset`, `useSubmitPasswordReset`, `useSubmitPasswordSet` |
| Phone | `useAddPhoneNumber`, `useVerifyPhoneNumber` |
| Profile | `useUserDetails`, `useSubmitUserUpdate`, `useSubmitAvatarUpdate`, `useSubmitAvatarRemove`, `useAcceptTerms` |
| Org join/switch | `useAcceptInvite`, `useJoinOrganisation`, `useSwitchOrganisation`, `useCreateProOrganisation`, `useCreateStarterOrganisation` |
| Engagement | `useFavouritesList`, `useAddFavourite`, `useRemoveFavourite`, `useRecentsList`, `useAddRecent` |
| Onboarding | `useGetOnboarding`, `useUpdateOnboarding` |
| Activity stream | `useActivityStream/index.tsx` + `parse.tsx` (and `parse.test.tsx` — one of the few hook-level tests in the repo) |

## Backend mapping

Two prefixes: `/v2/lumi/account/user/*` for the account service (auth, profile, org-join), and `/v2/lab/activity/stream` for the activity stream (lab service). Login alone short-circuits to `/api/...` Next.js routes. Backend: lumi-API gateway; specific service unclear from frontend code alone.

## Mocks

`lumi-web-v2/mocks/routes/user/` — 25+ fixtures, near-1:1 with the route list.

## Tests

`useActivityStream/parse.test.tsx` is the rare hook-level unit test (the parser is logic-heavy enough to deserve coverage). Everything else is E2E-tested via auth flows under `test/e2e/auth.setup.ts`, `accept-invite.serial.spec.ts`, and `create-org/`.

## See also

- [organisation](organisation.md) — invite-sending side; user is invite-receiving side
- [notifications](notifications.md) — alert delivery uses verified phone numbers from here
- [devices](devices.md) — pattern reference
