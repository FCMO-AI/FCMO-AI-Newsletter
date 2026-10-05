// Studio chrome strings. Spanish first, English second. Never code words: no git, branch, JSON, hash, gate.
export const S = {
  es: {
    'app.name': 'FCMO Studio', 'nav.home': 'Escritorio', 'nav.issues': 'Ediciones', 'nav.logout': 'Salir', 'nav.theme': 'Tema', 'nav.skip': 'Ir al contenido',
    'login.title': 'Entrar al estudio', 'login.user': 'Persona', 'login.pass': 'Contraseña', 'login.go': 'Entrar', 'login.bad': 'Esa combinación no es correcta. Revisa e inténtalo de nuevo.', 'login.lede': 'Un solo lugar para escribir, traducir y publicar.',
    'home.hello': 'Hola, {name}', 'home.new': 'Nuevo ensayo', 'home.letter': 'Carta', 'home.note': 'Nota', 'home.search': 'Buscar en tus textos',
    'home.attention': 'Necesita tu atención', 'home.continue': 'Seguir escribiendo', 'home.empty': 'Nada pendiente. Buen momento para escribir.',
    'home.drafts': 'Borradores', 'home.review': 'En revisión', 'home.published': 'Publicados', 'home.editions': 'Ediciones', 'home.none': 'Todavía no hay nada aquí.',
    'attn.review': '{who} pidió que revises «{title}».', 'attn.changes': '{who} pidió cambios en «{title}».', 'attn.failed': 'No se pudo publicar «{title}».', 'attn.open': 'Abrir', 'attn.read': 'Revisar',
    'row.words': '{n} palabras', 'row.by': 'de {who}', 'row.edited': 'editado {when}', 'ago.now': 'ahora mismo', 'ago.min': 'hace {n} min', 'ago.hour': 'hace {n} h', 'ago.day': 'hace {n} d',
    'kind.essay': 'Ensayo', 'kind.letter': 'Carta', 'kind.note': 'Nota',
    'state.ready': 'listo', 'state.drafting': 'en borrador', 'state.empty': 'vacío', 'state.later': 'se publica después',
    'new.title': 'Nuevo texto', 'new.name': 'Título de trabajo', 'new.lang': 'Idioma en que lo escribes', 'new.create': 'Empezar a escribir', 'new.hint': 'Puedes cambiar el título cuando quieras.',
    'ed.title': 'Escribe el título', 'ed.dek': 'Una frase que invite a leer', 'ed.byline': 'Por {who}', 'ed.min': '{n} min de lectura', 'ed.start': 'Empieza a escribir. Con «/» eliges un bloque.',
    'ed.words': '{n} palabras', 'ed.saved': 'Guardado', 'ed.saving': 'Guardando…', 'ed.offline': 'Sin conexión. Tu copia está a salvo en este navegador.', 'ed.dirty': 'Cambios sin guardar', 'ed.lang': 'Idioma',
    'ed.focus': 'Enfoque', 'ed.preview': 'Vista previa', 'ed.publish': 'Publicar…', 'ed.back': 'Escritorio', 'ed.translate': 'Idiomas', 'ed.readonly': '{who} está editando. Puedes leer y comentar.', 'ed.take': 'Tomar el control',
    'ed.restore.local': 'Hay una copia local más reciente que la guardada.', 'ed.restore.go': 'Restaurar tu copia local', 'ed.restore.drop': 'Descartarla',
    'ed.empty.lang': 'Este idioma todavía está vacío.', 'ed.empty.start': 'Empezar desde el original', 'ed.empty.blank': 'Escribir desde cero',
    'conf.title': 'Hay una versión más reciente', 'conf.body': 'Hay una versión más reciente (de {who}, {at}). Nada se ha perdido.', 'conf.diff': 'Ver diferencias', 'conf.mine': 'Usar la mía', 'conf.server': 'Usar la del servidor',
    'slash.h2': 'Título de sección', 'slash.h2.d': 'Divide el texto en partes numeradas', 'slash.h3': 'Subsección', 'slash.h3.d': 'Un título menor dentro de una sección',
    'slash.quote': 'Cita', 'slash.quote.d': 'Un pasaje de otra voz', 'slash.pull': 'Cita destacada', 'slash.pull.d': 'Una frase grande, para detenerse',
    'slash.ul': 'Lista', 'slash.ul.d': 'Elementos con viñeta', 'slash.ol': 'Lista numerada', 'slash.ol.d': 'Pasos u orden', 'slash.hr': 'Separador', 'slash.hr.d': 'Una pausa entre ideas',
    'slash.fig': 'Figura', 'slash.fig.d': 'Imagen con pie, crédito y licencia', 'slash.fn': 'Nota al pie', 'slash.fn.d': 'Aparece al margen sin romper la lectura', 'slash.src': 'Fuente', 'slash.src.d': 'Cita una fuente de tu lista',
    'slash.ev': 'Recuadro de evidencia', 'slash.ev.d': 'Clase, confianza y lo que no está establecido', 'slash.p': 'Párrafo', 'slash.p.d': 'Texto normal', 'slash.none': 'Nada coincide',
    'bub.b': 'Negrita', 'bub.i': 'Cursiva', 'bub.link': 'Enlace', 'bub.fn': 'Nota', 'bub.src': 'Fuente', 'link.ask': 'Dirección del enlace (https://…)', 'link.bad': 'Usa una dirección que empiece con https://',
    'fn.placeholder': 'Escribe la nota…', 'fn.heading': 'Notas',
    'fig.alt': 'Texto alternativo ({lang})', 'fig.alt.h': 'Describe la imagen para quien no la ve', 'fig.cap': 'Pie de figura ({lang})', 'fig.credit': 'Crédito', 'fig.licence': 'Licencia', 'fig.pick': 'Elegir imagen', 'fig.uploading': 'Subiendo imagen…', 'fig.fail': 'No se pudo subir la imagen.', 'fig.missing': 'Falta la imagen',
    'ev.class': 'Clase', 'ev.conf': 'Confianza', 'ev.limits': 'Lo que no está establecido', 'ev.title': 'Recuadro de evidencia', 'ev.A': 'A · verificada', 'ev.B': 'B · sólida', 'ev.C': 'C · provisional', 'ev.D': 'D · débil',
    'dr.toc': 'Índice', 'dr.versions': 'Versiones', 'dr.sources': 'Fuentes', 'dr.comments': 'Comentarios', 'dr.checks': 'Comprobaciones', 'dr.close': 'Cerrar', 'dr.toc.empty': 'Aún no hay títulos de sección.',
    'src.add': 'Añadir fuente', 'src.title': 'Título', 'src.author': 'Autor u organización', 'src.date': 'Fecha', 'src.url': 'Dirección (https://…)', 'src.accessed': 'Consultada el', 'src.locator': 'Ubicación (p. 4)', 'src.class': 'Clase de evidencia', 'src.none': 'Sin clase', 'src.empty': 'Aún no hay fuentes. Añade la primera.', 'src.del': 'Quitar', 'src.pick': 'Elige una fuente', 'src.new': 'Nueva fuente…', 'src.hint': 'La clase de evidencia es opcional.',
    'ver.empty': 'Todavía no hay versiones.', 'ver.name': 'Nombre de la versión', 'ver.save': 'Guardar versión', 'ver.restore': 'Restaurar', 'ver.compare': 'Comparar con el texto actual', 'ver.auto': 'Guardado automático', 'ver.restored': 'Versión restaurada. Lo anterior quedó guardado.', 'ver.confirm': 'Se guardará el texto actual y luego se restaurará esta versión. No se pierde nada.', 'ver.title': 'Versiones de «{title}»', 'ver.by': 'por {who}',
    'rev.pick': 'Toca un párrafo en la vista previa para comentarlo. Selecciona el párrafo antes de enviar.', 'rev.selected': 'Comentario sobre: {text}', 'cmt.add': 'Comentar este párrafo', 'cmt.ph': 'Escribe un comentario', 'cmt.send': 'Enviar', 'cmt.resolve': 'Resolver', 'cmt.go': 'Ir al párrafo', 'cmt.empty': 'Sin comentarios por resolver.', 'cmt.never': 'Los comentarios nunca se publican.',
    'chk.go': 'Llévame ahí', 'chk.ok': 'Todo en orden', 'chk.todo': '{n} por resolver', 'chk.title': 'Antes de publicar',
    'tr.title': 'Idiomas', 'tr.source': 'Original', 'tr.target': 'Traducción', 'tr.changed': 'El original cambió', 'tr.human': 'escrito por persona', 'tr.agent': 'borrador del asistente', 'tr.agent.edited': 'asistente, editado por persona', 'tr.chip': 'Fijo: igual que en el original',
    'tr.review': 'Marcar como revisado por mí', 'tr.later': 'Publicar después', 'tr.reviewed': 'Revisado por {who}, {when}', 'tr.zh.confirm': 'Leí y entiendo el texto chino', 'tr.zh.ask': 'Para marcar el chino como revisado, confirma:', 'tr.confirm': 'Confirmar', 'tr.cancel': 'Cancelar', 'tr.draft': 'Volver a borrador', 'tr.empty': 'Este idioma aún no tiene texto.', 'tr.edit': 'Editar en la página', 'tr.pick': 'Idioma de destino', 'tr.paragraph': 'Párrafo {n}', 'tr.copy': 'Copiar del original', 'tr.assist': 'Pedir borrador al asistente', 'tr.nowork': 'El asistente no está disponible ahora. Puedes traducir tú.',
    'pv.title': 'Vista previa', 'pv.banner': 'Construida con el mismo código que el sitio público.', 'pv.light': 'Claro', 'pv.dark': 'Oscuro', 'pv.phone': 'Teléfono', 'pv.desktop': 'Escritorio', 'pv.theme': 'Tema', 'pv.size': 'Tamaño', 'pv.lang': 'Idioma', 'pv.back': 'Volver al texto', 'pv.noloc': 'Este idioma aún no tiene texto.',
    'pub.title': 'Publicar «{title}»', 'pub.lead': 'Cada línea se comprueba sola. Cuando todo esté en orden, pide la revisión de {who}.', 'pub.reviewer': 'Revisa {who}', 'pub.ask': 'Pedir revisión', 'pub.blocked': 'Aún hay {n} por resolver.', 'pub.sent': 'Revisión pedida. {who} la verá en su escritorio.', 'pub.mt': 'Se publicará con aviso de traducción automática: {langs}.', 'pub.rerun': 'Volver a comprobar',
    'rev.title': 'Revisión de «{title}»', 'rev.approve': 'Aprobar y publicar', 'rev.changes': 'Pedir cambios', 'rev.note': 'Nota para {who} (opcional)', 'rev.diff': 'Cambios desde la última versión publicada', 'rev.none': 'Es un texto nuevo: no hay versión anterior.', 'rev.confirm': 'Al aprobar, el texto se publicará en el sitio público. Eso no se deshace con un clic.', 'rev.own': 'No puedes revisar tu propio texto.', 'rev.waiting': 'Esperando a {who}.', 'rev.sent': 'Listo. {who} verá tu respuesta.', 'rev.preview': 'Lectura', 'rev.changes.tab': 'Cambios', 'rev.comments': 'Comentarios',
    'prog.title': 'Progreso de publicación', 'prog.done': 'Publicado', 'prog.failed': 'No se publicó', 'prog.working': 'Publicando…', 'prog.live': 'Ya está en el sitio', 'prog.home': 'Volver al escritorio',
    'iss.title': 'Ediciones', 'iss.lib': 'Biblioteca', 'iss.essays': 'Ensayos', 'iss.letters': 'Cartas y notas', 'iss.briefs': 'Briefs del día', 'iss.canvas': 'Edición', 'iss.main': 'Principal', 'iss.essay.slot': 'Ensayos', 'iss.day': 'El día en IA', 'iss.notes': 'Notas', 'iss.note': 'Nota del editor', 'iss.drop': 'Arrastra aquí', 'iss.add': 'Añadir', 'iss.remove': 'Quitar', 'iss.filter': 'Filtrar por fecha o tema', 'iss.class': 'Clase', 'iss.readonly': 'Solo lectura', 'iss.empty': 'Nada que mostrar con ese filtro.', 'iss.up': 'Subir', 'iss.down': 'Bajar', 'iss.soon': 'Arma una edición con ensayos y briefs.', 'chk.running': 'Comprobando todo… puede tardar unos segundos.', 'iss.badlang': 'Falta un idioma listo',
    'err.net': 'No se pudo conectar. Inténtalo de nuevo en un momento.', 'err.generic': 'Algo no salió. Tu texto sigue a salvo.', 'err.notfound': 'No encontramos esto.', 'common.cancel': 'Cancelar', 'common.save': 'Guardar', 'common.close': 'Cerrar', 'common.open': 'Abrir', 'common.loading': 'Cargando…', 'common.you': 'ti', 'common.theme.auto': 'Automático',
    'zones.local': 'Esta aplicación funciona dentro de tu red privada.'
  },
  en: {
    'app.name': 'FCMO Studio', 'nav.home': 'Desk', 'nav.issues': 'Issues', 'nav.logout': 'Sign out', 'nav.theme': 'Theme', 'nav.skip': 'Skip to content',
    'login.title': 'Enter the studio', 'login.user': 'Person', 'login.pass': 'Password', 'login.go': 'Enter', 'login.bad': 'That combination is not right. Check it and try again.', 'login.lede': 'One place to write, translate and publish.',
    'home.hello': 'Hello, {name}', 'home.new': 'New essay', 'home.letter': 'Letter', 'home.note': 'Note', 'home.search': 'Search your pieces',
    'home.attention': 'Needs your attention', 'home.continue': 'Keep writing', 'home.empty': 'Nothing waiting. A good moment to write.',
    'home.drafts': 'Drafts', 'home.review': 'In review', 'home.published': 'Published', 'home.editions': 'Issues', 'home.none': 'Nothing here yet.',
    'attn.review': '{who} asked you to review “{title}”.', 'attn.changes': '{who} asked for changes to “{title}”.', 'attn.failed': '“{title}” could not be published.', 'attn.open': 'Open', 'attn.read': 'Review',
    'row.words': '{n} words', 'row.by': 'by {who}', 'row.edited': 'edited {when}', 'ago.now': 'just now', 'ago.min': '{n} min ago', 'ago.hour': '{n} h ago', 'ago.day': '{n} d ago',
    'kind.essay': 'Essay', 'kind.letter': 'Letter', 'kind.note': 'Note',
    'state.ready': 'ready', 'state.drafting': 'drafting', 'state.empty': 'empty', 'state.later': 'publish later'
  }
}
S.es['src.publisher'] = 'Organización o editorial'
S.en['src.publisher'] = 'Publisher or organization'
S.es['iss.date'] = 'Fecha de la edición'
S.en['iss.date'] = 'Edition date'
S.en['iss.soon'] = 'Put together an issue from essays and briefs.'
S.en['chk.running'] = 'Checking everything… this can take a few seconds.'
let lang = 'es'
export const setLang = l => { lang = S[l] ? l : 'es'; document.documentElement.lang = lang }
export const getLang = () => lang
export function t (key, vars) {
  let s = (S[lang] && S[lang][key]) || S.es[key] || key
  if (vars) for (const [k, v] of Object.entries(vars)) s = s.replaceAll(`{${k}}`, v)
  return s
}
export const LOCALE_NAME = { en: 'English', 'es-419': 'Español', 'zh-Hans': '中文' }
export const LOCALE_SHORT = { en: 'EN', 'es-419': 'ES', 'zh-Hans': '中文' }

