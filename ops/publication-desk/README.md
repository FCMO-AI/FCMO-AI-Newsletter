# Public desk ledger

The active ledger belongs on the separate `ops-ledger` branch at
`ops/publication-desk/LEDGER.jsonl`. It is no longer a product-branch file.

Before merging its removal, seed and verify the latest ledger using
`ops/publish_ledger.py`, update the scheduled desk and its health readers, and
confirm main protection with the desk's replacement credential.

The old bytes remain in git history. The administrator migration order and the
Spanish desk contract are in [PUBLISHING-SETUP.md](../../docs/PUBLISHING-SETUP.md).
