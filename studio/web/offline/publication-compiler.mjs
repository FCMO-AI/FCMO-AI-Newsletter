// Bounded native-JS compilation for the author publication sheet. The dependency
// bundle is immutable; changed function bodies come verbatim from current source.
// Every byte outside these supported regions remains pinned and fails closed.
import fs from 'node:fs'
import path from 'node:path'
import crypto from 'node:crypto'
const hash = s => crypto.createHash('sha256').update(s).digest('hex')
const SEED = '20e3cfd3dc20a0ebb44bdf6e73ba5336bf3c2873b050ccc472820bb1e0b54d7f'
function region (source, begin, end) {
  const a = source.indexOf(begin), b = source.indexOf(end, a)
  if (a < 0 || b < 0) throw Error('No se reconoce el bloque de publicación offline; usa esbuild.')
  return { body: source.slice(a, b), rest: source.slice(0, a) + source.slice(b) }
}
export function publicationParts (root) {
  const read = p => fs.readFileSync(path.join(root, p), 'utf8')
  const sheet = region(read('src/screens-flow.js'), 'export async function publishScreen (', '/* ---------------- review (S6)')
  const review = region(sheet.rest, 'export async function reviewScreen (', '/* ---------------- progress (S7)')
  const halt = region(read('src/publication-actions.js'), 'export function haltPlan (', '// While halted')
  const strings = region(read('src/i18n.js'), '// Author publication contract', '\nObject.assign(S.es, AUTHOR_PUBLICATION_STRINGS.es)')
  return { sheet, review, halt, strings }
}
export function publicationBundle (root, seed) {
  if (hash(seed) !== SEED) throw Error('La semilla de publicación cambió; reconstruye con esbuild.')
  const parts = publicationParts(root)
  const pins = JSON.parse(fs.readFileSync(path.join(root, 'offline/publication-rest.json'), 'utf8'))
  const normalized = { 'src/screens-flow.js': parts.review.rest, 'src/publication-actions.js': parts.halt.rest,
    'src/i18n.js': parts.strings.rest.replace('\nObject.assign(S.es, AUTHOR_PUBLICATION_STRINGS.es)\nObject.assign(S.en, AUTHOR_PUBLICATION_STRINGS.en)\n', '') }
  for (const [name, source] of Object.entries(normalized)) {
    if (hash(source) !== pins[name]) throw Error(`Cambió código fuera de la publicación en ${name}; usa esbuild.`)
  }
  // These symbols belong only to the hash-pinned seed above. No guessing or eval.
  return `\n{\nconst get=K, post=Y, put=Qe, h=d, t=u, clear=ae, toast=G, shell=Ne, session=_, checksList=yn, LOCALE_NAME=Be;
const LOCS=Zt, crumbs=en, other=Dt, INTEGRITY=dl;
${parts.sheet.body.replace(/^export /, '')}
${parts.halt.body.replace(/^export /, '')}
${parts.review.body.replace(/^export /, '')}
${parts.strings.body.replace('export const', 'const')}
Object.assign(ie.es, AUTHOR_PUBLICATION_STRINGS.es); Object.assign(ie.en, AUTHOR_PUBLICATION_STRINGS.en);
nl=publishScreen; Hr=haltPlan; rl=reviewScreen;
}\n`
}
