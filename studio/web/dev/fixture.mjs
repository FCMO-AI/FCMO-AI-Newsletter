// Sample piece used by the dev mock and by the essay page builder. Sample text only.
const t = (v, marks) => (marks ? { t: 'text', v, marks } : { t: 'text', v })
const fn = id => ({ t: 'fn', id })
const cite = (key, locator) => (locator ? { t: 'cite', key, locator } : { t: 'cite', key })
const p = (id, ...content) => ({ id, type: 'p', content })

const copy = {
  en: {
    title: 'The quiet work of being believed',
    dek: 'Trust is not announced. It accumulates in small, checkable promises, and it leaves when they stop being kept.',
    h: ['What a promise costs', 'Evidence before enthusiasm', 'A ledger that anyone can read'],
    a1: ['Every company says it can be trusted. The ones that are, rarely say so. They ', 'make a small promise, keep it where others can see, and then make another', '. After a year this looks like character. It is really bookkeeping.'],
    a2: ['A promise is cheap on the day it is made. Its cost arrives later, when keeping it is inconvenient and nobody would notice if it were quietly dropped.'],
    quote: 'Trust is the residue of promises kept when no one was checking.',
    b1: ['We hold our own claims to one rule: say what is established, say how well, and say what is not. A claim without its limits is a mood.'],
    b2: ['Readers do not need us to be certain. They need us to be legible, so that they can disagree with us for the right reasons.'],
    ev: 'Not established: whether readers act differently once limits are stated. We only know they complain less about surprises.',
    cap: 'A page of the ledger, 2026. Every line has a date, a source and a person who answers for it.', credit: 'FCMO, sample figure',
    c1: ['The ledger is dull on purpose. It lists what we said, what happened, and the distance between them. Anyone may read it', 'and a few do'],
    c2: ['Being believed is slow work. It is also the only kind that survives a bad week.'],
    n1: 'Sample note: this footnote is shown beside the paragraph on wide screens and under it on a phone.',
    n2: 'Second sample note, to show how margin notes stack without colliding.',
    s1: ['Sample source A', 'Example Press, 2025'], s2: ['Sample source B', 'Example Institute, 2026']
  },
  'es-419': {
    title: 'El trabajo silencioso de que te crean',
    dek: 'La confianza no se anuncia. Se acumula en promesas pequeñas y comprobables, y se va cuando dejan de cumplirse.',
    h: ['Lo que cuesta una promesa', 'Evidencia antes que entusiasmo', 'Un registro que cualquiera puede leer'],
    a1: ['Toda empresa dice que se puede confiar en ella. Las que lo merecen casi nunca lo dicen. ', 'Hacen una promesa pequeña, la cumplen a la vista de otros y luego hacen otra', '. Al cabo de un año parece carácter. En realidad es contabilidad.'],
    a2: ['Prometer es barato el día en que se promete. El costo llega después, cuando cumplir es incómodo y nadie notaría que la promesa se abandonó en silencio.'],
    quote: 'La confianza es el residuo de las promesas cumplidas cuando nadie estaba mirando.',
    b1: ['Nos exigimos una sola regla: decir qué está establecido, con cuánta solidez y qué no lo está. Una afirmación sin sus límites es un estado de ánimo.'],
    b2: ['Los lectores no necesitan que seamos seguros. Necesitan que seamos legibles, para poder discrepar de nosotros por las razones correctas.'],
    ev: 'No establecido: si los lectores actúan distinto cuando se declaran los límites. Solo sabemos que se quejan menos de las sorpresas.',
    cap: 'Una página del registro, 2026. Cada línea tiene fecha, fuente y una persona que responde por ella.', credit: 'FCMO, figura de ejemplo',
    c1: ['El registro es aburrido a propósito. Enumera lo que dijimos, lo que pasó y la distancia entre ambos. Cualquiera puede leerlo', 'y algunos lo hacen'],
    c2: ['Que te crean es un trabajo lento. También es el único que sobrevive a una mala semana.'],
    n1: 'Nota de ejemplo: este pie de página aparece junto al párrafo en pantallas anchas y debajo en el teléfono.',
    n2: 'Segunda nota de ejemplo, para ver cómo se apilan las notas del margen sin chocar.',
    s1: ['Fuente de ejemplo A', 'Example Press, 2025'], s2: ['Fuente de ejemplo B', 'Example Institute, 2026']
  },
  'zh-Hans': {
    title: '被相信，是一项安静的工作',
    dek: '信任不靠宣布。它在细小而可核对的承诺中积累，承诺不再兑现时便悄然离去。',
    h: ['一个承诺的代价', '先有证据，再有热情', '任何人都能读的账本'],
    a1: ['每家公司都说自己值得信任。真正值得的，很少这样说。它们', '先做一个小承诺，在众人看得见的地方兑现，然后再做下一个', '。一年之后，这看起来像品格，其实是记账。'],
    a2: ['承诺在许下的那天很便宜。代价来得晚，在兑现变得不便、而且没人会注意承诺被悄悄放弃的时候。'],
    quote: '信任，是无人检查时仍然兑现的承诺所留下的沉淀。',
    b1: ['我们对自己的说法只有一条规则：说清什么已经确立、确立到什么程度、什么尚未确立。没有限定的断言，只是一种情绪。'],
    b2: ['读者不需要我们确定无疑。他们需要我们清晰可读，这样才能出于正确的理由与我们意见不合。'],
    ev: '尚未确立：读者在看到限定之后是否会改变行为。我们只知道，他们对意外的抱怨变少了。',
    cap: '账本的一页，2026年。每一行都有日期、来源和为其负责的人。', credit: 'FCMO，示例图',
    c1: ['账本刻意写得乏味。它列出我们说过什么、发生了什么，以及两者之间的距离。任何人都可以阅读', '也有少数人真的读了'],
    c2: ['被相信是缓慢的工作，也是唯一能撑过糟糕一周的工作。'],
    n1: '示例注释：在宽屏上显示在段落旁边，在手机上显示在段落下方。',
    n2: '第二条示例注释，用来展示边注如何层叠而不相撞。',
    s1: ['示例来源 A', 'Example Press，2025'], s2: ['示例来源 B', 'Example Institute，2026']
  }
}

