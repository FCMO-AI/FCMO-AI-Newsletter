# Revisión Opus (10-26)

**Verdicts:** Kit **FIX** · Aviso **FIX** · Formulario **FIX**. None is GO yet.

**Checks I ran**
- `python` does not exist on the host, so I used `PYTHONPATH=.:tests python3 -m unittest discover -s tests`. Result: `Ran 1274 tests in 1643.854s — OK (skipped=9)`.
- My first full run died partway through. The log ends in `.E` with no summary, exit 1. A verbose rerun passed, so this looks flaky or environmental. I did not find the cause.
- `git diff --stat`: 4 files, +174/−33.
  - The only test file changed is `tests/test_subscribe_v2.py` (+37, no lines removed). No assertion was weakened.
  - One new assertion is too weak: `assertIn('required', html)` after the email check passes on the checkbox's own `required`. It should match the email input's own tag.
- `test_subscription_client.mjs` passes 4/4, but it does not cover the new retry button or the error link.

**(1) Kit — FIX**
1. **Wrong primary domain.** All three docs (`/var/tmp/kyrion-test/wt-nl-suscripcion/docs/suscripcion/KIT-FREE.md`, `LISTA-KIT-MATIAS.md`, `BLOQUE-JAVIER-DNS.md`) hard-code `news.fcmogroup.com`.
   - The 10-26 decision: fcmo.group is the official domain and the Newsletter goes first; `news.fcmogroup.com` is only the fallback if fcmo.group fails.
   - Fix: add a step 0 that picks `news.fcmo.group` if it is bought and in DNS, otherwise `news.fcmogroup.com`. Make the domain a variable in the list and in Javier's block.
2. **Sender step cannot be completed.** Step 2 uses `hola@news.fcmogroup.com`, but that subdomain has no mailbox (mail only exists on the root domain, Google Workspace). Kit's confirmation email to that address would never arrive. Use an existing Workspace mailbox, or create the alias first, and say so in the step.
3. **Steps 4 and 5 contradict each other.** Step 4 says «no los copies a mano»; step 5 says copy them. Step 5 also passes the DKIM values to Javier as a screenshot, which invites typos. Send them as text (portapapeles or a text message) and tell Javier's Claude to take them verbatim.
4. **Step 8 has an unfilled placeholder.** «te la paso» leaves the three confirmation-page URLs (EN/ES/ZH) blank. Write the literal URLs, or mark the step as blocked.
5. **Rejected look not addressed.** The Kit confirmation email and the hosted Kit page are in the Hub gallery as rejected (`identity/galeria/rechazados/newsletter-suscripcion-generica`). Step 8 only checks their text. Add a step to replace the email body and style the hosted form, or record it as a pending design unit.
6. **Tracking needs a stop condition.** `legal/email-privacy-kit.json` says open and click tracking «must be disabled… before activation». Step 9 should say: ask Kit support; if it can't be turned off, do not set COMPLIANCE_READY until the notice is changed.
- **What's already fine:**
  - Claims carry links, and anything unknown is labelled «NO CONFIRMADO». I did not re-check them live, and the pricing page (429) is still unread.
  - Javier's block has no secrets and fits «one plain step + pégale esto a tu Claude». Adding that the DNS is at GoDaddy and what he will see on screen would help.

**(2) Aviso — FIX**
1. **A false claim.** Section 3, in ES, EN and ZH, denies measuring opens and clicks (original false claim; corrected in this lane). The Kit research found no documented way to turn off the open pixel. Replace it with a true description (Kit's pixel and click counting) or make publishing depend on Kit support confirming it is off. The consent line in `docs/suscripcion/AVISO.md` («solo para eso») has the same problem.
2. **Missing LFPDPPP element.** There is no section on tracking technologies (web beacons in the email, GitHub Pages logs): what is collected, what for, and how to block it, e.g. turning off remote images. Add it, and list open/click events in section 2 if the pixel stays.
3. **Short and full notices disagree.** The short notice already names Matías Peña Szőke as the responsible party and mentions «fuera de México y del EEE»; the full notice says only «fuera de México». Align them, keeping the placeholders until Matías confirms.
4. **Still open from the report:** a fixed number for retention, and lawyer review of the ARCO deadlines (20+15 days) and the competent authority after the 2025 reform.
- **What's already fine:**
  - Placeholders are intact and balanced: 7 per language across `{{RESPONSABLE}}`, `{{DOMICILIO}}`, `{{CORREO_PRIVACIDAD}}` and `{{FECHA}}`.
  - The three translations have the same 10 sections with the same content.
  - Kit and GitHub are disclosed as processors. The 30-day backup claim matches `backup-email.yml` (`retention-days: 30`).

**(3) Formulario — FIX**
1. **More orange than claimed.** The kicker text «GRATIS · DIARIO» is orange. It comes from `site-src/assets/subscribe/subscribe.css` line 2: `.subscribe-v2 .section-kicker{color:#a9340e}`. So the report's «único naranja es el cuadrito» is false, and Design V4.0.1 rules out decorative orange. Set the kicker text to a neutral colour.
2. **Error capture is incomplete.** `capturas/estado-error-es-390.png` does not show the hosted-page link; it is cut off by the viewport and bottom bar. Recapture it.
   - That link, and the noscript fallback, send people to the Kit hosted page, which is the rejected stock look. Style that page or document the decision.
3. **Duplicate link in the pending state.** It offers «¿otra dirección?» twice: the serif link «…prueba con otra dirección.» and the button «¿Otra dirección? Usa una distinta». Merge them into one.
4. **Empty space at 1440.** There is a gap of about 100 px between the lede and the proof list, and dead space below the list.
5. **Tests to add:** a JS test for the retry button and the error link, and a tighter regex for the email input's `required`.
6. **Needs Matías's judgment.** The form is a light page with a dark panel; R4 is an all-dark page. It is a hybrid, not a 1:1 copy of the approved R4, so under the canon it is not «visually complete» until Matías judges it.
- **What's already fine:**
  - The consent box is required and unchecked, and links the notice in all 3 languages.
  - With the flag off there is no `<form>`, only «coming soon» (test plus the `apagado` capture).
  - The states make no false claims: «Si se recibió tu solicitud…», with no claim of subscription.
  - It is clearly not the generic Kit look.


## Nota del carril de corrección (10-26)

Esta revisión describe el estado anterior. La cita de la promesa falsa sobre medición se parafraseó arriba para que no sobreviva como texto vigente en la búsqueda de aceptación. El original tiene **ocho**, no siete, marcadores de cuerpo por idioma: responsable ×1, domicilio ×2, contacto ×4, fecha ×1; se conservaron exactamente. Resultados y límites del candidato: `CIERRE-FIX.md`. Las capturas de esta revisión no acreditan el candidato corregido.
