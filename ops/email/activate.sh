#!/bin/sh
set -eu
email_release="$HOME/.local/share/fcmo-email/current"
python3 "$email_release/ops/email/preflight.py" /etc/fcmo/secrets/email.env
python3 "$email_release/ops/email/bootstrap.py"
systemctl --user enable --now fcmo-email-gateway.service fcmo-email-maintenance.timer
python3 - <<'PY'
import json,time,urllib.request
deadline=time.monotonic()+30
while True:
    try:
        with urllib.request.urlopen('http://127.0.0.1:9010/healthz',timeout=2) as response:
            assert json.load(response)['status']=='ok'
        break
    except (OSError,ValueError,AssertionError):
        if time.monotonic()>=deadline:raise
        time.sleep(.2)
print('Gateway observed healthy on 127.0.0.1:9010. Public TLS/DNS and mailbox proof remain separate.')
PY
