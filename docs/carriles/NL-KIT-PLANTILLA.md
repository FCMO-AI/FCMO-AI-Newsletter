# Carril nl-kit-plantilla: el correo de confirmación como plantilla de Kit, sin marcadores propios

Lee el Hub: `runtime/FCMO_RUNTIME_V1.txt` y `disciplines/SOFTWARE_ENGINEERING.md` (en el checkout local del Agent Hub). Lee el `AGENTS.md` del repo.

**Problema.** `tools/email_confirm_render.py` genera `email/kit/confirmacion/{en,es,zh}.html` como correo completo con un marcador propio `{{CONFIRM_URL}}` (botón y enlace de respaldo). Kit no expone una variable para el enlace de confirmación: el botón lo pone Kit en el editor del correo de incentivo («The Incentive Email uses your default template»). Por eso `test_confirmation_email_has_no_unresolved_markers` es `expectedFailure` y el paso manual de `docs/EMAIL-PROVIDERS.md` §plantillas es frágil.

**Hechos de Kit (help.kit.com, artículo 2810454 «troubleshooting html email templates»):** una plantilla HTML de Kit válida exige `{{ message_content }}` (lo que se escribe en el editor; el preview falla sin él), un enlace de baja `{{ unsubscribe_url }}` (o `{{ unsubscribe_link }}`) y la dirección física `{{ address }}`. El correo de incentivo usa la plantilla por defecto y Kit inserta su propio botón de confirmación en el cuerpo.

**Hazlo así.**
1. Divide la salida en dos piezas por idioma: (a) `email/kit/plantilla/{en,es,zh}.html`: plantilla de Kit con el diseño actual (cabecera, tipografía, pie con `{{ address }}` y `{{ unsubscribe_url }}`) y `{{ message_content }}` donde va el cuerpo; (b) `email/kit/incentivo/{en,es,zh}.md` (o `.txt`): el texto del cuerpo para pegar en el editor del correo de incentivo, con la instrucción de usar el botón de confirmación propio de Kit (texto del botón por idioma: los que ya existen).
2. Quita `{{CONFIRM_URL}}` del renderizador y de las salidas. Mantén `email/kit/confirmacion/` sólo si algo vivo lo usa (grep); si no, retíralo y di dónde estaba.
3. Pruebas (rojo antes, verde después): cada plantilla contiene exactamente una vez `{{ message_content }}`, `{{ unsubscribe_url }}` y `{{ address }}`, y ninguna otra llave `{{…}}`; el texto del incentivo no contiene llaves; quita el `expectedFailure` y convierte el test en una aserción real. Ajusta `tests/test_subscription_journey.py` al nuevo contrato.
4. Actualiza `docs/EMAIL-PROVIDERS.md` (sección de plantillas): pasos exactos en Kit para Javier (Ajustes → plantillas de correo → pegar HTML; formulario → correo de incentivo → pegar texto y dejar el botón de Kit) y la prueba de envío. Lenguaje llano.

**Dueño de archivos:** `tools/email_confirm_render.py`, `email/kit/**`, `tests/test_subscription_journey.py`, `docs/EMAIL-PROVIDERS.md`. Nada más.

**Aceptación (corre tú):**
- `nice -n 10 python3 -m unittest tests.test_subscription_journey` → OK, sin expected failures.
- `python3 tools/email_confirm_render.py` regenera sin diff (`git status --short email/` vacío tras regenerar).
- `grep -rn "CONFIRM_URL" . --include=*.py --include=*.html --include=*.md | grep -v docs/carriles` → vacío.

Commits pequeños en esta rama, sin push. Ya existe: Kit soporta plantillas con `{{ message_content }}` (doc oficial arriba) → ADOPTAR su mecanismo de botón; no inventamos marcador. Reporte final ≤10 líneas: COMMITS, ACCEPTANCE, archivos retirados, UNVERIFIED.
