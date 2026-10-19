"""Bound release commands and clean up their browser/server descendants."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time


def run_command(command, *, timeout, capture_output=False, check=False, **kwargs):
    if timeout <= 0:
        raise ValueError('command timeout must be positive')
    if capture_output:
        kwargs.update(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    label = ' '.join(map(str, command[:2]))
    print(f'Iniciando: {label} (límite {timeout:g} s)', file=sys.stderr, flush=True)
    started = time.monotonic()
    # A separate session lets the watchdog stop Node, Chromium and HTTP servers,
    # including those left behind when their immediate parent has exited.
    process = subprocess.Popen(command, start_new_session=True, **kwargs)
    previous_term = None
    terminating = False
    if threading.current_thread() is threading.main_thread():
        previous_term = signal.getsignal(signal.SIGTERM)
        def terminate(signum, _frame):
            nonlocal terminating
            terminating = True
            # An outer release watchdog must unwind this watchdog too, so its
            # separately grouped browser children are cleaned before it exits.
            raise SystemExit(128 + signum)
        signal.signal(signal.SIGTERM, terminate)
    try:
        while True:
            remaining = timeout - (time.monotonic() - started)
            try:
                stdout, stderr = process.communicate(timeout=max(.001, min(30, remaining)))
                break
            except subprocess.TimeoutExpired as exc:
                elapsed = time.monotonic() - started
                if elapsed >= timeout:
                    print(f'Tiempo agotado: {label} ({elapsed:.0f} s; límite {timeout:g} s)',
                          file=sys.stderr, flush=True)
                    raise subprocess.TimeoutExpired(command, timeout, exc.output, exc.stderr) from exc
                print(f'En curso: {label} ({elapsed:.0f} s; límite {timeout:g} s)',
                      file=sys.stderr, flush=True)
    finally:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            # Leave time for this cleanup to finish before an outer watchdog
            # reaches its own hard-kill deadline.
            process.wait(timeout=.5 if terminating else 5)
        except subprocess.TimeoutExpired:
            pass
        finally:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            # Reap the direct child and close capture pipes even on timeout or
            # interruption. Descendants cannot keep a capture pipe open now.
            try:
                process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                # An independently detached child must not make cleanup wait
                # forever by retaining a capture descriptor.
                for pipe in (process.stdout, process.stderr):
                    if pipe:
                        pipe.close()
            finally:
                if previous_term is not None:
                    signal.signal(signal.SIGTERM, previous_term)
    result = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
    print(f'Finalizado: {label} ({time.monotonic() - started:.1f} s; salida {result.returncode})',
          file=sys.stderr, flush=True)
    if check:
        result.check_returncode()
    return result
