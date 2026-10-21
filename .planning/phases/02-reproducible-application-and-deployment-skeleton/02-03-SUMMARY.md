---
phase: 02-reproducible-application-and-deployment-skeleton
plan: "03"
status: complete
subsystem: frontend
tags: [astro, react, static, synthetic]
requires: [02-00, 02-02]
provides: [frozen-static-frontend, strict-build-collection, selected-react-island]
affects: [02-04, 02-13, 02-17]
tech-stack:
  added: [Astro 7.4.1, React 19.3.1, React DOM 19.3.1, TypeScript 6.0.3]
  patterns: [build-time-content-collection, selected-client-hydration]
key-files:
  created: [frontend/package.json, frontend/package-lock.json, frontend/astro.config.mjs, frontend/tsconfig.json, frontend/src/content.config.ts, frontend/src/content/probes/skeleton.md, frontend/src/components/BuildProbe.tsx, frontend/src/pages/index.astro, frontend/tests/build.test.mjs]
  modified: []
key-decisions:
  - Use only the unchanged approved direct artifact set; no peer bypass or additional browser-test dependency.
  - Real React client event/state proof uses a bounded DOM host; browser hydration remains a human end-of-phase check.
requirements-completed: [BUILD-01, BUILD-03]
completed: 2026-10-21
coverage:
  - deliverable: Static HTML and strict build-time Markdown input with emitted island assets
    verification:
      - kind: command
        ref: nix develop ./ops/nixos --command npm --prefix frontend run check
        status: pass
      - kind: command
        ref: nix develop ./ops/nixos --command npm --prefix frontend run build
        status: pass
      - kind: test
        ref: frontend/tests/build.test.mjs
        status: pass
    human_judgment: false
  - deliverable: Real browser island hydration and accessible interaction
    human_judgment: true
    rationale: Real React client event/state and emitted hydration contract pass locally; no browser executable or automation dependency was available. Perform the planned browser check at phase end.
---
# Phase 2 Plan 03: Static collection and selected React island

An exact locked Astro/React build produces static synthetic HTML from strict Markdown and a selected interactive counter, with no request-time Node service or commercial offer.

## Accomplishments

- Exact approved Astro 7.4.1, integration 7.1.0, matching React/DOM 19.3.1, checker 0.9.11, TypeScript 6.0.3 and React types 19.3.0 resolve through npm's actual lock. Node 24.22.0/npm 11.19.1 pinned shell used; npm ci installed 273 packages without peer bypass.
- Strict collection validates id/title/evidence_class. Actual disposable builds prove changed Markdown changes HTML and unknown fields/wrong types fail. Static GET returned 200/text-html and no server output is emitted.
- Actual React client renderer dispatches the button event and updates useState from 0 to 1 in a bounded DOM host, without mocking hooks/state. Emitted client-load island assets are checked separately; full browser hydration is not claimed.

## Verification

Clean npm ci, Astro check (6 files, 0 errors/warnings/hints), static build (one page) and 3 Node integration tests passed, zero skips. Final test duration 2.465 seconds; static build 473 ms, acquisition/install measured separately (273 packages in 2 seconds). Runtime metadata and actual installed CLI path were checked. No host/proxy/DNS/certificate/bank/mail changes or product UI acceptance.

## Task commits

- 6a532a5: exact frozen graph and first static HTTP tracer.
- 1581176: strict Markdown collection and actual React event/state checks.

## Deviations from Plan

None. The actual Astro CLI location is bin/astro.mjs (through installed .bin/astro), rather than an obsolete astro.js path; the test uses the installed binary. Build tools remain development-only. Generated frontend dependency/output/cache paths were locally excluded from Git; tracked .gitignore publication remains 02-17.

## References and remaining checks

Official implementation references: https://docs.astro.build/en/guides/content-collections/ and https://react.dev/reference/react-dom/client/createRoot . Locked installed APIs/CLI and actual build are the executable compatibility evidence. These references confer no production acceptance.

End-of-phase human check: serve built dist over a bounded local static server, open the synthetic page, click Increment synthetic counter, verify visible count changes and keyboard/announcement behavior. No browser check was marked passed. Ready for 02-04; independent Python slice 02-05 is next in this inline run.
