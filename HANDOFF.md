# Handoff — estado del sitio y trabajo pendiente

Escrito 2026-09-04. El autor anterior deja de trabajar aquí. Este documento es
todo lo que necesitas para continuar. `main` está en verde y desplegado.

Sitio: https://fcmo-ai.github.io/FCMO-AI-Newsletter/

---

## 1. Qué ya está hecho y verificado

- **Refresco diario** (`.github/workflows/daily-refresh.yml`): ingesta del corpus
  saneado de ARB → traducción curada → overlay → recibo → 6 compuertas → commit →
  `pages.yml` por `workflow_run`. PR #9.
- **23 historias** publicadas en `en`, `es-419`, `zh-Hans`. PR #10.
- **`llms.txt` / `llms-full.txt`** enumeran el corpus entero (antes emitían solo
  el delta del día).
- **`agent.json.newly_ingested_brief_ids`** se limpia en cada corrida (antes se
  heredaba de su propia salida y crecía sin fin).
- **`_format_json`** ya no reformatea los `part-*.json` compactos (un refresco
  diario producía 150 KB de ruido).
- **El commit del refresco incluye `READY_TO_PUBLISH.md`** (sin él la compuerta
  «recibo contra el árbol» salía en rojo a la corrida siguiente).
- **El salto a una historia conserva el idioma.** PR #11. Los stubs de
  `developments/` y `editions/` usan
  `location.replace("../index.html" + location.search + "#/...")`, con el
  `<meta http-equiv="refresh">` de respaldo sin JS.

`MEDIDO` 2026-09-04 sobre el sitio vivo, Edge headless con `--lang=ja-JP` para
que nada pase por accidente — 3 rutas × 3 idiomas, todas correctas:

| ruta | `?lang=en` | `?lang=es-419` | `?lang=zh-Hans` |
|---|---|---|---|
| `developments/FCMO-8AB23060CBF3.html` | `en` | `es-419` | `zh-Hans` |
| `developments/FCMO-183728526F81.html` | `en` | `es-419` | `zh-Hans` |
| `editions/2026-09-01.html` | `en` | `es-419` | `zh-Hans` |

Suite: `python -m unittest discover -s tests` → 10 tests, OK (~37 s local,
~10 s en CI).

---

## 2. Lo que queda abierto — dos defectos reales

Los encontré con un barrido en navegador y **no alcancé a arreglarlos**. Están
descritos con su causa raíz; no hace falta rediagnosticar.

### 2.1 `Evidence distribution` no se traduce — y volverá a romperse cada día

**Síntoma** `MEDIDO` en `#/research`:

- `es-419` → `Evidence distribution / 23 dossiers`
- `zh-Hans` → `Evidence distribution / 23 份档案`

La mitad derecha se traduce, la izquierda no.

**Causa raíz** — es el defecto importante, no el cosmético. El `<h3>` se compone
en runtime, en `release-src/index.html`, dentro de `evidenceMeter()`:

    return `<div class="evidence-meter"><h3>Evidence distribution / ${D.meta.count} briefs</h3>...

y el catálogo tiene la cadena **con el número dentro de la clave**, en
`site/data/i18n/es-419/ui.json` y `site/data/i18n/zh-Hans/ui.json`, línea 184:

    "Evidence distribution / 22 briefs": "DISTRIBUCIÓN DE EVIDENCIA / 22 DOSSIERS"

El sitio ya va por 23, así que la clave no casa nunca. **No lo arregles subiendo
22 a 23**: la clave lleva un contador, y el contador sube cada día que ARB
entrega una historia. Se rompe sola mañana.

**Arreglo correcto** (`PROPUESTA`): sacar el número de la cadena traducible. O
bien partir el `<h3>` en un fragmento fijo traducible más un nodo con el número,
o bien introducir una clave con marcador de posición y sustituir el número
después de traducir. Aplícalo también a cualquier otra clave de `ui.json` que
lleve una cifra dentro — búscalas con:

    grep -nE '"[^"]*[0-9]+[^"]*":' site/data/i18n/*/ui.json

**Barrera que hay que añadir** al oráculo, o el fallo vuelve: un test que falle
si alguna clave de `ui.json` contiene un dígito proveniente de un conteo del
corpus. Sin esa barrera esto se repite en el próximo crecimiento.

Nota: existe además la clave `"EVIDENCE DISTRIBUTION"` (mayúsculas) ya traducida
en los dos locales. Probablemente sea el resto de un intento anterior; revisa si
sirve o si sobra.

### 2.2 El mensaje de ruta inexistente está en inglés

**Síntoma** `MEDIDO`: en `es-419` y en `zh-Hans`, cualquier hash que no sea una
ruta real muestra

> That standalone route does not exist. Use the publication navigation above.

**Dónde** `release-src/index.html`, una sola ocurrencia, generada desde JS — no
es texto estático del documento, y por eso el runtime curado no la alcanza.

**Rutas reales de la SPA**, para que no repitas mi error de probar rutas que no
existen: `#/`, `#/home`, `#/research`, `#/brief/<id>`, `#/editions`,
`#/edition/<fecha>`, `#/topics`, `#/organizations`, `#/desks`, `#/chronology`,
`#/agent`. **No** existen `#/sections`, `#/timeline`, `#/about`, `#/licensing`,
`#/privacy` ni `#/methodology`; las páginas legales viven en otra parte, confirma
dónde antes de tocarlas.

