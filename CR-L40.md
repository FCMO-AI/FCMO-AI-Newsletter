# CR-L40 — revalidación tras integrar main; Studio sigue bloqueado

Actualizado el **2026-10-07, 20:13 CDMX**. Se continuó la entrega anterior de esta
branch y se integró `origin/main` en `f683aa2`. **La aceptación actual no pasa:**
el corpus nuevo rompe el renderer por el límite del índice de búsqueda. Studio
responde en loopback, pero sus vistas previas devuelven 503. El URL
**https://fcmo-hub.tail8cbe0b.ts.net:8447/** sigue sin activación demostrada.

La entrega anterior, documentada en el commit `403e8f6`, probó el recorrido con el
corpus de `9468c9e`. Ese resultado es histórico y no sustituye la revalidación
actual. La unidad permanece en `ops/studio/fcmo-studio.service`, sin instalar;
la línea exacta está en [OPERATOR-LINE.md](OPERATOR-LINE.md). Reparar el renderer
antes de activar el URL. No se modificaron gates, datos editoriales ni secretos.

## COMMITS

Continuación de `75027f8`, `ead71d8`, `f63ef5a` y `403e8f6`:

- `75962cc` — Merge current main into Studio live lane.
- `b7f95e8` — Explain production preview failures without leaking diagnostics.

El commit de este informe y `NEEDS.md` se identifica en el log final de la branch.
El intento de `GIT_TERMINAL_PROMPT=0 git push -u origin c5/studio-live` terminó
con exit 128: no hay autenticación HTTPS disponible. No se creó PR, no se buscaron
secretos ni se intentó otra identidad. La entrega termina en commits locales.

## FINDINGS CLOSED

- **L40-DIAGNOSTIC:** Studio ya no atribuye cualquier fallo del build a una
  integración ausente. Reconoce el límite numérico del índice de búsqueda y
  comunica en español el tamaño, el límite y la necesidad de reparar el generador.
  Otros errores reciben un aviso general del renderer, sin divulgar stderr,
  tracebacks, rutas o texto privado. Las dos pruebas de `PreviewFailureReason`
  fallaron primero con el mensaje anterior y pasaron después. También comprueban
  limpieza del workspace y ausencia de una entrada de cache tras el fallo.
  La reproducción con el corpus real devuelve el nuevo aviso de 166155 frente a
  153600 bytes; el build permanece rechazado.
- **L40-INSTALL / preparación del host:** las pruebas existentes de rutas
  entre comillas, ambas cuentas, puerto/origen, permisos, bundle y API privada
  siguen pasando. No equivalen a instalación permanente ni a renderer funcional.

## FINDINGS NOT CLOSED

- **L40-RENDERER:** `tools/paper/search_index.py:43` rechaza el corpus actual:
  EN=166155, ES=187049 y ZH=205362 bytes, todos por encima de 153600. El generador
  es idéntico al de `origin/main`; sólo cambió el corpus en los commits integrados.
  Hay cinco fallos y un error en la suite Studio. Afecta la vista previa privada,
  publicación por HTTP/bare, identidad byte por byte, traducción por HTTP y seam
  de email. La reparación del generador está solicitada en `NEEDS.md`, fuera de
  la propiedad de Studio. No se elevó el límite ni se retiraron stories.
- **L40-BROWSER:** el Playwright indicado existe, pero no su ejecutable Chromium
  headless build 1243. El recorrido actual terminó con `BROWSER_UNAVAILABLE` y
  no produjo capturas nuevas. Las 46 imágenes anteriores permanecen en la carpeta
  requerida; los recibos actuales dicen `completed: false`.
- **L40-TAILNET:** el gestor systemd de usuario devuelve `offline` y no hay socket
  local de Tailscale. La instalación y el mapping quedan reservados al operador
  por el brief. No se afirma que el URL sirva ni que Javier haya entrado.
- **L40-PUBLICATION:** no se probaron credenciales personales reales, protecciones
  remotas, backup de producción ni PR/Pages/origen público. Conservar dry-run.

## ACCEPTANCE

