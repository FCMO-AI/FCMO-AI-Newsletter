#!/usr/bin/env bash
set -euo pipefail

script_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
state_dir="$script_dir/.state"
network=fcmo-newsletter-staging
mail_name=fcmo-newsletter-mailpit
ghost_name=fcmo-newsletter-ghost
volume=fcmo-newsletter-ghost-content

case "${1:-}" in
  up)
    command -v podman >/dev/null || { echo 'podman is required' >&2; exit 1; }
    mkdir -p "$state_dir"
    chmod 700 "$state_dir"
    podman network exists "$network" || podman network create "$network" >/dev/null
    podman volume exists "$volume" || podman volume create "$volume" >/dev/null
    if ! podman container exists "$mail_name"; then
      podman run -d --name "$mail_name" --network "$network" \
        -p 127.0.0.1:8025:8025 -p 127.0.0.1:1025:1025 \
        docker.io/axllent/mailpit:latest >/dev/null
    else
      podman start "$mail_name" >/dev/null || true
    fi
    if ! podman container exists "$ghost_name"; then
      podman run -d --name "$ghost_name" --network "$network" \
        -p 127.0.0.1:2368:2368 -v "$volume":/var/lib/ghost/content \
        -e url=http://127.0.0.1:2368 \
        -e NODE_ENV=development \
        -e database__client=sqlite3 \
        -e mail__transport=SMTP \
        -e mail__options__host="$mail_name" \
        -e mail__options__port=1025 \
        -e mail__from='FCMO staging <staging@localhost>' \
        docker.io/library/ghost:5 >/dev/null
    else
      podman start "$ghost_name" >/dev/null || true
    fi
    printf '%s\n' 'Ghost: http://127.0.0.1:2368/ghost/' 'Mailpit: http://127.0.0.1:8025/'
    printf '%s\n' "Create a Ghost custom integration, then save its Admin API key in $state_dir/admin-api-key (mode 600)."
    ;;
  down)
    podman rm -f "$ghost_name" "$mail_name" >/dev/null 2>&1 || true
    podman network rm "$network" >/dev/null 2>&1 || true
    printf '%s\n' 'Staging containers removed; the Ghost volume is retained. Use down --purge to remove it.'
    if [[ "${2:-}" == '--purge' ]]; then
      podman volume rm "$volume" >/dev/null 2>&1 || true
      rm -rf -- "$state_dir"
      printf '%s\n' 'Staging volume and local state removed.'
    fi
    ;;
  *)
    printf '%s\n' 'Usage: ghost-staging.sh up|down [--purge]' >&2
    exit 2
    ;;
esac
