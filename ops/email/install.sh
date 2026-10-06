#!/bin/sh
# Reversible install. Stops before mutation if host/secret prerequisites are absent.
set -eu
umask 077
email_root=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd)
email_state="$HOME/.local/share/fcmo-email"
email_units="$HOME/.config/systemd/user"
email_env=/etc/fcmo/secrets/email.env
command -v podman >/dev/null
command -v python3 >/dev/null
command -v age >/dev/null
systemctl --user show-environment >/dev/null
test -r "$email_env" || { echo 'Missing readable /etc/fcmo/secrets/email.env' >&2; exit 1; }
email_user=$(id -un)
awk -F: -v u="$email_user" '$1==u && $3>=65536 { found=1 } END { exit !found }' /etc/subuid || {
  echo 'Host prerequisite: allocate non-overlapping subordinate UID/GID ranges for this user (requires host administrator).' >&2; exit 1;
}
awk -F: -v u="$email_user" '$1==u && $3>=65536 { found=1 } END { exit !found }' /etc/subgid
python3 "$email_root/ops/email/preflight.py" "$email_env" --phase install
mkdir -p "$email_state/releases" "$email_units"
email_release="$email_state/releases/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir "$email_release"
# Explicit source-only allowlist: no .git, credentials, audience or previews.
mkdir -p "$email_release/ops" "$email_release/community"
cp -R "$email_root/tools" "$email_release/tools"
cp -R "$email_root/ops/email" "$email_release/ops/email"
cp -R "$email_root/legal" "$email_release/legal"
cp -R "$email_root/community/config" "$email_release/community/config"
python3 "$email_root/ops/email/preflight.py" "$email_env" --phase install --write-state "$email_state"
for email_image in $(python3 -c 'import json,sys; print(" ".join(json.load(open(sys.argv[1])).values()))' "$email_release/ops/email/images.json"); do
  podman pull "$email_image"
done
podman network exists fcmo-email || podman network create fcmo-email >/dev/null
podman volume exists fcmo-email-db || podman volume create fcmo-email-db >/dev/null
if [ -L "$email_state/current" ]; then
  readlink "$email_state/current" > "$email_state/previous"
  systemctl --user stop fcmo-email-gateway fcmo-email-listmonk
fi
ln -s "$email_release" "$email_state/current.new"
mv -Tf "$email_state/current.new" "$email_state/current"
cp "$email_release"/ops/email/*.service "$email_units/"
cp "$email_release"/ops/email/*.timer "$email_units/"
systemctl --user daemon-reload
systemctl --user enable --now fcmo-email-db.service
"$email_release/ops/email/wait-db.sh"
"$email_release/ops/email/run-container.sh" init
systemctl --user enable --now fcmo-email-listmonk.service
echo 'Listmonk installed on 127.0.0.1:9000. Create the private admin and API user, then run ops/email/activate.sh.'
echo 'Rollback: ops/email/rollback.sh. The database volume is retained.'