/* second pass: new keys (es) and the complete English catalogue */
Object.assign(S.es, {
  'iss.dup': 'Ya está en la edición', 'iss.saved': 'Ediciones guardadas', 'iss.new': 'Nueva edición',
  'ed.more': 'Más acciones', 'chk.general': 'General', 'chk.done': '{n} en orden', 'chk.sr.ok': 'Listo: ', 'chk.sr.todo': 'Pendiente: ',
  'prog.empty.title': 'Todavía no se ha pedido publicar', 'prog.empty.lead': 'Cuando pidas la revisión, aquí verás cada paso hasta que el texto esté en el sitio.',
  'prog.empty.s1': 'Pides la revisión a {who}.', 'prog.empty.s2': '{who} lee el texto tal como lo verán los lectores y lo aprueba o pide cambios.',
  'prog.empty.s3': 'Se hacen las comprobaciones finales del sitio.', 'prog.empty.s4': 'El texto se publica y aquí aparecen los enlaces en vivo.', 'prog.empty.go': 'Preparar la publicación'
})
Object.assign(S.en, {
  'iss.dup': 'Already in the issue', 'iss.saved': 'Saved issues', 'iss.new': 'New issue',
  'ed.more': 'More actions', 'chk.general': 'General', 'chk.done': '{n} in order', 'chk.sr.ok': 'Done: ', 'chk.sr.todo': 'Pending: ',
  'prog.empty.title': 'Publication has not been requested yet', 'prog.empty.lead': 'Once you ask for review, you will see every step here until the text is on the site.',
  'prog.empty.s1': 'You ask {who} for a review.', 'prog.empty.s2': '{who} reads the text as readers will see it, then approves it or asks for changes.',
  'prog.empty.s3': 'The final site checks run.', 'prog.empty.s4': 'The text goes live and the live links appear here.', 'prog.empty.go': 'Prepare publication',
  'new.title': 'New text', 'new.name': 'Working title', 'new.lang': 'Language you write it in', 'new.create': 'Start writing', 'new.hint': 'You can change the title any time.',
  'ed.title': 'Write the title', 'ed.dek': 'One sentence that invites reading', 'ed.byline': 'By {who}', 'ed.min': '{n} min read', 'ed.start': 'Start writing. Type “/” to choose a block.',
  'ed.words': '{n} words', 'ed.saved': 'Saved', 'ed.saving': 'Saving…', 'ed.offline': 'Offline. Your copy is safe in this browser.', 'ed.dirty': 'Unsaved changes',
  'ed.lang': 'Language', 'ed.focus': 'Focus', 'ed.preview': 'Preview', 'ed.publish': 'Publish…', 'ed.back': 'Desk', 'ed.translate': 'Languages',
  'ed.readonly': '{who} is editing. You can read and comment.', 'ed.take': 'Take over', 'ed.restore.local': 'A local copy is newer than the saved one.', 'ed.restore.go': 'Restore your local copy', 'ed.restore.drop': 'Discard it',
  'ed.empty.lang': 'This language is still empty.', 'ed.empty.start': 'Start from the original', 'ed.empty.blank': 'Write from scratch',
  'conf.title': 'There is a newer version', 'conf.body': 'There is a newer version (by {who}, {at}). Nothing has been lost.', 'conf.diff': 'See differences', 'conf.mine': 'Use mine', 'conf.server': 'Use the server’s',
  'slash.h2': 'Section heading', 'slash.h2.d': 'Splits the text into numbered parts', 'slash.h3': 'Subsection', 'slash.h3.d': 'A smaller heading inside a section', 'slash.quote': 'Quote', 'slash.quote.d': 'A passage in another voice',
  'slash.pull': 'Pull quote', 'slash.pull.d': 'A large sentence, to make readers pause', 'slash.ul': 'List', 'slash.ul.d': 'Bulleted items', 'slash.ol': 'Numbered list', 'slash.ol.d': 'Steps or order', 'slash.hr': 'Divider', 'slash.hr.d': 'A pause between ideas',
  'slash.fig': 'Figure', 'slash.fig.d': 'Image with caption, credit and licence', 'slash.fn': 'Footnote', 'slash.fn.d': 'Appears in the margin without breaking the reading', 'slash.src': 'Source', 'slash.src.d': 'Cite a source from your list',
  'slash.ev': 'Evidence box', 'slash.ev.d': 'Class, confidence and what is not established', 'slash.p': 'Paragraph', 'slash.p.d': 'Plain text', 'slash.none': 'Nothing matches',
  'bub.b': 'Bold', 'bub.i': 'Italic', 'bub.link': 'Link', 'bub.fn': 'Note', 'bub.src': 'Source', 'link.ask': 'Link address (https://…)', 'link.bad': 'Use an address that starts with https://',
  'fn.placeholder': 'Write the note…', 'fn.heading': 'Notes', 'fig.alt': 'Alt text ({lang})', 'fig.alt.h': 'Describe the image for someone who cannot see it', 'fig.cap': 'Caption ({lang})', 'fig.credit': 'Credit', 'fig.licence': 'Licence',
  'fig.pick': 'Choose image', 'fig.uploading': 'Uploading image…', 'fig.fail': 'The image could not be uploaded.', 'fig.missing': 'Image missing',
  'ev.class': 'Class', 'ev.conf': 'Confidence', 'ev.limits': 'What is not established', 'ev.title': 'Evidence box', 'ev.A': 'A · verified', 'ev.B': 'B · solid', 'ev.C': 'C · provisional', 'ev.D': 'D · weak',
  'dr.toc': 'Contents', 'dr.versions': 'Versions', 'dr.sources': 'Sources', 'dr.comments': 'Comments', 'dr.checks': 'Checks', 'dr.close': 'Close', 'dr.toc.empty': 'No section headings yet.',
  'src.add': 'Add source', 'src.title': 'Title', 'src.author': 'Author or organization', 'src.date': 'Date', 'src.url': 'Address (https://…)', 'src.accessed': 'Accessed on', 'src.locator': 'Location (p. 4)', 'src.class': 'Evidence class',
  'src.none': 'No class', 'src.empty': 'No sources yet. Add the first one.', 'src.del': 'Remove', 'src.pick': 'Choose a source', 'src.new': 'New source…', 'src.hint': 'The evidence class is optional.',
  'ver.empty': 'No versions yet.', 'ver.name': 'Version name', 'ver.save': 'Save version', 'ver.restore': 'Restore', 'ver.compare': 'Compare with the current text', 'ver.auto': 'Autosave',
  'ver.restored': 'Version restored. The previous text was kept.', 'ver.confirm': 'The current text will be saved, then this version restored. Nothing is lost.', 'ver.title': 'Versions of “{title}”', 'ver.by': 'by {who}',
  'rev.pick': 'Tap a paragraph in the preview to comment on it. Select the paragraph before sending.', 'rev.selected': 'Comment on: {text}', 'cmt.add': 'Comment on this paragraph', 'cmt.ph': 'Write a comment', 'cmt.send': 'Send', 'cmt.resolve': 'Resolve', 'cmt.go': 'Go to paragraph', 'cmt.empty': 'No comments to resolve.', 'cmt.never': 'Comments are never published.',
  'chk.go': 'Take me there', 'chk.ok': 'All in order', 'chk.todo': '{n} to resolve', 'chk.title': 'Before publishing',
  'tr.title': 'Languages', 'tr.source': 'Original', 'tr.target': 'Translation', 'tr.changed': 'The original changed', 'tr.human': 'written by a person', 'tr.agent': 'assistant draft', 'tr.agent.edited': 'assistant, edited by a person',
  'tr.chip': 'Fixed: same as the original', 'tr.review': 'Mark as reviewed by me', 'tr.later': 'Publish later', 'tr.reviewed': 'Reviewed by {who}, {when}', 'tr.zh.confirm': 'I have read and understand the Chinese text',
  'tr.zh.ask': 'To mark the Chinese as reviewed, confirm:', 'tr.confirm': 'Confirm', 'tr.cancel': 'Cancel', 'tr.draft': 'Back to draft', 'tr.empty': 'This language has no text yet.', 'tr.edit': 'Edit on the page',
  'tr.pick': 'Target language', 'tr.paragraph': 'Paragraph {n}', 'tr.copy': 'Copy from the original', 'tr.assist': 'Ask the assistant for a draft', 'tr.nowork': 'The assistant is not available now. You can translate yourself.',
  'pv.title': 'Preview', 'pv.banner': 'Built with the same code as the public site.', 'pv.light': 'Light', 'pv.dark': 'Dark', 'pv.phone': 'Phone', 'pv.desktop': 'Desktop', 'pv.theme': 'Theme', 'pv.size': 'Size', 'pv.lang': 'Language', 'pv.back': 'Back to the text', 'pv.noloc': 'This language has no text yet.',
  'pub.title': 'Publish “{title}”', 'pub.lead': 'Every line checks itself. When everything is in order, ask {who} for a review.', 'pub.reviewer': '{who} reviews', 'pub.ask': 'Ask for review', 'pub.blocked': '{n} still to resolve.',
  'pub.sent': 'Review requested. {who} will see it on their desk.', 'pub.mt': 'It will be published with a machine-translation notice: {langs}.', 'pub.rerun': 'Check again',
  'rev.title': 'Review of “{title}”', 'rev.approve': 'Approve and publish', 'rev.changes': 'Ask for changes', 'rev.note': 'Note for {who} (optional)', 'rev.diff': 'Changes since the last published version', 'rev.none': 'This is a new text: there is no earlier version.',
  'rev.confirm': 'By approving, the text will be published on the public site. That cannot be undone with one click.', 'rev.own': 'You cannot review your own text.', 'rev.waiting': 'Waiting for {who}.', 'rev.sent': 'Done. {who} will see your answer.',
  'rev.preview': 'Reading', 'rev.changes.tab': 'Changes', 'rev.comments': 'Comments',
  'prog.title': 'Publication progress', 'prog.done': 'Published', 'prog.failed': 'Not published', 'prog.working': 'Publishing…', 'prog.live': 'It is now on the site', 'prog.home': 'Back to the desk',
  'iss.title': 'Issues', 'iss.lib': 'Library', 'iss.essays': 'Essays', 'iss.letters': 'Letters and notes', 'iss.briefs': 'Daily briefs', 'iss.canvas': 'Issue', 'iss.main': 'Main', 'iss.essay.slot': 'Essays', 'iss.day': 'AI of the day', 'iss.notes': 'Notes',
  'iss.note': 'Editor’s note', 'iss.drop': 'Drop here', 'iss.add': 'Add', 'iss.remove': 'Remove', 'iss.filter': 'Filter by date or topic', 'iss.class': 'Class', 'iss.readonly': 'Read-only', 'iss.empty': 'Nothing matches that filter.', 'iss.up': 'Move up', 'iss.down': 'Move down', 'iss.badlang': 'A language is not ready',
  'err.net': 'Could not connect. Try again in a moment.', 'err.generic': 'Something went wrong. Your text is safe.', 'err.notfound': 'We could not find this.',
  'common.cancel': 'Cancel', 'common.save': 'Save', 'common.close': 'Close', 'common.open': 'Open', 'common.loading': 'Loading…', 'common.you': 'you', 'common.theme.auto': 'Automatic', 'zones.local': 'This app works inside your private network.'
})
Object.assign(S.es, {
  'amend.reason.EDITORIAL': 'Decisión editorial', 'amend.reason.UPSTREAM_RETRACTION': 'La fuente retiró la información', 'amend.reason.UNVERIFIED_RELEASE': 'Información aún sin verificar', 'amend.reason.DUPLICATE': 'Publicación duplicada', 'amend.reason.FACTUAL_ERROR': 'Error en los hechos', 'amend.reason.RIGHTS': 'Derechos de uso', 'amend.reason.PRIVACY': 'Privacidad', 'amend.reason.LEGAL': 'Motivo legal',
  'amend.type': 'Tipo de corrección', 'amend.typo': 'Errata', 'amend.clarification': 'Aclaración', 'amend.substantive': 'Corrección sustantiva', 'amend.correct': 'Corregir', 'amend.withdraw': 'Retirar', 'amend.review': 'La modificación necesita otra revisión antes de publicarse.', 'amend.reason': 'Motivo del retiro. Escribe una nota en cada idioma.', 'amend.begin': 'Preparar revisión', 'amend.rollback': 'Volver a la última versión comprobada del sitio', 'amend.limit': 'Esta recuperación es temporal. No deshace lo que un lector ya vio; el retiro revisado sigue siendo necesario.', 'amend.confirm': 'Escribe: Volver a la última versión comprobada', 'amend.requested': 'Recuperación solicitada. Comprueba el sitio antes de darla por terminada.',
  'assist.title': 'Sugerencias del asistente', 'assist.accept': 'Aceptar', 'assist.edit': 'Editar', 'assist.discard': 'Descartar', 'assist.wait': 'Esperando sugerencias…', 'assist.none': 'Ningún asistente conectado', 'assist.qa': 'Revisar presentación', 'assist.qa.done': 'Revisión visual terminada', 'pub.public': 'Al aprobar, el texto se vuelve público en GitHub.'
})
Object.assign(S.en, {
  'amend.reason.EDITORIAL': 'Editorial decision', 'amend.reason.UPSTREAM_RETRACTION': 'The source retracted the information', 'amend.reason.UNVERIFIED_RELEASE': 'Information not yet verified', 'amend.reason.DUPLICATE': 'Duplicate publication', 'amend.reason.FACTUAL_ERROR': 'Factual error', 'amend.reason.RIGHTS': 'Usage rights', 'amend.reason.PRIVACY': 'Privacy', 'amend.reason.LEGAL': 'Legal reason',
  'amend.type': 'Correction type', 'amend.typo': 'Typo', 'amend.clarification': 'Clarification', 'amend.substantive': 'Substantive correction', 'amend.correct': 'Correct', 'amend.withdraw': 'Withdraw', 'amend.review': 'The change requires another review before publication.', 'amend.reason': 'Withdrawal reason. Write a notice in each language.', 'amend.begin': 'Prepare review', 'amend.rollback': 'Restore the last verified site version', 'amend.limit': 'Recovery is temporary. It cannot undo what a reader has seen; the reviewed withdrawal is still needed.', 'amend.confirm': 'Type: Volver a la última versión comprobada', 'amend.requested': 'Recovery requested. Check the site before confirming completion.',
  'assist.title': 'Assistant suggestions', 'assist.accept': 'Accept', 'assist.edit': 'Edit', 'assist.discard': 'Discard', 'assist.wait': 'Waiting for suggestions…', 'assist.none': 'No assistant connected', 'assist.qa': 'Review layout', 'assist.qa.done': 'Visual review completed', 'pub.public': 'Approval makes the text public on GitHub.'
})

