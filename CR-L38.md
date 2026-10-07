# CR-L38 — coherencia de fuente, traducciones y recibos

Fecha: 2026-10-07. Rama: `c5/l29-main`, PR #61.

## Causa comprobada

El árbol heredado de L35 combina tres momentos distintos: `corpus/` contiene
la entrega del 7 de octubre; `release-src/` y sus traducciones habían avanzado
respecto del overlay congelado; `translation-status.json` todavía contaba 46
historias. En el overlay anterior, `FCMO-9E06CC5FA8A5` tenía 5 claims y 4
limitaciones; la fuente editable y los locales ya tenían 6 y 5. El hash global
también correspondía a otro corte. La ausencia del manifest del candidato era
una consecuencia del ensamblado rechazado, no un archivo que hubiera que inventar.

L31 restauró el paso de regenerar el estado de traducciones antes del ACK.
Eso corrige el orden del workflow de esta rama, pero `finalize` seguía dependiendo
de que otro paso actualizara un archivo derivado. El error observado en main
puede repetirse si ese paso no está presente o si conserva el recibo anterior.

Además, `refresh_locale_identity.py` renovaba hashes globales sin vincular cada
campo traducido al inglés que realmente se tradujo. La prueba roja mostró que
cambiar «matches» por «fails to match», manteniendo números y estructura, dejaba
la traducción declarada `NATIVE_ARB`. Truncar listas por posición también podía
asociar una traducción a un item distinto tras retirar el primero en inglés.

## Cambio

Los paquetes conservan `source_bindings` por historia y campo: huella de la prosa
inglesa y del valor traducido. Un refresco automático de metadatos no renueva
esas huellas. Una fuente cambiada deja su pareja historia/locale `PENDING`;
el Story layer no recibe la prosa obsoleta y la ruta muestra el aviso localizado
con enlace al original inglés. ES y ZH pueden tener backlogs distintos.

Los deltas airlocked nuevos vinculan su propio contenido. Reimportar el mismo
texto no renueva una vinculación antigua. El desk puede vincular campos recién
traducidos mediante `--bind-updated-fields` y debe pasar la validación estricta;
el workflow automático no utiliza esa opción. Los hashes iniciales se migraron
antes de regenerar la fuente, desde el corte ya medido, sin redactar traducciones.

`newsroom_receipt.py finalize` ahora vuelve a clasificar el conjunto de historias
recién construido y produce sus páginas pendientes y recibo antes del ACK.
Conserva las comprobaciones de conteos, IDs, estados, media y backlog. Un recibo
antiguo deja de ser una dependencia externa del paso de finalización.

Se recompusieron la fuente desde el corpus público existente, los locales,
Story, media local, overlay y READY_TO_PUBLISH. El candidato contiene 50 historias
vivas y la edición del 7 de octubre; las 50 parejas de cada locale están vigentes.
Se conservaron los recibos de investigación existentes después de comprobar que
sus firmas coinciden con las fuentes recompuestas. La Visual Desk se ejecutó
offline; no se afirmó investigación de red nueva ni despliegue.

Las pruebas de ledger ahora verifican preservación exacta de todos los registros
comprometidos, procedencia de cada nueva fecha desde Story y punto fijo en una
copia temporal completada. La composición puede preceder al ledger del corpus;
no se modificó el corpus para forzar la igualdad de esos dos cortes.

## Evidencia y límite

Las regresiones cubren cambio semántico sin cambio de forma, eliminación de un
item, refrescos repetidos, aprobación editorial explícita y backlog independiente
por locale. La fixture de extremo a extremo modifica una copia del corpus,
conserva su delta anterior, sustituye un recibo de conteo cero, ejecuta Story →
ACK → paper y comprueba las rutas pendientes y el inglés corregido.

La evidencia final y el resultado del push se registran en `REPORT.md`.
Claude debe repetir la aceptación antes de merge. El push de la rama no confirma
CI, merge, despliegue ni continuidad autónoma en el origen público.

**Resumen:** la traducción obsoleta queda pendiente por locale; el recibo se
recalcula desde la edición actual y el release local vuelve a ser coherente.
