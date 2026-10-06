#!/bin/sh
set -eu
email_state="$HOME/.local/share/fcmo-email"
email_units="$HOME/.config/systemd/user"
systemctl --user disable --now fcmo-email-gateway.service fcmo-email-maintenance.timer || true
systemctl --user stop fcmo-email-listmonk.service
if [ -f "$email_state/previous" ]; then
  email_previous=$(cat "$email_state/previous")
  test -d "$email_previous/ops/email"
  ln -s "$email_previous" "$email_state/rollback.new"
  mv -Tf "$email_state/rollback.new" "$email_state/current"
  cp "$email_previous"/ops/email/*.service "$email_units/"
  cp "$email_previous"/ops/email/*.timer "$email_units/"
  systemctl --user daemon-reload
  systemctl --user start fcmo-email-listmonk.service
  echo 'Previous software restored. Gateway remains disabled pending inspection.'
else
  systemctl --user disable --now fcmo-email-listmonk.service fcmo-email-db.service
  echo 'Email stopped; subscriber database and dispatch journal retained.'
fi
echo 'Set FCMO_EMAIL_ENABLED=false in GitHub and remove the email Caddy block. Already delivered mail cannot be recalled.'
echo 'Never delete the campaign database or journal to retry an edition.'