Object.assign(S.es, { 'assist.dek': 'Sugerir título e introducción', 'assist.cites': 'Revisar fuentes' })
Object.assign(S.en, { 'assist.dek': 'Suggest title and introduction', 'assist.cites': 'Check sources' })

Object.assign(S.es, { 'ver.first': 'Primera versión', 'ver.second': 'Segunda versión', 'ver.compare.two': 'Comparar versiones' })
Object.assign(S.en, { 'ver.first': 'First version', 'ver.second': 'Second version', 'ver.compare.two': 'Compare versions' })

Object.assign(S.es, { 'iss.confidence': 'Confianza', 'iss.importance': 'Importancia', 'confidence.strongly_supported': 'Respaldo sólido', 'confidence.reported': 'Reportado', 'confidence.unconfirmed': 'Sin confirmar', 'confidence.disputed': 'Disputado' })
Object.assign(S.en, { 'iss.confidence': 'Confidence', 'iss.importance': 'Importance', 'confidence.strongly_supported': 'Strongly supported', 'confidence.reported': 'Reported', 'confidence.unconfirmed': 'Unconfirmed', 'confidence.disputed': 'Disputed' })

Object.assign(S.es, { 'confidence.confirmed': 'Confirmado', 'confidence.supported': 'Respaldado', 'confidence.supported_with_limits': 'Respaldado con límites', 'confidence.claimed_unverified': 'Declarado, sin verificar' })
Object.assign(S.en, { 'confidence.confirmed': 'Confirmed', 'confidence.supported': 'Supported', 'confidence.supported_with_limits': 'Supported with limits', 'confidence.claimed_unverified': 'Claimed, unverified' })
