---
name: web/api/organisation
description: Org-level admin — members, invites, roles, org-wide files, and device-order requests.
type: api-domain
graph_node: web:api:organisation
sources:
  - { repo: lumi-web-v2, path: src/api/organisation }
  - { repo: lumi-web-v2, path: src/consts/gatewayRoutes.ts }
tags: [web]
---

# web/api/organisation

Fourteen hooks under `lumi-web-v2/src/api/organisation/` powering the `/organisation` admin page. They cover three concern groups: **membership & invites** (member list, simple member list, role edits, send/cancel invite, remove members), **org-wide files** (upload / update / delete / list / list-references), and one **device-order** endpoint that lets an admin submit a new-hardware request to Lumi from the UI.

## The pattern, in a nutshell

```ts
// src/api/organisation/useUploadOrganisationFile.tsx (paraphrased)
const useUploadOrganisationFile = () =>
  useConfiguredMutation({
    getRequestConfig: (request) => {
      const data = new FormData();
      data.append("file", request.file);
      data.append("displayName", request.displayName);
      data.append("category", request.category);
      if (request.fileId !== "") data.append("fileId", request.fileId);
      return {
        url: gatewayRoutes.organisation.uploadFile,
        method: "POST",
        data,
        onUploadProgress: (e) => request.onProgress?.(e)
      };
    },
    errorCodeMap,
    getKeysToInvalidate: () => [[queryCacheKeys.organisationFilesList]]
  });
```

The file-upload hooks are the most interesting — they hand-build `FormData`, thread an `onUploadProgress` callback through axios, and invalidate `organisationFilesList` so the file table repaints after upload. The same pattern shows up in [projects](projects.md) and [imageMoments](imageMoments.md).

## What lives in the folder

| Hook | Purpose |
|------|---------|
| `useMemberList`, `useSimpleMemberList` | Org-member tables (full + minimal). |
| `useGetOpenInvites`, `useSendInvites`, `useCancelInvite` | Invite lifecycle. |
| `useGetOrganisationRoles`, `useEditOrganisationMemberRole` | Role assignment. |
| `useRemoveOrganisationMembers` | Bulk-revoke access. |
| `useUploadOrganisationFile`, `useUpdateOrganisationFile`, `useDeleteOrganisationFile` | File CRUD with progress callbacks. |
| `useListOrganisationFiles`, `useListOrganisationFileReference` | File discovery. |
| `useSubmitNewDevicesOrder` | Submits a device-order request to Lumi sales/ops. |

## Backend mapping

Two route prefixes: `/v2/lumi/account/organisation/*` for membership/invites/roles (account service) and `/v2/lab/organisation/*` for files (lab service). The device-order endpoint is also under the account service. Backend: lumi-API gateway; specific service unclear from frontend code alone.

## Mocks

`lumi-web-v2/mocks/routes/organisation/` — fourteen fixtures (`memberList.ts`, `sendInvites.ts`, `editOrganisationMemberRole.ts`, `uploadFile.ts`, `newDevicesOrder.ts`, …).

## Tests

E2E coverage under the org-admin specs; the file-upload progress is exercised by Storybook for the uploader component.

## See also

- [user](user.md) — invite acceptance and `joinOrganisation` live there
- [projects](projects.md) — same upload-with-progress pattern
- [notifications](notifications.md) — invite notifications
- [devices](devices.md) — pattern reference
