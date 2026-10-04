# Studio integration report

See [REPORT-STUDIO-INT.md](REPORT-STUDIO-INT.md) for the merged identities, red-first evidence, verified HTTP publication flow, frontend rebuild blocker and exact host continuation commands.

The loopback API, production preview and fourteen-gate mock publication path are verified. The editor source is wired to the real server, but the browser artifact could not be rebuilt without unavailable locked npm dependencies. Studio chrome therefore fails closed until the host rebuilds and verifies it. No production publication, push, visual acceptance or complete Studio UI acceptance is claimed.

Resumen: integración HTTP comprobada; interfaz pendiente de reconstrucción y navegador. Sin push ni publicación real.
