# Public desk ledger

The active ledger remains tracked on main at
`ops/publication-desk/LEDGER.jsonl`. L30 defers the isolated-branch migration
because the live scheduled Publication Desk still appends here. Preserve the
existing bytes and reconcile concurrent main updates before each append.
Missing history is an operational error, never an empty ledger.

After translating changed English prose, bind the newly written locale fields
with `python3 tools/refresh_locale_identity.py --corpus corpus --bind-updated-fields`,
then run `python3 tools/validate_localizations.py --strict --corpus corpus`.
Commit the field bindings alongside the corresponding source-controlled locale
pack. Unchanged wording retains its previous English binding; automated builds
never use the editorial binding option. If identical wording remains valid after
an English revision, the desk must explicitly record a reviewed source binding
for that field rather than approving it through an edition metadata refresh.

`ops/publish_ledger.py` remains a local-only rehearsal tool. Before a future
removal, pause writes, capture and verify the latest main ledger, switch the
scheduled desk and every health reader, and prove a new activation on the
isolated branch. The staged migration contract is in
[PUBLISHING-SETUP.md](../../docs/PUBLISHING-SETUP.md).
