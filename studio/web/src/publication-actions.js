import { post } from './api.js'
import { t, LOCALE_NAME } from './i18n.js'
import { h, modal, toast } from './ui.js'

export function amendDialog (meta, withdrawal = false) {
  let type = withdrawal ? 'withdraw' : 'typo'
  let reason = 'EDITORIAL'
  const notes = {}; const fields = h('div')
  const draw = () => {
    fields.replaceChildren()
    if (type === 'typo') return
    for (const loc of ['en', 'es-419', 'zh-Hans'].filter(l => meta.meta.locales[l] === 'ready')) {
      const input = h('textarea', { rows: 3, 'aria-label': LOCALE_NAME[loc], lang: loc })
      input.value = notes[loc] || ''; input.addEventListener('input', () => { notes[loc] = input.value })
      fields.append(h('label', { class: 'f' }, LOCALE_NAME[loc], input))
    }
  }
  const select = h('select', { 'aria-label': t('amend.type'), onchange: e => { type = e.target.value; draw() } }, [['typo', 'amend.typo'], ['clarification', 'amend.clarification'], ['substantive', 'amend.substantive']].map(([v, k]) => h('option', { value: v }, t(k))))
  const reasons = h('select', { 'aria-label': t('amend.reason'), onchange: e => { reason = e.target.value } }, ['EDITORIAL', 'UPSTREAM_RETRACTION', 'UNVERIFIED_RELEASE', 'DUPLICATE', 'FACTUAL_ERROR', 'RIGHTS', 'PRIVACY', 'LEGAL'].map(v => h('option', { value: v }, t('amend.reason.' + v))))
  draw()
  modal({ title: t(withdrawal ? 'amend.withdraw' : 'amend.correct'), body: [h('p', null, t('amend.review')), withdrawal ? h('label', { class: 'f' }, t('amend.reason'), reasons) : select, fields], actions: [{ label: t('common.cancel') }, { label: t('amend.begin'), kind: 'primary', onclick: async close => {
    try {
      await post(`/api/pieces/${meta.slug}/${withdrawal ? 'withdraw' : 'correct'}`, { type, note: notes, reason_code: reason })
      close(); location.hash = `#/p/${meta.slug}/${withdrawal ? 'publish' : meta.source_locale}`
    } catch (e) { toast(e.data?.error_plain || t('err.generic'), 'bad') }
  } }] })
}

export function rollbackDialog () {
  const confirmation = h('input', { type: 'text', 'aria-label': t('amend.confirm') })
  modal({ title: t('amend.rollback'), body: [h('p', null, t('amend.limit')), h('label', { class: 'f' }, t('amend.confirm'), confirmation)], actions: [{ label: t('common.cancel') }, { label: t('amend.rollback'), kind: 'primary', onclick: async close => {
    if (confirmation.value !== 'Volver a la última versión comprobada') return
    try { await post('/api/site/rollback', { confirmation: confirmation.value }); close(); toast(t('amend.requested')) } catch (e) { toast(e.data?.error_plain || t('err.generic'), 'bad') }
  } }] })
}
