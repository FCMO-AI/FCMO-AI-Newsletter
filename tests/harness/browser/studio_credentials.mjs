// Run against a fixture launched with two empty personal gh configurations.
import { session, check, finish } from './studio_common.mjs'
import fs from 'node:fs'
const base = process.argv[2]
const frames = process.argv[3]
const s = await session(base)
for (const width of [390, 1440]) {
  await s.page.setViewportSize({ width, height: 900 })
  await s.page.waitForSelector('#publication-readiness:not([hidden])')
  const banner = await s.page.locator('#publication-readiness').innerText()
  check(`both missing logins visible at ${width}`, banner.includes('Falta iniciar sesión de Javier.') && banner.includes('Falta iniciar sesión de Matías.'))
  check(`no horizontal overflow at ${width}`, await s.page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
  check(`empty home has no null text at ${width}`, !/^null$/m.test(await s.page.locator('.home').innerText()))
  if (frames) {
    fs.mkdirSync(frames, { recursive: true })
    await s.page.screenshot({ path: `${frames}/missing-credentials-${width}.png`, fullPage: true })
  }
}
await finish(s)
