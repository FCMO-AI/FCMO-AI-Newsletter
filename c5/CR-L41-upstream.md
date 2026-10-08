# ARB — reparación de ediciones nativas retenidas por Newsletter (L41)

El Airlock recibido el 8 de octubre conserva prosa inglesa en campos internos,
aunque los titulares y otros campos estén traducidos. Newsletter conserva el
material recibido y retiene estas cinco identidades; no genera traducciones.
La siguiente entrega válida vuelve a admitirlas automáticamente.

| Idioma | Identidad | Campo | Defecto |
|---|---|---|---|
| es-419 | FCMO-28A7A138B4E8 | claims[0].text | prosa inglesa |
| es-419 | FCMO-2B000C93D92A | technical.claimed_result | idéntico al original |
| es-419 | FCMO-710E8BDAF4B5 | technical.strongest_baseline | idéntico al original |
| es-419 | FCMO-727CB05A3E39 | technical.claimed_result | idéntico al original |
| zh-Hans | FCMO-28A7A138B4E8 | claims[0].text | prosa inglesa |
| zh-Hans | FCMO-503C5DEC490A | summary | prosa inglesa |
| zh-Hans | FCMO-710E8BDAF4B5 | technical.strongest_baseline | idéntico al original |

Reparar la traducción recursiva de `claims[].text`, `technical.claimed_result`,
`technical.strongest_baseline` y `summary`, además de recorrer todas las hojas de
prosa: limitaciones, contradicciones, descripciones de gaps y relaciones.
Preservar cifras, identidades, URLs, alcance y fuerza de evidencia. No traducir
los enums ni las identidades estructurales. Validar cada par completo antes de
emitirlo como edición nativa; un titular traducido no acredita los campos internos.

Newsletter acepta los diez tiers del rubric v2 sin inferirlos del score y
mantiene `reproduction_or_audit`, `signal_or_leak` y `other` como tipos distintos.
El oracle de Deploy también se ejecuta antes del commit del refresh.