export const LOCALES = ['en', 'es-419', 'zh-Hans']
export const piece = {
  schema: 'fcmo-piece-v1', id: 'FCMO-P-5a1e0c0ffee1', kind: 'essay', slug: 'el-trabajo-silencioso', brand: 'fcmo',
  authors: [{ key: 'javier', name: 'Javier' }], source_locale: 'es-419', status: 'published',
  first_published_at: '2026-10-04T15:00:00Z', updated_at: '2026-10-04T15:00:00Z',
  locales: { en: 'ready', 'es-419': 'ready', 'zh-Hans': 'ready' }, hero: null, tags: [], corrections: [], withdrawal: null
}
export const sources = [
  { key: 'src-a', title: 'Sample source A', author: 'Example Author', publisher: 'Example Press', date: '2025-03-01', url: 'https://example.org/a', accessed: '2026-09-30', locator: '', evidence_class: 'B' },
  { key: 'src-b', title: 'Sample source B', author: 'Example Institute', publisher: 'Example Institute', date: '2026-01-15', url: 'https://example.org/b', accessed: '2026-09-30', locator: '', evidence_class: '' }
]
export const figures = {
  'fig-ledger': { file: 'figures/fig-ledger.svg', width: 1200, height: 630, credit: 'FCMO', licence: 'CC BY 4.0', alt: { en: 'A ledger page with dated lines', 'es-419': 'Una página de registro con líneas fechadas', 'zh-Hans': '带日期条目的账本页面' }, caption: Object.fromEntries(Object.entries(copy).map(([l, c]) => [l, c.cap])) }
}

export function doc (loc) {
  const c = copy[loc]
  return {
    schema: 'fcmo-essay-doc-v1', locale: loc, title: c.title, dek: c.dek,
    blocks: [
      p('b-00000001', t(c.a1[0]), t(c.a1[1], ['em']), t(c.a1[2])),
      { id: 'b-00000002', type: 'h2', content: [t(c.h[0])] },
      p('b-00000003', t(c.a2[0]), fn('fn-00000001'), t(' '), cite('src-a', 'p. 4')),
      { id: 'b-00000004', type: 'pullquote', content: [t(c.quote)] },
      { id: 'b-00000005', type: 'h2', content: [t(c.h[1])] },
      p('b-00000006', t(c.b1[0]), fn('fn-00000002')),
      p('b-00000007', t(c.b2[0] + ' '), cite('src-b')),
      { id: 'b-00000008', type: 'evidence', content: [], attrs: { class: 'B', confidence: loc === 'en' ? 'Moderate' : loc === 'zh-Hans' ? '中等' : 'Moderada', limits: [t(c.ev)] } },
      { id: 'b-00000009', type: 'h2', content: [t(c.h[2])] },
      { id: 'b-0000000a', type: 'figure', content: [], attrs: { fig: 'fig-ledger' } },
      p('b-0000000b', t(c.c1[0] + ', '), t(c.c1[1], ['strong']), t('.')),
      p('b-0000000c', t(c.c2[0]))
    ],
    footnotes: { 'fn-00000001': [t(c.n1)], 'fn-00000002': [t(c.n2)] }
  }
}
export const docs = Object.fromEntries(LOCALES.map(l => [l, doc(l)]))
if (process.argv[2] === '--json') process.stdout.write(JSON.stringify({ piece, sources, figures, docs }, null, 1))
