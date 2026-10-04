# STUDIO-A2 — missing binding specification

Date: 2026-10-04 UTC  
Branch: `c5/studio-a2`  
Starting commit: `a6275de`

## Outcome

Implementation is blocked before the red-test step. The required binding document
`/srv/fcmo/agents/work/newsletter/c5/STUDIO-SPEC.md` does not exist. Consequently,
the file ownership list in §13, principles in §2, acceptance commands, and mock
publish contract cannot be established. No product code, tests, host operations,
or publication state were changed. This report is the only change.

## Evidence and completed preparation

- Read the FCMO Agent Hub runtime and Software Engineering, High Consequence,
  and Worthy Work disciplines.
- Read the repository parent doctrine, product goal, communication standard,
  README, HANDOFF, publication policy, and AGENTS contract.
- Read all of campaign `STATE-AND-PLAN.md` and campaign `MISSION.md`; consulted
  the previous PLAN, OPERADOR, and Newsletter vault notes for existing platform,
  publication, and brand decisions.
- Confirmed the worktree starts clean on `c5/studio-a2`.
- Repeated direct reads/stat of the required specification failed with
  `No such file or directory`.
- Searched file paths under the campaign, Newsletter work directory, and
  Newsletter vault notes; no replacement `STUDIO-SPEC.md` was found.
- Existing offline Ghost mock: `tests/harness/mock_ghost.py`. Existing Ghost
  staging script: `ops/staging/ghost-staging.sh`. Neither establishes A2's
  missing contract and neither was changed or started.
- Requested the current specification path or restoration of the specified
  file. No response was available at the time this report was written.

No tests were executed and no red/green evidence is claimed. Inventing a failing
test without the assigned behavior would not satisfy the red-first requirement.
There was no network access, push, merge, live publish, credential access, or
mutation outside this worktree.

## Continuation

1. Make the binding specification available at its designated path (or supply
   its authoritative replacement).
2. Read it completely; derive A2's exact file ownership and acceptance commands.
3. Write and execute the relevant failing test, then commit that red test with
   author `Codex <noreply@openai.com>` before implementing the assigned behavior.
4. Implement and verify only A2's assigned files. Place the host operations
   artifacts under `studio/host-ops/**` in this worktree and adjust the backup
   drill acceptance path as instructed.
5. Exercise publication against the mock. Live publication remains outside
   this lane, pending L11 and operator Q1/Q5. Commit locally without pushing;
   update this report with reproducible results for Claude's independent rerun.

## Resumen

A2 queda bloqueado por la ausencia de `STUDIO-SPEC.md`. La orientación y la
búsqueda local están completas; no se inventó alcance, no se modificó el
producto y no se publicó nada. Para continuar hace falta el documento vinculante.
