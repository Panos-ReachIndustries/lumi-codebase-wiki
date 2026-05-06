---
name: web/api/records
description: Records — finalised, immutable result snapshots. CRUD plus file and data-table uploads.
type: api-domain
graph_node: web:api:records
sources:
  - { repo: lumi-web-v2, path: src/api/records }
  - { repo: lumi-web-v2, path: src/consts/gatewayRoutes.ts }
tags: [web]
---

# web/api/records

Nine hooks under `lumi-web-v2/src/api/records/`. Records are the **finalised** outputs of an experiment / workspace — a frozen snapshot users archive for later reference, reporting, or audit. This domain covers the create-draft → finalise lifecycle and the file / data-table attachments hung off a record. The `(authenticated)/record/[recordId]/page.tsx` route is the consumer.

Note these hooks use `.ts` extensions (no JSX) — they're pure data hooks with no inline render fallbacks, the convention this codebase uses for lighter API hooks.

## The pattern, in a nutshell

```ts
// src/api/records/useGetRecord.ts (paraphrased)
const useGetRecord = (params, opts) =>
  useConfiguredQuery<GetRecordResponse>({
    getRequestConfig: () => ({
      url: gatewayRoutes.record.get,
      params
    }),
    queryOptions: {
      enabled: opts?.enabled ?? true,
      queryKey: [queryCacheKeys.record, params.recordId]
    }
  });
```

Standard recipe. The upload mutations build `FormData` exactly the way [organisation](organisation.md) and [projects](projects.md) do — same `onUploadProgress` callback wired through axios, same `getKeysToInvalidate` returning the per-record cache key so the file/data-table tables repaint.

## What lives in the folder

| Hook | Purpose |
|------|---------|
| `useCreateRecordDraft`, `useCreateRecord` | Two-step creation: draft a record, then finalise it. |
| `useGetRecord` | Fetch a record by ID. Powers the record page. |
| `useGetRecordFiles`, `useGetRecordDataTables` | List attachments. |
| `useUploadRecordFile`, `useDeleteRecordFile` | Generic file CRUD with upload progress. |
| `useUploadRecordDataTable`, `useDeleteRecordDataTable` | Structured data-table CRUD (CSV / similar tabular uploads). |

## Backend mapping

Routes under `/v2/lab/record/*`, served by the lumi-API gateway. The lab-API persists the record and its attachments. Records are read-only after finalise — the two-step `createDraft` → `create` pattern is what enforces that. Backend: lumi-API gateway; specific service unclear from frontend code alone.

## Mocks

`lumi-web-v2/mocks/routes/records/` — nine fixtures (`createRecord.ts`, `createRecordDraft.ts`, `getRecord.ts`, `getRecordFiles.ts`, `getRecordDataTables.ts`, `uploadRecordFile.ts`, `uploadRecordDataTable.ts`, `deleteRecordFile.ts`, `deleteRecordDataTable.ts`).

## Tests

E2E specs cover the create-draft / finalise / attach-file flow.

## See also

- [projects](projects.md) — records belong to a project, listed by `useGetProjectRecords`
- [experiments](experiments.md), [workspaces](workspaces.md) — typical sources of a record
- [organisation](organisation.md) — same upload-with-progress recipe
- [devices](devices.md) — pattern reference
