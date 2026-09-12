# Handoff — estado canónico de FCMO AI Newsletter

**Actualizado:** 2026-09-12  
**Estado:** `PRODUCTION_HARDENING_AND_FRESHNESS_CONVERGENCE`  
**Sitio:** https://fcmo-ai.github.io/FCMO-AI-Newsletter/

La meta normativa de producto está en [`PRODUCT_GOAL.md`](PRODUCT_GOAL.md). Toda sesión futura dedicada específicamente a Newsletter debe tratarla como el objetivo principal junto con `AGENTS.md`.

## 1. Estado real

La Newsletter ya superó la etapa `AWAITING_GITHUB_APP_ONLY`: el bridge autenticado, newsroom autónomo, release gates, Pages y live oracle han completado al menos un round-trip real hasta producción.

El 2026-09-12 se verificó una release cuyo headline principal fue `FCMO-955A495823F7` (NVIDIA / OpenAI-linked infrastructure finance). El build comprobó el headline actual en navegador real para EN/ES/ZH, comprobó layout responsive en 17 combinaciones de ruta/viewport, verificó receipt, desplegó GitHub Pages y después ejecutó un oracle post-deploy contra el origen público en navegador real. Los tres jobs finales —build, deploy y live oracle— concluyeron `success`.

Esto demuestra que el camino end-to-end puede funcionar. **No demuestra todavía por sí solo una racha prolongada de ciclos diarios totalmente desatendidos.** Esa diferencia es ahora parte explícita del estándar de producto.

## 2. Arquitectura de producción

El camino deseado y operativo es:

`ARB -> PUBLICATION_READY immutable snapshot -> read-only GitHub App -> publication seal -> sanitized _public_release -> corpus/ -> autonomous newsroom -> native EN/ES/ZH -> public-source re-research -> Story/editorial surfaces -> frozen release -> publication gates -> GitHub Pages -> post-deploy browser oracle -> production health`

El repositorio privado ARB no se hace público. El checkout privado es efímero y se destruye antes del staging público. Sólo bytes sanitizados sobreviven al Airlock.

## 3. Cambio de fase

La prioridad ya no es “activar por primera vez” la Newsletter. La prioridad es convertirla en el periódico real y aburridamente confiable descrito por `PRODUCT_GOAL.md`.

Orden de prioridad:

1. demostrar ciclos diarios repetidos y desatendidos;
2. asegurar freshness real de portada;
3. distinguir con claridad evidencia verificada de material developing/signal sin ocultar noticias recientes útiles;
4. detectar automáticamente en qué etapa se produce cualquier stale state;
5. mantener fail-closed, privacidad, localización y release integrity;
6. mejorar presentación sólo cuando no compita con confiabilidad/frescura.

## 4. Freshness: problema actual

La cronología pública puede dar la impresión de detenerse alrededor del 3 de septiembre aunque el corpus/Story layer ya contenga material posterior. Eso no debe racionalizarse como comportamiento aceptable.

La Newsletter es un periódico, no el espejo del último watermark histórico exhaustivamente cerrado de ARB.

Meta editorial de producción:

- preferir noticias materiales del día actual o del día anterior;
- mantener al menos una noticia material <=48 h cuando exista material legítimo;
- usar lane **verified** para evidencia fuerte;
- usar lane **developing/signal** para material reciente valioso que aún conserve gaps explícitos;
- nunca convertir frescura o importancia en confianza falsa;
- recurrir a material más viejo sólo cuando la ventana reciente no tenga nada suficientemente material.

La edad del front-page lead y de la noticia pública más reciente deben convertirse en señales de health, no en observaciones manuales.

## 5. Definición de salud de producción

Un deploy verde que sirve noticias stale **no está sano**.

Production health debe poder distinguir, como mínimo:

- edad del material upstream más reciente;
- edad del snapshot `PUBLICATION_READY`;
- edad del material más reciente recibido en `corpus/`;
- edad del Story más reciente;
- edad del front-page lead;
- último newsroom refresh exitoso;
- último Pages deploy exitoso;
- último live-browser oracle exitoso.

Esto debe permitir localizar si el atraso está en ARB readiness, bridge, corpus, newsroom/editorial selection, deploy o serving.

## 6. Evidencia que sí cuenta

No declarar una release o reparación “realmente lista” por una sola capa.

Para reader-visible outcomes, la evidencia fuerte termina en producción: build candidate -> browser/runtime checks -> deploy -> public-origin check -> real-browser post-deploy check.

Un workflow configurado, un commit, un HTML correcto o un deployment API `success` por sí solos no prueban el producto final.

## 7. Fallo y recuperación

La Newsletter permanece fail-closed. Si una nueva candidate falla privacidad, localización, release integrity, rendering, deployment o live verification, conservar la última known-good release pública y reparar la etapa causal.

No debilitar gates para “hacerlo verde”. No convertir una falla técnica ordinaria en una nueva acción manual para el usuario si puede resolverse dentro del sistema.

## 8. Próximo trabajo recomendado

El siguiente trabajo de mayor valor es implementar/fortalecer el **freshness SLO** y sus health checks, de modo que un periódico técnicamente desplegado pero con portada vieja falle observabilidad de producción de forma explícita.

Después, observar varios ciclos programados consecutivos sin intervención y conservar receipts diarios que demuestren:

`fresh snapshot -> bridge -> newsroom -> release -> Pages -> live oracle`.

Sólo entonces conviene llamar al sistema no sólo funcional, sino operacionalmente confiable.