**Arreglo** (`PROPUESTA`): dar de alta la cadena en los dos `ui.json` y asegurar
que el nodo que la contiene pasa por `curated-i18n.js`.

### 2.3 Falsos positivos de mi barrido — no los persigas

Mi detector marcó también estos, y **están bien como están**: `Google Research`,
`Anthropic Research`, `Redwood Research`, `Google DeepMind`, `Virginia Tech`,
`WeatherNext`, `WikiSkill` (nombres propios); `agentic-research` (slug de tema);
`FCMO AI Newsletter` (marca). El barrido completo dio **0 errores de consola y
0 respuestas 4xx** en las 36 combinaciones ruta × idioma.

---

## 3. Prerrequisitos que no son de código — bloquean el refresco automático

El mecanismo está construido y probado en seco. Para que corra solo faltan tres
cosas que sólo puede hacer quien administra la organización:

1. **`ANTHROPIC_API_KEY`** como secreto del repo Newsletter (lo consume
   `tools/translate_records.py --engine anthropic`). Sin él el traductor **falla
   cerrado**: sale 2 y no escribe nada. Es el comportamiento deseado.
2. **`FCMO_NEWSLETTER_PUBLISH_TOKEN`** como secreto en el repo ARB. Un push hecho
   con `GITHUB_TOKEN` no dispara otros workflows; por eso `pages.yml` cuelga de
   `workflow_run`.
3. **Facturación de Actions en la organización FCMO-AI.** `MEDIDO`: hoy las
   corridas de ARB mueren en 2 s con 0 pasos ejecutados. Es el bloqueo duro, y el
   que el usuario planea resolver subiendo la org al plan Teams.

---

## 4. Restricciones de seguridad — no negociables

- **`FCMO-AI/AI-Research-Breakthroughs` (ARB) es privado y sensible.** Su propia
  descripción dice: *«Internal agent-only center… DO NOT PUBLISH THIS INTERNAL
  MATERIAL, treat it as sensitive company content.»* **Nada de ARB en crudo sale
  de la máquina.** Este repo Newsletter es **público**.
- `_audit/` contiene material derivado de ARB y está en `.gitignore`. Que siga
  así.
- Lo único publicable es la salida saneada de la esclusa (`public-release.yml` →
  `build_public_release.py`, con allowlist). `_fixtures/corpus-2026-09-01/` es
  exactamente eso, ya validado contra el verificador de carga de ARB, y por eso
  sí puede viajar.
- `PUBLICATION_POLICY.md` manda: el destino público no lleva investigación
  privada, estado operativo, credenciales, historia del repo de origen ni
  direcciones personales.
- El correo del usuario se usa sólo para identificarlo; no lo mandes a ningún
  servicio.

---

## 5. Cómo verificar tu trabajo

    python -m unittest discover -s tests          # 10 tests
    python tests/oraculos/verificar_generador.py  # crecimiento, punto fijo, idioma en el salto
    python tests/oraculos/verificar_traduccion.py # todo lo publicado, en los 3 idiomas
    python tests/oraculos/verificar_refresco.py   # el refresco diario entero, sobre copia limpia
    python tools/verify_release.py                # arma publish/ y corre las 6 compuertas

### Cómo se mide lo visual — no cuentes cadenas en el HTML

Lo visual se mide **renderizando el DOM**, nunca buscando texto en el archivo: el
runtime curado decide qué se aplica, no el archivo de datos. Sirve `publish/` y
renderiza. El arnés que usé es Edge headless vía `puppeteer-core`, con la lección
incorporada de forzar `--lang=ja-JP` para que ningún acierto venga del idioma del
navegador:

    const nav = await puppeteer.launch({
      executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
      headless: 'new', args: ['--no-sandbox', '--lang=ja-JP'] });
    const p = await nav.newPage();
    await p.goto(url, { waitUntil: 'networkidle0' });
    await new Promise(x => setTimeout(x, 1400));   // el runtime curado corre despues de load
    const lang = await p.evaluate(() => document.documentElement.lang);