| Comando | Resultado actual |
| --- | --- |
| `git fetch origin main` y `git merge origin/main` | Merge sin conflictos de `f683aa2`; commit `75962cc` |
| `python3 -m unittest tests.test_studio_preview_errors` antes del cambio | Dos fallos observados por el aviso incorrecto |
| `python3 -m unittest tests.test_studio_preview_errors tests.test_studio_host tests.test_studio_activation` después | 14 tests, OK |
| `python3 -m unittest discover -s tests -p 'test_studio*.py'` final | 91 tests: 84 pasan, cinco fallan, un error, un skip; exit 1 |
| `node --test studio/web/test/*.test.mjs` | 9/9, sin skips |
| `python3 -m tests.harness.studio_host_journey --out ../../reports/studio-frames` con el Playwright indicado | Launcher y probe reales en 127.0.0.1:8490 pasan; navegador no disponible; exit 1 |
| Invocación directa de `search_index.build` con corpus real por locale | Los tres idiomas exceden 153600 bytes |
| Vista previa directa con Store y renderer reales | Rechazo correcto por el límite; el aviso ya nombra la causa |
| `systemd-analyze --user verify ops/studio/fcmo-studio.service` con runtime temporal | Exit 0; no instala ni inicia un gestor |
| Integridad del bundle, `git diff --check` | PASS |
| `systemctl --user is-system-running` | `offline` |
| `GIT_TERMINAL_PROMPT=0 git push -u origin c5/studio-live` | Exit 128, sin autenticación HTTPS; sin PR |

El probe consulta health, HTML, JS/CSS actuales y rechazo sin sesión de las APIs
privadas. Usa launcher, almacenamiento, git local y cuentas temporales. La
inyección existente cambia sólo el límite del remoto. No hubo modelos, transporte
GitHub editorial real ni acceso a datos privados de producción. Los procesos
locales temporales terminaron; 8490 quedó libre.

Los logs actuales están en `../../reports/studio-frames/{unit-current.log,
host-current.log,journey-current.log}`. `current-validation.json` distingue la
revisión actual, el corpus, el resultado de tests y la procedencia histórica de
las imágenes. `journey.json` acredita loopback y `completed: false`; no atribuir
las capturas anteriores al intento actual. El manifest del bundle sigue teniendo
SHA-256 `0c2bb3f931b214cfee202e9f949f0ea9a27dd8d43fbf9abb961aaf0916d2651e`.

## UNVERIFIED

Recorrido y capturas actuales en navegador, uso de escritorio/teléfono, instalación
permanente, reinicio de systemd, mapping Tailscale, DNS/TLS/ACL y acceso de Javier.
Publicación real y sus prerrequisitos. La suite amplia anterior de 830 tests no
se repitió ni se presenta como aceptación actual. El skip de la suite Studio es
el caso condicional de renderer ausente, porque el renderer está presente.
No se afirma nueva freshness ni un ciclo autónomo del periódico público.

## NEEDS.md

Se conserva todo el contenido anterior, incluida la activación del host. Se
agregaron dos solicitudes completas en [NEEDS.md](NEEDS.md):

1. **Renderer:** compactar el índice del corpus real conservando 150 KiB,
   todos los stories, locales y contratos de consumidores; resolver la duplicación
   de campos humanos/agentes en la lane del generador. Repetir las seis pruebas
   afectadas, el build real, la suite Studio y el recorrido con navegador.
2. **Chromium:** montar el ejecutable existente y configurar `CHROME_PATH`, o
   montar su cache y configurar `PLAYWRIGHT_BROWSERS_PATH`; después repetir la
   batería. No instalar dependencias desde esta lane.

La entrada previa exige, tras reparar esos límites, preparar las dos cuentas y
el entorno privado, ejecutar la línea de instalación/mapping desde la sesión
con permiso, probar guardar/recargar por HTTPS en escritorio y teléfono, confirmar
TLS/ACL/persistencia y conservar dry-run hasta probar publicación protegida.

## KNOWN GAPS

**Studio aún no está funcional de extremo a extremo con el corpus actual ni live
en el URL tailnet.** El launcher y la API privada responden; el renderer está
bloqueado. El aviso ya es correcto y la continuación está especificada. Las
capturas son históricas, no aceptación humana ni prueba de publicación remota.
