---
name: web/api/projects
description: Project CRUD plus file management, member management, references, and child-resource listings (experiments / workspaces / records / protocol versions).
type: api-domain
graph_node: web:api:projects
sources:
  - { repo: lumi-web-v2, path: src/api/projects }
  - { repo: lumi-web-v2, path: src/consts/gatewayRoutes.ts }
tags: [web]
---

# web/api/projects

Nineteen hooks at `lumi-web-v2/src/api/projects/`. Projects are the top-level container in the lab data model — every experiment, workspace, record, and protocol version belongs to a project. This domain handles project CRUD, project-membership editing, file uploads, references (linked URLs / DOIs), and the listing endpoints that the project page uses to render its tabs (experiments, workspaces, records, protocol versions, resources).

## The pattern, in a nutshell

```ts
// src/api/projects/useGetProject.tsx (paraphrased)
const useGetProject = (params, opts) =>
  useConfiguredQuery<ProjectResponse>({
    getRequestConfig: () => ({
      url: gatewayRoutes.projects.getProject,
      params
    }),
    queryOptions: {
      queryKey: [queryCacheKeys.project, params.projectId],
      enabled: opts?.enabled ?? true
    }
  });
```

`useGetProject` returns the full project bundle (metadata, members, summary). The list-X hooks (`useGetProjectExperiments`, `useGetProjectWorkspaces`, etc.) are paginated and key by `[<resource>List, projectId]` so each tab caches independently. Mutations invalidate `[project, projectId]` — single source of truth.

## What lives in the folder

A representative slice (`ls lumi-web-v2/src/api/projects/` for the rest):

| Hook | Purpose |
|------|---------|
| `useCreateProject`, `useGetProject`, `useGetProjects`, `useUpdateProject`, `useArchiveProject` | Core CRUD. |
| `useAddProjectMembers`, `useRemoveProjectMember` | Membership. |
| `useUploadFile`, `useDeleteFile`, `useGetProjectFilesList` | File management with upload-progress callback. |
| `useGetProjectReferencesList`, `useAddProjectReferences`, `useRemoveProjectReference`, `useUpdateProjectReference` | External-reference management (DOIs, URLs). |
| `useGetProjectExperiments`, `useGetProjectWorkspaces`, `useGetProjectRecords`, `useGetProjectProtocolVersions` | Tab-content listings. |
| `useListResources` | Generic resource lookup spanning the project. |

## Backend mapping

Routes under `/v2/lab/project/*` and `/v2/lab/resources/*` (for the cross-project resource list). The lab-API owns the project record and proxies the listing endpoints to the underlying experiment / workspace / record / protocol services. Backend: lumi-API gateway; specific service unclear from frontend code alone.

## Mocks

`lumi-web-v2/mocks/routes/projects/` — nineteen fixtures (`createProject.ts`, `getProject.ts`, `getProjectExperiments.ts`, `uploadFile.ts`, `addProjectMembers.ts`, `listProjectResources.ts`, …).

## Tests

E2E flows exercise project creation, membership, and file upload. No dedicated hook tests.

## See also

- [experiments](experiments.md), [workspaces](workspaces.md), [records](records.md), [protocols](protocols.md) — the children listed by this domain
- [organisation](organisation.md) — sibling admin layer one level up
- [devices](devices.md) — pattern reference
