# Publicar — Javier y Matías

Para publicar la edición que ya fue revisada e integrada en `main`:

1. Abre **Actions → Deploy FCMO AI Newsletter → Run workflow**.
2. Selecciona **main**, operación **deploy**, y pulsa **Run workflow**.
3. Espera el resultado de **live-verify**: debe pasar antes de considerar publicada la edición. Abre la portada y comprueba la fecha y los tres idiomas.

Desde una terminal autenticada, la misma operación es una orden:

```sh
python3 ops/publish.py --publish
```

La acción ejecuta la suite, las seis comprobaciones del release congelado, los 14 gates del periódico, el navegador, el deploy y la comprobación del origen público. Un fallo previo al deploy conserva el sitio anterior. Si el candidato desplegado falla la comprobación pública, se reconstruye y vuelve a desplegar el tag `lkg`. La solicitud por terminal sólo confirma el despacho; el resultado está en Actions.

Si quieres recuperar la última edición comprobada, usa el mismo botón con **rollback**, o:

```sh
python3 ops/publish.py --rollback
```

Esta entrada publica el contenido integrado. Para cambiar una edición, abre un PR y espera **publish-gate** y la aprobación de un propietario del código. No publiques desde otra rama. La protección propuesta exige una aprobación independiente, también para Javier y Matías; no hay excepción por transcurrir 48 horas.

El comando vuelve a construir el corpus existente; no genera noticias ni traducciones ausentes. Tampoco activa las reglas remotas. Antes del primer uso protegido, el administrador debe completar [la instalación](PUBLISHING-SETUP.md). La revisión de contenido, el teléfono y el sitio de producción requieren una prueba real posterior a la integración; el ensayo local no demuestra esos resultados.
