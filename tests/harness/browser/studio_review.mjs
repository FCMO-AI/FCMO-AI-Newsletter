// Matías comments on the chosen paragraph at phone width, including a locale change.
import { session, go, check, finish } from './studio_common.mjs'
const slug=process.argv[3] || process.env.STUDIO_SLUG
if(!slug)throw new Error('A seeded, multi-paragraph fixture is required')
const s=await session(process.argv[2],{user:'matias',viewport:{width:390,height:844}}), p=s.page
await go(s,`#/p/${slug}/review`);await p.waitForSelector('.pv-frame')
for(const [locale,index] of [['en',1],['es-419',3]]){
  await p.getByRole('tab',{name:'Lectura',exact:true}).click()
  if(locale==='es-419')await p.locator('.pv-controls button').filter({hasText:/^ES$/}).click()
  const body=p.frameLocator('.pv-frame').locator('.essay-body [id^="b-"]')
  await body.nth(index).waitFor()
  const id=await body.nth(index).getAttribute('id')
  await body.nth(index).click()
  await p.getByRole('tab',{name:'Comentarios',exact:true}).click()
  const marker=`Private paragraph ${locale} ${Date.now()}`
  await p.locator('.rv-cmt textarea').fill(marker)
  await p.locator('.rv-cmt').getByRole('button',{name:'Enviar',exact:true}).click()
  await p.locator('.cmt').filter({hasText:marker}).waitFor()
  const comments=await p.evaluate(async slug=>(await(await fetch(`/api/pieces/${slug}/comments`)).json()),slug)
  const posted=comments.find(c=>c.body===marker)
  check(`phone comment targets selected ${locale} paragraph`,posted?.block_id===id&&posted?.locale===locale&&posted?.user==='matias',JSON.stringify({id,actual:posted?.block_id,locale:posted?.locale}))
  await p.locator('.cmt').filter({hasText:marker}).getByRole('button',{name:'Ir al párrafo',exact:true}).click()
  check('comment link returns to its preview',await p.locator('.rv-read').isVisible())
}
await finish(s)
