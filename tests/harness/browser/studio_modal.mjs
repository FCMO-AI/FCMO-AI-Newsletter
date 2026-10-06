// Recovery dialogs belong to their screen; leaving preserves the private buffer.
import {session,go,check,finish} from './studio_common.mjs'
const slug=process.argv[3]||process.env.STUDIO_SLUG
if(!slug)throw new Error('Seeded fixture required')
const s=await session(process.argv[2]), p=s.page
await p.evaluate(async slug=>{
 const target=await(await fetch(`/api/pieces/${slug}/doc/es-419`)).json()
 const key=`studio:buf:${slug}:es-419`
 const doc=target.doc;doc.blocks[1].content=[{t:'text',v:'Una copia local con 42 ideas.'}]
 localStorage.setItem(key,JSON.stringify({doc,at:Date.now()+1000,rev:target.rev}))
},slug)
await go(s,`#/p/${slug}/en/translate/es-419`)
await p.getByRole('button',{name:'Restaurar tu copia local',exact:true}).waitFor()
check('a different local buffer requires an explicit recovery choice',await p.locator('.modal').isVisible())
await go(s,`#/p/${slug}/review`);await p.waitForSelector('.rv-panes')
check('leaving translation dismisses its dialog',await p.locator('.modal').count()===0)
check('leaving preserves the private local copy',await p.evaluate(slug=>!!localStorage.getItem(`studio:buf:${slug}:es-419`),slug))
await finish(s)