Recorre el DOM con un `TreeWalker` sobre nodos de texto, descarta los ocultos
(`display:none`, `visibility:hidden`, sin `getClientRects()`) y los que estén
dentro de `script`, `style`, `noscript`, `code` o `pre`. Excluye los bloques
`[data-fcmo-legal="canonical"] .fcmo-legal-notice`: por ADR-0009 el texto legal
se traduce, pero la nota que dice «rige la versión en inglés» es deliberada.

---

## 6. Trampas que ya costaron tiempo — no las vuelvas a pagar

- **Un oráculo que nombra el dato concreto que verifica se vuelve vacío el día
  que ese dato se publica.** Usa oráculos de **crecimiento**: mete en la entrada
  algo que el esperado no contiene y exige que salga en la salida.
- **Si el resultado esperado vive donde el ejecutor puede leerlo, la igualdad
  byte a byte no mide nada**: la satisface un `cp`. Ya pasó aquí una vez.
- **Punto fijo entre la pasada 2 y la 3, no entre la 1 y la 2.** La pasada 1
  anuncia legítimamente una llegada.
- **Dos clases de superficie.** `ENUMERAN` (lista todas las historias) frente a
  `ANUNCIAN` (dice qué llegó en esta corrida). Confundirlas hace un oráculo
  autocontradictorio. La partición está en `tests/oraculos/verificar_generador.py`.
- **`release-src/` es la BASE del generador, no su producto.** `index.html` son
  500 KB de render hecho a mano; el `index.html` del corpus es otra página, sin
  bloque `fcmo-data`. El armazón se conserva; el contenido se deriva del corpus.
- **`Path.write_text` trunca ANTES de validar `newline=`.** Un parche fallido
  deja 0 bytes, y un script vacío sale 0, así que los oráculos siguientes mienten.
  Siempre temporal + `os.replace`.
- **Códigos de salida tras una tubería** (`| head`, `| tail`) son del último
  eslabón, no del programa que te importa.
- **Windows:** `subprocess.run(..., text=True, input=...)` traduce los saltos a
  CRLF en stdin; `git check-ignore --stdin` deja entonces de casar y **falla en
  silencio**. Pasa bytes.
- **Consola cp1252:** imprimir chino revienta con `UnicodeEncodeError`. Los
  oráculos llaman `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`.
- **El identificador sintético debe ser válido:** `FCMO-` más 12 hex en
  mayúsculas, o el validador de publicación lo rechaza con `invalid brief
  identifier` y te da un rojo por el motivo equivocado. El oráculo usa
  `FCMO-0C0DE0000001`.
- **`BLOQUEADO` no prueba nada**: mira los archivos en disco antes de rehacer
  trabajo que quizá ya aterrizó.

---

## 7. Decisiones ya tomadas — respétalas o ábrelas explícitamente

Viven en `10-Decisiones` de la vault del usuario, fuera de este repo y no
publicables. Las dos que más te van a afectar:

- **ADR-0009** — el texto legal **se traduce**, y cada bloque traducido inserta
  en runtime, sólo cuando el idioma no es `en`, una nota de que la versión en
  inglés es la que rige, con enlace a `?lang=en`. El marcador
  `data-fcmo-legal="canonical"` ya **no** significa «no traducir»; significa
  «aquí manda el inglés». Todo texto legal nuevo necesita entrada en los dos
  `ui.json` o el build rompe: falla cerrado, y es deseado.
- **ADR-0011** — la esclusa ARB → Newsletter: el corpus saneado llega a
  `corpus/`, la Newsletter ingiere, traduce, reconstruye el overlay y despliega.

---

## 8. Objetivo del usuario, literal

> «Resuelve todos los errores y fallas que se ven y encuentres, y construye lo
> necesario para que la Newsletter se refresque con nuevo contenido ya traducido
> de forma diaria, en base a la investigación de ARB. Aunque no funcione por el
> límite de uso, que el mecanismo esté funcionando y listo cuando mejoremos la
> org de FCMO-AI al plan de GitHub teams.»

Y como criterio permanente:

> «Todo el texto de la página debe estar en el idioma seleccionado, sin nada de
> inglés escabulléndose en Es y Zh.»

El mecanismo está construido. Lo que queda son los dos defectos de la sección 2
y los tres prerrequisitos de la sección 3.
