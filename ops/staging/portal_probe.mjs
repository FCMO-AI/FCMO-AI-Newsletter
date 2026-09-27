import {createRequire} from 'node:module';
import process from 'node:process';
const require = createRequire(import.meta.url);
const {chromium} = require(process.env.PLAYWRIGHT_CORE || 'playwright-core');
const [operation, url, email, selections = ''] = process.argv.slice(2);
const context = await chromium.launchPersistentContext(process.env.STAGING_BROWSER_PROFILE, {
  executablePath: process.env.CHROMIUM_PATH || undefined,
  headless: true,
});
const page = context.pages()[0] || await context.newPage();
try {
  await page.goto(url, {waitUntil: 'domcontentloaded'});
  if (operation === 'confirm') {
    await page.waitForTimeout(1500);
    console.log('confirmation_link_opened');
  } else {
    if (operation === 'signup') {
      const frame = await (async () => {
        for (let attempt = 0; attempt < 30; attempt++) {
          for (const candidate of page.frames()) {
            if (await candidate.locator('input[type="email"]').count()) return candidate;
          }
          await page.waitForTimeout(200);
        }
        throw new Error('Ghost Portal email input was not found');
      })();
      const labels = selections.split(',').filter(Boolean);
      await frame.locator('input[type="email"]').first().fill(email);
      for (const name of labels) {
        const choice = frame.getByLabel(name, {exact: false});
        if (await choice.count() !== 1) throw new Error(`Newsletter choice not unique: ${name}`);
        await choice.check();
      }
      const submit = frame.getByRole('button', {name: /sign up|subscribe|suscribir|continuar|continue/i});
      if (await submit.count() !== 1) throw new Error('Ghost Portal signup button was not unique');
      await submit.click();
      console.log('signup_submitted');
    } else if (operation === 'unsubscribe') {
      await page.waitForTimeout(1500);
      const account = page.frames().find(candidate => candidate.url().includes('portal')) || page.mainFrame();
      for (const name of selections.split(',').filter(Boolean)) {
        const choice = account.getByLabel(name, {exact: false});
        if (await choice.count() !== 1) throw new Error(`Preference control not unique: ${name}`);
        await choice.uncheck();
      }
      const save = account.getByRole('button', {name: /save|guardar|update|actualizar/i});
      if (await save.count() === 1) await save.click();
      console.log('unsubscribe_submitted');
    } else throw new Error('unknown probe operation');
  }
} finally {
  await context.close();
}
