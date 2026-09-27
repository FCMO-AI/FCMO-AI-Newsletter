# Integration requests from WP-B

## WP-B2 slot contract (deferred)

WP-B2 may add community integration only through the slots owned by the paper
template lane. It must not edit `community/ghost-theme/` or invent a second
Ghost client.

- `slot:subscribe`: a no-JavaScript-safe link to the Ghost portal signup. The
  link must remain useful when JavaScript is disabled and must not expose an
  email address or token in the static paper.
- `slot:cartas`: a best-effort rail of up to three published Ghost posts tagged
  `cartas`, ordered newest first. A timeout, 4xx/5xx, malformed payload or
  missing API key is a normal empty-rail result; the paper build remains
  successful and must not cache private/member data.
- `slot:banner`: reserved for the reader-facing edition/freshness banner. B2
  must not change its state or copy; it only places the already-localized
  banner emitted by A3b.

The paper-side adapter should receive `GHOST_CONTENT_URL` and
`GHOST_CONTENT_API_KEY` from its caller, use a bounded timeout (5 seconds),
and expose only `title`, `url`, `custom_excerpt`, `published_at` and an
allowlisted feature image URL. It must never call the Admin API.

## A3a/A3b integration points

- A3a owns `design/tokens.json`. `community/ghost-theme/build.sh` reads it
  when present and never writes it; the checked-in theme has a safe local
  fallback so the B1 lane remains independently buildable.
- A3b should call `tools/paper/pwa.py build --source <candidate> --out
  <candidate>` after static routes are generated, or perform the equivalent
  copy. The PWA manifest, service worker, icons and registration marker are
  expected at the candidate root, including `/favicon.ico`.
- The PWA service worker deliberately does not cache `data/newsroom-status`
  or any freshness/health document. A3b must not add a broad `cache.addAll`
  over the generated data tree.

## Operator boundaries

Ghost(Pro), real email delivery, domain/DNS, postal address and production
credentials remain blocked by the operator decisions in `OPERADOR.md`. The
implementation and tests in this lane use only the local `MockGhost`; no real
mail or external account is contacted.
