// Reproducible bundle: esbuild + a copy of the self-hosted fonts. No network, no CDN.
import { build } from 'esbuild'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.dirname(fileURLToPath(import.meta.url))
const dist = path.join(root, 'dist')
fs.rmSync(dist, { recursive: true, force: true })
fs.mkdirSync(path.join(dist, 'fonts'), { recursive: true })

await build({
  entryPoints: [path.join(root, 'src/main.js')], bundle: true, minify: true, format: 'iife', target: 'es2022',
  outfile: path.join(dist, 'app.js'), legalComments: 'none', logLevel: 'warning'
})
await build({ entryPoints: [path.join(root, 'src/app.css')], bundle: true, minify: true, outfile: path.join(dist, 'app.css'), loader: { '.woff2': 'file' }, external: ['*.woff2'], logLevel: 'warning' })

const fontSrc = path.resolve(root, '../../site-src/assets/fonts')
for (const f of fs.readdirSync(fontSrc).sort()) if (f.endsWith('.woff2')) fs.copyFileSync(path.join(fontSrc, f), path.join(dist, 'fonts', f))
fs.copyFileSync(path.join(root, 'src/index.html'), path.join(dist, 'index.html'))
fs.copyFileSync(path.join(root, 'src/favicon.svg'), path.join(dist, 'favicon.svg'))
console.log('studio/web/dist built')
