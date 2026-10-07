// Photo dropped directly onto the real writing surface (no file chooser).
import { session, go, check, finish, TINY_PNG } from './studio_common.mjs'
const s=await session(process.argv[2]), p=s.page
await p.click('text=Nuevo ensayo')
await p.locator('.modal input[type=text]').fill('Arrastrar una foto '+Date.now())
await p.getByRole('button',{name:'Empezar a escribir',exact:true}).click()
await p.waitForSelector('.ed-body')
await p.evaluate(bytes=>{
  const transfer=new DataTransfer();transfer.items.add(new File([Uint8Array.from(bytes)],'foto.png',{type:'image/png'}))
  document.querySelector('.ed-body').dispatchEvent(new DragEvent('drop',{bubbles:true,cancelable:true,dataTransfer:transfer}))
},Array.from(TINY_PNG))
await p.waitForSelector('.ed-figure img',{timeout:8000})
check('dropped photo re-encoded and inserted with editable caption/rights',await p.locator('.ed-figure .fig-field').count()>=3)
await p.waitForFunction(()=>document.querySelector('.save-state')?.textContent==='Guardado')
await p.reload();await p.waitForSelector('.ed-figure img')
check('dropped photo survives a real reload',await p.locator('.ed-figure img').count()===1)
if(s.errors.length)check('photo path has no console errors',false,s.errors.join(' | '))
await s.browser.close()
const m=await session(process.argv[2],{user:'matias'}), q=m.page
await go(m,'#/issues');await q.waitForSelector('.iss-grid')
await q.getByRole('tab',{name:'Briefs del día',exact:true}).click()
const cards=q.locator('.lib-item .card.brief'), ids=await cards.evaluateAll(els=>els.slice(0,2).map(e=>e.dataset.ref))
for(let i=0;i<2;i++)await cards.nth(i).dragTo(q.locator('[data-slot=day-in-ai]'))
await q.locator(`[data-slot=day-in-ai] .card[data-ref="${ids[1]}"]`).dragTo(q.locator(`[data-slot=day-in-ai] .slot-item[data-ref="${ids[0]}"]`))
const order=await q.locator('[data-slot=day-in-ai] .slot-item').evaluateAll(els=>els.map(e=>e.dataset.ref))
check('issue cards reorder by dragging within a slot',order[0]===ids[1]&&order[1]===ids[0])
await finish(m)
