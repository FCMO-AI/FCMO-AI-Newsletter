// Studio chrome strings. Spanish first, English second. Never code words: no git, branch, JSON, hash, gate.
const S = {
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
    'cmt.add': 'Comentar este párrafo', 'cmt.ph': 'Escribe un comentario', 'cmt.send': 'Enviar', 'cmt.resolve': 'Resolver', 'cmt.go': 'Ir al párrafo', 'cmt.empty': 'Sin comentarios por resolver.', 'cmt.never': 'Los comentarios nunca se publican.',
    'chk.go': 'Llévame ahí', 'chk.ok': 'Todo en orden', 'chk.todo': '{n} por resolver', 'chk.title': 'Antes de publicar',
    'tr.title': 'Idiomas', 'tr.source': 'Original', 'tr.target': 'Traducción', 'tr.changed': 'El original cambió', 'tr.human': 'escrito por persona', 'tr.agent': 'borrador del asistente', 'tr.agent.edited': 'asistente, editado por persona', 'tr.chip': 'Fijo: igual que en el original',
    'tr.review': 'Marcar como revisado por mí', 'tr.later': 'Publicar después', 'tr.reviewed': 'Revisado por {who}, {when}', 'tr.zh.confirm': 'Leí y entiendo el texto chino', 'tr.zh.ask': 'Para marcar el chino como revisado, confirma:', 'tr.confirm': 'Confirmar', 'tr.cancel': 'Cancelar', 'tr.draft': 'Volver a borrador', 'tr.empty': 'Este idioma aún no tiene texto.', 'tr.edit': 'Editar en la página', 'tr.pick': 'Idioma de destino', 'tr.paragraph': 'Párrafo {n}', 'tr.copy': 'Copiar del original', 'tr.assist': 'Pedir borrador al asistente', 'tr.nowork': 'El asistente no está disponible ahora. Puedes traducir tú.',
    'pv.title': 'Vista previa', 'pv.banner': 'Construida con el mismo código que el sitio público.', 'pv.light': 'Claro', 'pv.dark': 'Oscuro', 'pv.phone': 'Teléfono', 'pv.desktop': 'Escritorio', 'pv.theme': 'Tema', 'pv.size': 'Tamaño', 'pv.lang': 'Idioma', 'pv.back': 'Volver al texto', 'pv.noloc': 'Este idioma aún no tiene texto.',
    'pub.title': 'Publicar «{title}»', 'pub.lead': 'Cada línea se comprueba sola. Cuando todo esté en orden, pide la revisión de {who}.', 'pub.reviewer': 'Revisa {who}', 'pub.ask': 'Pedir revisión', 'pub.blocked': 'Aún hay {n} por resolver.', 'pub.sent': 'Revisión pedida. {who} la verá en su escritorio.', 'pub.mt': 'Se publicará con aviso de traducción automática: {langs}.', 'pub.rerun': 'Volver a comprobar',
    'rev.title': 'Revisión de «{title}»', 'rev.approve': 'Aprobar y publicar', 'rev.changes': 'Pedir cambios', 'rev.note': 'Nota para {who} (opcional)', 'rev.diff': 'Cambios desde la última versión publicada', 'rev.none': 'Es un texto nuevo: no hay versión anterior.', 'rev.confirm': 'Al aprobar, el texto se publicará en el sitio público. Eso no se deshace con un clic.', 'rev.own': 'No puedes revisar tu propio texto.', 'rev.waiting': 'Esperando a {who}.', 'rev.sent': 'Listo. {who} verá tu respuesta.', 'rev.preview': 'Lectura', 'rev.changes.tab': 'Cambios', 'rev.comments': 'Comentarios',
    'prog.title': 'Progreso de publicación', 'prog.done': 'Publicado', 'prog.failed': 'No se publicó', 'prog.working': 'Publicando…', 'prog.live': 'Ya está en el sitio', 'prog.home': 'Volver al escritorio',
    'iss.title': 'Ediciones', 'iss.lib': 'Biblioteca', 'iss.essays': 'Ensayos', 'iss.letters': 'Cartas y notas', 'iss.briefs': 'Briefs del día', 'iss.canvas': 'Edición', 'iss.main': 'Principal', 'iss.essay.slot': 'Ensayos', 'iss.day': 'El día en IA', 'iss.notes': 'Notas', 'iss.note': 'Nota del editor', 'iss.drop': 'Arrastra aquí', 'iss.add': 'Añadir', 'iss.remove': 'Quitar', 'iss.filter': 'Filtrar por fecha o tema', 'iss.class': 'Clase', 'iss.readonly': 'Solo lectura', 'iss.empty': 'Nada que mostrar con ese filtro.', 'iss.up': 'Subir', 'iss.down': 'Bajar', 'iss.soon': 'Guardar la edición estará disponible cuando el servidor lo ofrezca.', 'iss.badlang': 'Falta un idioma listo',
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
