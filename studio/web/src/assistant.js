import { get, post } from './api.js'
import { t } from './i18n.js'
import { h, modal, toast } from './ui.js'

// Suggestions stay outside the document until a person chooses each paragraph.
export async function suggestions (slug, loc, kind = 'translate', button) {
  const queued = await post(`/api/pieces/${slug}/assist`, { kind, loc })
  if (queued.status === 'no_worker') { if (button) { button.disabled = true; button.textContent = t('assist.none') } return toast(t('assist.none')) }
  if (!queued.job_id) return toast(queued.plain_es || t('err.generic'))
  let active = true; let timer; let accepted = false
  const body = h('div', null, h('p', null, t('assist.wait')))
  modal({ title: t('assist.title'), body, onClose: reason => { active = false; clearTimeout(timer); if (accepted && reason !== 'route') location.reload() }, actions: [{ label: t('common.close'), onclick: close => { active = false; clearTimeout(timer); close() } }] })
  async function poll () {
    if (!active) return
    try {
      const result = await get(`/api/jobs/${queued.job_id}`)
      if (!result.suggestions) { timer = setTimeout(poll, 1500); return }
      body.replaceChildren(h('p', { class: 'notice soft' }, t('tr.agent')))
      let number = 0
      for (const suggestion of result.suggestions) {
        const text = h('textarea', { rows: 4, readonly: true, 'aria-label': t('tr.paragraph', { n: ++number }) }); text.value = suggestion.text || suggestion.flag || ''
        const apply = async () => {
          try {
            const current = await get(`/api/pieces/${slug}/doc/${loc}`)
            await post(`/api/jobs/${queued.job_id}/accept`, { base_rev: current.rev, block_ids: [suggestion.block_id], ...(text.readOnly ? {} : { edits: { [suggestion.block_id]: text.value } }) })
            accepted = true; row.remove(); toast('✓')
          } catch (e) { toast(e.data?.error_plain || t('err.generic'), 'bad') }
        }
        const row = h('section', { class: 'slot' }, text, h('div', { class: 'btn-row' },
          suggestion.text ? h('button', { class: 'btn small', onclick: apply }, t('assist.accept')) : null,
          suggestion.text ? h('button', { class: 'btn small', onclick: () => { text.readOnly = false; text.focus() } }, t('assist.edit')) : null,
          h('button', { class: 'btn small', onclick: () => row.remove() }, t('assist.discard'))))
        body.append(row)
      }
    } catch (e) { active = false; toast(e.data?.error_plain || t('err.generic'), 'bad') }
  }
  poll()
}
