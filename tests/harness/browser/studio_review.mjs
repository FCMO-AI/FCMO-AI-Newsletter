// A saved review link (the second-person review screen is retired, c59d060f9) lands on the Publish sheet; the other
// author sees no approval or comment control, and the chosen paragraph of both languages still reads at phone width.
import { session, go, check, finish, previewTimeout } from './studio_common.mjs'
const slug=process.argv[3] || process.env.STUDIO_SLUG
if(!slug)throw new Error('A seeded, multi-paragraph fixture is required')
const s=await session(process.argv[2],{user:'matias',viewport:{width:390,height:844}}), p=s.page
await go(s,`#/p/${slug}/review`);await p.waitForSelector('.check-list',{state:'attached'})
check('a saved review link lands on the publish sheet',/\/publish$/.test(await p.evaluate(()=>location.hash)))
check('only the author can press Publicar',await p.locator('.btn-row').getByRole('button',{name:'Publicar',exact:true}).isDisabled())
check('no second-person approval or comment control remains',await p.getByRole('button',{name:/Aprobar|Pedir cambios|Comentar|Enviar/}).count()===0)
for(const [locale,index] of [['en',1],['es-419',3]]){
  await go(s,`#/p/${slug}/${locale}/preview`);await p.waitForSelector('.pv-frame')
  const body=p.frameLocator('.pv-frame').locator('.essay-body [id^="b-"]')
  await body.nth(index).waitFor({ timeout: previewTimeout })
  await body.nth(index).click()
  check(`paragraph ${index} of the ${locale} preview reads at phone width`,(await body.nth(index).innerText()).trim().length>0)
  check(`the ${locale} preview does not scroll sideways on the phone`,await p.evaluate(()=>document.documentElement.scrollWidth-document.documentElement.clientWidth<=1))
}
await finish(s)
