# Public desk ledger

The active ledger remains tracked on main at
`ops/publication-desk/LEDGER.jsonl`. L30 defers the isolated-branch migration
because the live scheduled Publication Desk still appends here. Preserve the
existing bytes and reconcile concurrent main updates before each append.
Missing history is an operational error, never an empty ledger.

`ops/publish_ledger.py` remains a local-only rehearsal tool. Before a future
removal, pause writes, capture and verify the latest main ledger, switch the
scheduled desk and every health reader, and prove a new activation on the
isolated branch. The staged migration contract is in
[PUBLISHING-SETUP.md](../../docs/PUBLISHING-SETUP.md).
