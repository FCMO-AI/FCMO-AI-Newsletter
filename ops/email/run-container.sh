#!/bin/sh
set -eu
email_state="$HOME/.local/share/fcmo-email"
email_release="$email_state/current"
case "${1:-}" in
 database)
  email_image=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["postgres"])' "$email_release/ops/email/images.json")
  exec podman run --rm --name fcmo-email-db --network fcmo-email \
    --env-file "$email_state/db.env" --volume fcmo-email-db:/var/lib/postgresql/data \
    --health-cmd 'pg_isready -U listmonk -d listmonk' --health-interval 10s \
    "$email_image"
  ;;
 listmonk|init)
  email_image=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["listmonk"])' "$email_release/ops/email/images.json")
  if [ "$1" = init ]; then
    exec podman run --rm --name fcmo-email-init --network fcmo-email \
      --env-file "$email_state/app.env" -v "$email_release/ops/email/config.toml:/listmonk/config.toml:ro" \
      "$email_image" ./listmonk --install --yes --idempotent
  fi
  exec podman run --rm --name fcmo-email-listmonk --network fcmo-email \
    --env-file "$email_state/app.env" -p 127.0.0.1:9000:9000 \
    -v "$email_release/ops/email/config.toml:/listmonk/config.toml:ro" \
    -v "$email_state/static:/listmonk/static:ro" \
    "$email_image" ./listmonk --static-dir /listmonk/static
  ;;
 *) exit 2;;
esac
