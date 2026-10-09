"""Real private launcher and browser tasks, isolated local git; no model/GitHub calls.

python3 -m tests.harness.studio_host_journey --out /private/studio-frames
Playwright comes from PLAYWRIGHT_MODULE, never an installation during this proof.
"""
import argparse
import importlib.util
import hashlib
import json
import math
from http.client import HTTPConnection
import os
from pathlib import Path
import secrets
import signal
import subprocess
import tempfile
import time
from urllib.parse import urlsplit

from studio.server.auth import Auth
from studio.server.storage import Store, git

ROOT = Path(__file__).resolve().parents[2]

def preview_timeout_ms(cold_seconds):
    if not isinstance(cold_seconds, (int, float)) or not math.isfinite(cold_seconds) or cold_seconds <= 0:
        raise ValueError('No se pudo leer el tiempo de la primera vista previa.')
    # Twice the measured render, plus five seconds for browser/frame scheduling.
    return math.ceil(cold_seconds * 2000 + 5000)


def measure_preview(origin, slug, user, password):
    address = urlsplit(origin)
    if address.scheme != 'http' or address.hostname != '127.0.0.1':
        raise ValueError('La medición de prueba solo admite el listener local aislado.')
    conn = HTTPConnection(address.hostname, address.port, timeout=195)
    cookie = csrf = None
    try:
        conn.request('POST', '/api/login', json.dumps({'user': user, 'password': password}),
                     {'Origin': origin, 'Content-Type': 'application/json'})
        response = conn.getresponse(); login = json.loads(response.read())
        if response.status != 200: raise RuntimeError('No se pudo abrir la sesión aislada para medir la vista previa.')
        cookie = response.getheader('Set-Cookie').split(';')[0]; csrf = login['csrf']
        start = time.perf_counter()
        conn.request('GET', '/preview/' + slug + '/en/', headers={'Cookie': cookie})
        response = conn.getresponse(); body = response.read()
        seconds = time.perf_counter() - start
        if response.status != 200 or b'essay-body' not in body:
            raise RuntimeError('El renderer no entregó el ensayo; no se puede fijar un timeout con una vista previa fallida.')
        return {'cold_preview_seconds': seconds, 'preview_timeout_ms': preview_timeout_ms(seconds)}
    finally:
        if cookie and csrf:
            conn.request('POST', '/api/logout', '{}', {'Cookie': cookie, 'X-CSRF-Token': csrf,
                                                    'Origin': origin, 'Content-Type': 'application/json'})
            conn.getresponse().read()
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    report = {'completed': False, 'loopback': False, 'browser_regressions': [],
              'bundle_manifest_sha256': hashlib.sha256((ROOT / 'studio/web/dist/build-manifest.json').read_bytes()).hexdigest()}
    def receipt():
        (args.out / 'journey.json').write_text(json.dumps(report, indent=2) + '\n')
    receipt()
    (args.out / 'acceptance.json').write_text('{"completed": false}\n')
    with tempfile.TemporaryDirectory(prefix='studio-l40-') as temporary:
        root = Path(temporary)
        bare = root / 'origin.git'
        subprocess.run(['git', 'clone', '--quiet', '--bare', '--no-hardlinks', str(ROOT), str(bare)], check=True)
        git(bare, 'update-ref', 'refs/heads/main', 'HEAD')
        data = root / 'data'
        key = secrets.token_urlsafe(48)
        password = secrets.token_urlsafe(24)
        store = Store(data)
        try:
            git(data / 'clone', 'remote', 'set-url', 'origin', str(bare))
            auth = Auth(store, key)
            for user in ('javier', 'matias'): auth.add_user(user, password)
        finally: store.close()
        env = {k: v for k, v in os.environ.items() if not k.startswith(('GH_', 'GITHUB_', 'STUDIO_', 'DOGFOOD_'))}
        for user in ('javier', 'matias'): (root / user).mkdir(mode=0o700)
        env.update(STUDIO_REPO=str(ROOT), STUDIO_DATA=str(data), STUDIO_PORT='8490', STUDIO_BIND='127.0.0.1',
                   STUDIO_ORIGIN='http://127.0.0.1:8490', STUDIO_SESSION_KEY=key,
                   STUDIO_DRY_RUN='1', STUDIO_LIVE_ENABLED='0', STUDIO_TRANSLATION_PROVIDER='disabled',
                   STUDIO_GH_CONFIG_JAVIER=str(root / 'javier'), STUDIO_GH_CONFIG_MATIAS=str(root / 'matias'),
                   STUDIO_PASS=password, STUDIO_USER='javier',
                   DOGFOOD_ACTIVE='local-bare-only', DOGFOOD_BARE=str(bare), DOGFOOD_ROOT=str(root),
                   DOGFOOD_LIVE='http://127.0.0.1:8490/',
                   PYTHONPATH=str(ROOT / 'studio/dogfood') + os.pathsep + str(ROOT))
        # Existing, explicit fixture-only injection changes the remote boundary,
        # never the launcher, Store, HTTP, renderer, UI or publication checks.
        seeded = subprocess.check_output(['python3', '-m', 'tests.harness.seed_studio'], cwd=ROOT, env=env, text=True).strip()
        review_seed = subprocess.check_output(['python3', '-m', 'tests.harness.seed_studio'], cwd=ROOT, env=env, text=True).strip()
        env['STUDIO_SLUG'] = seeded
        source = ROOT / 'ops/studio/host.py'
        spec = importlib.util.spec_from_file_location('host_probe_l40', source)
        host = importlib.util.module_from_spec(spec); spec.loader.exec_module(host)
        with (args.out / 'launcher.log').open('w') as log:
            process = subprocess.Popen(['sh', str(ROOT / 'studio/host-ops/start.sh')], env=env, stdout=log, stderr=log, start_new_session=True)
            try:
                for _ in range(100):
                    if process.poll() is not None: raise RuntimeError('No arrancó el launcher de Studio; consulta launcher.log.')
                    try: host.probe(8490, ROOT); break
                    except OSError: time.sleep(.1)
                else: raise RuntimeError('Studio no respondió en loopback.')
                report['loopback'] = True
                report.update(measure_preview(env['STUDIO_ORIGIN'], seeded, 'javier', password))
                env['STUDIO_PREVIEW_TIMEOUT_MS'] = str(report['preview_timeout_ms'])
                env['STUDIO_COLD_PREVIEW_SECONDS'] = str(report['cold_preview_seconds'])
                browser_timeout = max(180, math.ceil(report['preview_timeout_ms'] / 1000) * 6 + 120)
                receipt()
                subprocess.run(['node', str(ROOT / 'tests/harness/browser/studio_host_task.mjs'), env['STUDIO_ORIGIN'] + '/', str(args.out)], env=dict(env, STUDIO_SLUG=review_seed), check=True, timeout=max(600, browser_timeout))
                # Preserve the established, stronger browser regression journeys.
                for script, argv in (('studio_editor', []), ('studio_review', [seeded]), ('studio_translate', [seeded]), ('studio_publish', [seeded]), ('studio_credentials', [])):
                    if script == 'studio_publish':
                        fresh = subprocess.check_output(['python3', '-m', 'tests.harness.seed_studio'], cwd=ROOT, env=env, text=True).strip()
                        argv = [fresh]
                    with (args.out / (script + '.log')).open('w') as evidence:
                        subprocess.run(['node', str(ROOT / ('tests/harness/browser/' + script + '.mjs')), env['STUDIO_ORIGIN'] + '/', *argv], env=env, stdout=evidence, stderr=evidence, check=True, timeout=browser_timeout)
                    report['browser_regressions'].append(script)
                    receipt()
                report['completed'] = True
                receipt()
            finally:
                try: os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError: pass
                process.wait(timeout=10)
    print('Recorrido privado completado; capturas y evidencia en ' + str(args.out))


if __name__ == '__main__': main()
