// New paths exercised through the real UI: issue assembly, correction, withdrawal.
// Runs only against dogfood's disposable store. No approval or external transport.
import { session, go, check, finish } from './studio_common.mjs'
const base=process.argv[2], authorSlug=process.env.STUDIO_ESSAY_SLUG, otherSlug=process.env.STUDIO_OTHER_SLUG
if (!authorSlug || !otherSlug) throw new Error('Dogfood published slugs required')
let s=await session(base,{user:'matias'}); let p=s.page
await go(s,'#/issues'); await p.waitForSelector('.iss-grid')
await p.locator('.lib-item .card.piece').first().dragTo(p.locator('[data-slot=principal]'))
const texts={en:['A curated issue','A human editorial note.'],'es-419':['Una edición curada','Una nota editorial humana.'],'zh-Hans':['精选版本','人类编辑说明。']}
const langIndex={'en':0,'es-419':1,'zh-Hans':2}
for(const loc of Object.keys(texts)){
  await p.locator('.editor-note .seg button').nth(langIndex[loc]).click()
  await p.locator('.issue-title').fill(texts[loc][0]);await p.locator('.editor-note textarea').fill(texts[loc][1])
  await p.waitForFunction(()=>document.querySelector('.save-state')?.textContent==='Guardado')
}
for(const loc of Object.keys(texts)){
  await p.locator('.editor-note .seg button').nth(langIndex[loc]).click()
  await p.getByRole('button',{name:'Marcar como revisado por mí',exact:true}).click()
  if(loc==='zh-Hans'){await p.locator('.modal input[type=checkbox]').check();await p.locator('.modal button:has-text("Confirmar")').click()}
  await p.waitForTimeout(200)
}
await p.getByRole('button',{name:'Publicar…',exact:true}).click()
await p.waitForSelector('.sheet'); await p.waitForSelector('.check-list',{state:'attached'})
check('issue language review unblocks request',!(await p.getByRole('button',{name:'Pedir revisión',exact:true}).isDisabled()))
check('issue lead retained',await p.evaluate(async()=>{const slug=location.hash.split('/')[2];const r=await(await fetch(`/api/issues/${slug}`)).json();return r.issue.slots.filter(x=>x.slot==='principal').length===1}))
await p.getByRole('button',{name:'Pedir revisión',exact:true}).click();await p.waitForSelector('.home-head')
await go(s,`#/p/${otherSlug}/en/preview`);await p.waitForSelector('.pv-frame')
await p.getByRole('button',{name:'Retirar',exact:true}).click();await p.locator('.modal select').selectOption('FACTUAL_ERROR')
const notes=['Withdrawal for a test.','Retiro para una prueba.','测试撤回。']
for(let i=0;i<3;i++)await p.locator('.modal textarea').nth(i).fill(notes[i])
await p.getByRole('button',{name:'Preparar revisión',exact:true}).click();await p.waitForSelector('.sheet')
const withdrawn=await p.evaluate(async slug=>(await(await fetch(`/api/pieces/${slug}`)).json()).meta,otherSlug)
check('withdrawal is a dated tombstone draft, awaiting review',withdrawn.status==='withdrawn'&&withdrawn.withdrawal.reason_code==='FACTUAL_ERROR'&&Object.keys(withdrawn.withdrawal.note).length===3)
await s.browser.close()
s=await session(base,{user:'javier'});p=s.page
await go(s,`#/p/${authorSlug}/en/preview`);await p.waitForSelector('.pv-frame')
await p.getByRole('button',{name:'Corregir',exact:true}).click();await p.locator('.modal select').selectOption('clarification')
for(let i=0;i<3;i++)await p.locator('.modal textarea').nth(i).fill(['A dated clarification.','Una aclaración fechada.','注明日期的说明。'][i])
await p.getByRole('button',{name:'Preparar revisión',exact:true}).click();await p.waitForSelector('.ed-body')
const corrected=await p.evaluate(async slug=>(await(await fetch(`/api/pieces/${slug}`)).json()),authorSlug)
check('correction retains text and records three notices',corrected.state==='amending'&&corrected.meta.corrections.at(-1).type==='clarification'&&Object.keys(corrected.meta.corrections.at(-1).note).length===3)
await finish(s)
