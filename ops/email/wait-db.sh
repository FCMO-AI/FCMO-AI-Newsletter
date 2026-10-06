#!/bin/sh
set -eu
email_try=0
while [ "$email_try" -lt 60 ]; do
  if podman exec fcmo-email-db pg_isready -U listmonk -d listmonk >/dev/null 2>&1; then exit 0; fi
  email_try=$((email_try+1))
  sleep 1
done
echo 'Email database did not become ready' >&2
exit 1
