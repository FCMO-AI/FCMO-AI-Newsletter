# Studio A2 — implementation and verification

2026-10-04 UTC · branch `c5/studio-a2` · base `f0223ab` (`a6275de` product base).

The missing-specification report is superseded. The binding specification is
present locally and was read in full; it is intentionally not committed.

Implemented within A2 ownership: stdlib server, per-person scrypt auth, sessions,
CSRF/Origin checks, private durable autosave journal and atomic file mirrors,
locale locks, checkpoints, restoration, comments, localization review states,
figure/container validation, private preview through the production builder,
two-person review, candidate isolation, GitHub/Pages state machine, curated
issues, corrections and withdrawals, optional jobs, private backups and restore.
Host operations are staged under `studio/host-ops` for architect installation.

Red-first evidence: `e525dc5` commits the initial durability/closed-document
regressions before implementation. Running that test failed with missing Studio
package. Subsequent mechanism tests challenged HTTP authentication, lost
acknowledgements, tree isolation and restoration against real local git and
loopback HTTP mocks. No external network, push, live publication, host service
installation or changes to other lanes were performed.

Verification is in progress; final commands/counts will replace this paragraph.
The initial full suite exposed a forbidden machine path in the superseded report
and a recursive temporary-directory placement in an existing refresh oracle.
Neither publication gates nor unrelated tests are weakened to address them.

Material integration boundary: A1's editorial renderer/contracts and B's essay
page/template/bundle are absent from this lane base. Preview fails closed instead
of substituting HTML. The byte-identity test explicitly skips until those files
are integrated. This lane cannot claim M1, rendered UI acceptance, or production
success. Live publishing remains disabled by default and depends on L11 and
operator Q1/Q5; Q2 remains unadopted, so English originals are the default.

The mock replaces only candidate gate execution and remote transport. It proves
a real locally assembled git tree includes only the selected editorial scope,
uses the author's credential for the PR and the other's for approval, refuses
red checks and missing/refused protection, and reconciles acknowledged-but-lost
push/PR/review/merge responses without repeating them. It does not prove live
GitHub permissions, the integrated gate command, browser layout, or human use.

Continuation: integrate A1/B and L11; rerun focused and full tests, require the
preview-identity test to execute without a skip, inspect final browser/UI frames,
install the staged ops and complete access/protection/operator decisions. Do not
enable publication or represent the newspaper as live on the basis of mocks.

Resumen: A2 implementa y prueba el servidor privado y el flujo contra el mock.
Falta la verificación integrada del renderer/UI y la habilitación autorizada de
producción; no se hizo push ni publicación real.
