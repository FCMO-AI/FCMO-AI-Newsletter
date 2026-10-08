"""Server errors and persisted publication progress in both Studio UI languages."""
ERRORS = {
    'Javier debe iniciar sesión en GitHub.': 'Javier needs to sign in to GitHub.',
    'Matías debe iniciar sesión en GitHub.': 'Matías needs to sign in to GitHub.',
    'Inicia sesión para continuar.': 'Sign in to continue.',
    'Abre el inicio de sesión desde Studio.': 'Open the sign-in page from Studio.',
    'Recarga Studio antes de continuar.': 'Reload Studio before continuing.',
    'El archivo es demasiado grande.': 'The file is too large.',
    'No se pudo iniciar sesión. Revisa tus datos o espera 15 minutos.': 'Sign-in failed. Check your details or wait 15 minutes.',
    'Hay una versión más reciente. Compara las versiones antes de guardar.': 'A newer version exists. Compare versions before saving.',
    'Revisa los datos enviados.': 'Check the information you sent.',
    'La página no existe.': 'This page does not exist.',
    'No se pudo completar la operación. Tu última versión guardada sigue disponible.': 'The operation could not finish. Your last saved version remains available.',
    'La publicación en vivo aún no está habilitada.': 'Live publication has not been enabled yet.',
    'La otra persona debe revisar y aprobar la publicación.': 'The other person must review and approve this publication.',
    'La otra persona debe pedir cambios.': 'The other person must request changes.',
    'Solo el autor puede pedir revisión del borrador.': 'Only the author can request review of this draft.',
    'Completa las comprobaciones antes de pedir revisión.': 'Complete the checks before requesting review.',
    'El artículo cambió durante las comprobaciones; vuelve a pedir revisión.': 'The article changed during the checks; request review again.',
    'El artículo cambió; pide una nueva revisión.': 'The article changed; request a new review.',
    'El artículo cambió después de aprobarlo.': 'The article changed after approval.',
    'La versión pública cambió; pide una nueva revisión.': 'The public version changed; request a new review.',
    'La publicación contiene un archivo no permitido.': 'The publication contains a file that is not allowed.',
    'La publicación contiene cambios fuera del artículo.': 'The publication includes changes outside this article.',
    'La versión aprobada cambió antes de publicar.': 'The approved version changed before publication.',
    'Las comprobaciones locales fallaron. Revisa el artículo; nada se hizo público.': 'Local checks failed. Review the article; nothing was made public.',
    'Las comprobaciones locales no pudieron terminar. Nada se publicó.': 'Local checks could not finish. Nothing was published.',
    'Las comprobaciones públicas fallaron. Corrige el artículo y pide revisión otra vez.': 'Public checks failed. Correct the article and request review again.',
    'Las comprobaciones públicas cambiaron; revisa el artículo.': 'Public checks changed; review the article.',
    'Las comprobaciones públicas no terminaron en 30 minutos.': 'Public checks did not finish within 30 minutes.',
    'Publicación protegida aún no activa.': 'Protected publication is not active yet.',
    'GitHub no permitió publicar. Revisa los permisos y las protecciones.': 'GitHub refused publication. Check permissions and protections.',
    'GitHub no permitió publicar. Revisa la revisión y las comprobaciones.': 'GitHub refused publication. Check the review and checks.',
    'Falta la credencial personal para publicar.': 'The personal publication credential is missing.',
    'La respuesta de publicación no está confirmada.': 'The publication response is unconfirmed.',
    'No se confirmó la respuesta. Se está comprobando el estado antes de repetir la acción.': 'The response was not confirmed. The state is being checked before repeating the action.',
    'No se pudo confirmar el envío. Se comprobará antes de repetirlo.': 'The upload could not be confirmed. Its state will be checked before any retry.',
    'No se confirmó el cierre de la revisión anterior.': 'Closing the previous review has not been confirmed.',
    'No se pudo confirmar la identidad de revisión.': 'The reviewer identity could not be confirmed.',
    'El despliegue falló. La publicación aún no está confirmada.': 'Deployment failed. Publication is still unconfirmed.',
    'El despliegue no terminó en 30 minutos; comprueba su estado.': 'Deployment did not finish within 30 minutes; check its state.',
    'Desplegado pero aún no visible.': 'Deployed but not visible yet.',
    'Desplegado pero aún no visible. Revisa el sitio antes de confirmar la publicación.': 'Deployed but not visible yet. Check the site before confirming publication.',
    'La vista previa espera la integración del formato de ensayos con el sitio.': 'Preview is waiting for the essay format to be integrated with the site.',
    'Solo el autor puede ver sus sugerencias.': 'Only the author can see their suggestions.',
    'Solo el autor puede pedir ayuda sobre su borrador.': 'Only the author can request assistance on their draft.',
}
PROGRESS = {
    'approved': ('Revisado por la otra persona.', 'Reviewed by the other person.'),
    'candidate': ('Comprobaciones locales aprobadas.', 'Local checks passed.'),
    'pushed': ('El texto ya es público en GitHub.', 'The text is now public on GitHub.'),
    'pr_open': ('Revisión pública abierta.', 'Public review opened.'),
    'reviewed': ('Aprobación pública confirmada.', 'Public approval confirmed.'),
    'checks_green': ('Comprobaciones públicas aprobadas.', 'Public checks passed.'),
    'merged': ('Publicación aceptada; esperando despliegue.', 'Publication accepted; waiting for deployment.'),
    'deployed': ('Desplegado; comprobando la página visible.', 'Deployed; checking the visible page.'),
    'deployed_unverified': ('Desplegado pero aún no visible.', 'Deployed but not visible yet.'),
    'published': ('Publicado; las tres páginas fueron comprobadas.', 'Published; all three pages were verified.'),
    'failed': ('La publicación se detuvo. Revisa el motivo indicado.', 'Publication stopped. Check the stated reason.'),
}

def localize(body, language):
    if language != 'en': return body
    if isinstance(body, list): return [localize(item, language) for item in body]
    if isinstance(body, dict):
        out = {key: localize(value, language) for key, value in body.items()}
        value = out.get('error_plain')
        if value:
            if value.endswith(' está editando.'): out['error_plain'] = value.replace(' está editando.', ' is editing.')
            else: out['error_plain'] = ERRORS.get(value, 'The operation could not finish. Check the publication details before continuing.')
        return out
    return body
