# nl-suscripcion-fix — correcciones y evidencia

Correcciones de Kit 1–6: dominio parametrizado con prioridad fcmo.group y respaldo; buzón existente o alias creado primero; DNS por portapapeles/texto literal; paso 8 BLOQUEADO por dominio; diseño del correo/página alojada como unidad pendiente; parada de tracking y hecho del operador sobre Advanced Tracking. Ninguna operación hecha en la cuenta.

Aviso 1–3: se retiró la negación falsa de mediciones, se añadieron eventos y sección de tecnologías de rastreo en ES/EN/ZH y se alinearon región y nombre propuesto del responsable sin eliminar marcadores. **La alineación con el aviso corto aún necesita el cambio fuera de propiedad de NEEDS.md.** Retención, ARCO/autoridad vigente y clasificación/consentimiento de medición requieren revisión jurídica; este carril sin red no verificó derecho vigente ni aprueba el aviso.

Formulario 1/3/4/5: kicker neutro; un control de reintento; columna de contenido independiente del alto del formulario y espacio vertical reducido; regex de required en el input de correo; pruebas JS de foco, reintento y enlace de error. No cambió el JS de producción porque ya implementaba esas transiciones. Formulario 2/6 (captura completa y juicio de Matías) y diseño alojado siguen abiertos.

## Aceptación local
- `TMPDIR=/var/tmp PYTHONPATH=.:tests python3 -m unittest tests.test_subscribe_v2`: 15 pruebas, OK, sin omisiones.
- `TMPDIR=/var/tmp node --test tests/test_subscription_client.mjs`: 6 pruebas, OK, sin omisiones.
- Tres casos existentes de `tests.test_subscription_journey.SubscriptionJourneyTests`: `test_real_builder_emits_subscription_states_with_noindex_and_site_shell`, `test_form_has_pending_target_errors_and_language_links_in_each_locale`, `test_native_provider_locale_selector_is_submitted_with_the_form`: OK; builder real contra fixtures, flag apagada y salida temporal. Emitió 198 rutas, 57 feeds y 210 redirecciones.
- Antes de corregir, las regresiones nuevas reprodujeron nueve fallos de aserción/subcaso. Además se contrastaron los cinco métodos de regresión completos contra archivos y plantilla del HEAD base: 12 fallos de aserción/subcaso y cero errores, frente al candidato verde. La cobertura JS añadida pasaba ya en la base: faltaban pruebas, no una reparación del JS.
- Búsqueda requerida de la negación falsa en `legal` y `docs/suscripcion`: sin coincidencias; `grep -n "a9340e\|F05A28" site-src/assets/subscribe/subscribe.css`: sin coincidencias. Los dos valores naranja en minúsculas que permanecen son fondos/bordes existentes, no color de texto.
- `git diff --check`: limpio.

No se corrió la suite completa; no se atribuyen al candidato las 1274 pruebas de la revisión anterior. Total local de esta entrega: 24 pruebas (15 + 6 + 3), ninguna omitida. No habilitado el correo; sin llamadas a Kit, red, secretos, nuevos paquetes ni push.

## NO VERIFICADO / continuación
Capturas nuevas y geometría renderizada a 1440/390/320 en EN/ES/ZH: Claude fuera del sandbox, por encargo del brief. El test CSS prueba estructura, no distancia en píxeles. Pendientes diseño de correo/página Kit y juicio de Matías, DNS/remitente, soporte de tracking, revisión legal y prueba semilla de DOI/baja. No se afirma suscripción lista ni activación autorizada. NEEDS.md al final contiene las sustituciones exactas del aviso corto y dueño de continuación.

En juego: datos de suscriptores y reputación de FCMO → evidencia exigida: avisos concordantes aprobados, diseño juzgado y recorrido real DOI/baja → evidencia que hay: borradores corregidos y 24 pruebas locales → **NO-GO de activación**.
ÉTICA: material §1 y §2.1 → los lectores tienen derecho a una explicación veraz del rastreo; se declara y se preservan las paradas antes de recoger datos reales.

## CANON
Rutas relativas a `/srv/fcmo/agents/repos/FCMO-Agent-Hub/`, leídas con herramientas:

| Ruta | Principio que cambió la decisión |
| --- | --- |
| `standard/CORE.md` | L5: las pruebas de CSS/HTML no prueban la geometría ni el alta en Kit; dejé esas afirmaciones abiertas y el aviso corto como dependencia real. |
| `runtime/FCMO_RUNTIME_V1.txt` | Autoridad acotada: no activé correo ni convertí hechos aportados por el operador en comprobación de cuenta/DNS. |
| `AGENTS.md` | Ruteo: cargué las disciplinas e identidad exigidas y mantuve fuera de la edición los archivos de otros dueños. |
| `disciplines/SOFTWARE_ENGINEERING.md` | Reproduje rojo en la base y comprobé el candidato; agrupé título/lista para quitar la dependencia causal del alto del formulario. |
| `disciplines/VISUAL_ENGINEERING.md` | Inspección final: no inventé capturas y dejé pendiente el juicio visual del candidato, aunque las pruebas pasen. |
| `identity/README.md` | Conservé el diseño recibido y separé método visual de identidad; no improvisé el reemplazo de Kit stock rechazado. |
| `identity/readable/original/FCMO_Design_Current_V4.0.1_UNCHANGED.txt` | Paleta contenida: neutralicé el texto naranja del kicker conforme a la revisión. |
| `identity/readable/original/Desglose_de_la_simbologia_de_FCMO_UNCHANGED.txt` | El acento debe significar intervención, no decoración: conservé el cuadro existente y no extendí naranja al texto. |
| `identity/FCMO_TECHNICAL_EXPOSURE_GRADIENT_v0.1.md` | La atmósfera no se decide por dogma: conservé el híbrido entregado y reservé su aceptación comparada con R4 a Matías. |
| `disciplines/WORTHY_WORK.md` | La evidencia exigida nace de los datos/reputación en juego; 24 pruebas locales no permiten aprobar captación real ni llamar listo al flujo. |
| `policy/FCMO_ETHICAL_MORAL_CONSTITUTION_V1.md` | §1 y §2.1: sustituí la promesa falsa por descripción del píxel/clics y sus límites, sin transferir datos ni suplantar confirmación del responsable. |

`claudex` y `organismo` no están en PATH. Se buscó contexto en la bóveda por archivos y en el Hub/proyecto; el directorio de contexto Kyrion indicado por la instrucción de host no está montado en esta sesión. No se escribió estado vivo ni se inventaron notas/latidos.
