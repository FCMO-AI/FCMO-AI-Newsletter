// Browser proof for actual post-template email and the real generated signup.
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const preview = path.resolve(process.argv[2] || 'reports/email-preview');
const candidate = process.argv[3] && path.resolve(process.argv[3]);
const files = fs.readdirSync(preview).filter(f => /^\d{4}-\d{2}-\d{2}-(en|es-419|zh-Hans)\.html$/.test(f));
const server = http.createServer((req, res) => {
  let name = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  let root;
  if (name.startsWith('/preview/')) { root = preview; name = name.slice(9); }
  else if (candidate && name.startsWith('/FCMO-AI-Newsletter/')) { root = candidate; name = name.slice(20); }
  else { res.writeHead(404); return res.end(); }
  if (name.endsWith('/')) name += 'index.html';
  const target = path.resolve(root, name);
  if (path.relative(root, target).startsWith('..')) { res.writeHead(403); return res.end(); }
  try {
    const ext = path.extname(target);
    res.setHeader('Content-Type', {'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.json':'application/json','.woff2':'font/woff2','.svg':'image/svg+xml','.png':'image/png','.webp':'image/webp'}[ext] || 'application/octet-stream');
    res.end(fs.readFileSync(target));
  } catch { res.writeHead(404); res.end(); }
});
(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch();
  const rows = [];
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.route('**/*', route => route.request().url().startsWith(origin) ? route.continue() : route.abort());
    for (const file of files) for (const width of [390, 1440]) {
      await page.setViewportSize({width, height:900});
      await page.goto(origin+'/preview/'+file);
      const result = await page.evaluate(() => ({
        width:document.documentElement.scrollWidth, viewport:innerWidth,
        lang:document.documentElement.lang,
        articles:document.querySelectorAll('article').length,
        unsubscribe:[...document.querySelectorAll('a')].some(a => a.href.includes('/subscription/preview/reader')),
        height:document.body.scrollHeight,
      }));
      if (result.width > width || result.articles !== 3 || !result.unsubscribe) throw Error(JSON.stringify({file,width,result}));
      await page.screenshot({path:path.join(preview,file.replace('.html',`-${width}.png`)),fullPage:true});
      rows.push({file,width,...result});
    }
    if (candidate) for (const [locale,prefix] of [['en',''],['es-419','es/'],['zh-Hans','zh/']]) for (const width of [390,1440]) {
      await page.setViewportSize({width,height:900});
      await page.goto(origin+'/FCMO-AI-Newsletter/'+prefix+'suscribete/');
      await page.evaluate(() => document.fonts.ready);
      const result = await page.evaluate(() => {
        const form = document.querySelector('form');
        const consent = form?.querySelector('[name=consent]');
        return {width:document.documentElement.scrollWidth, viewport:innerWidth,
          action:form?.action, method:form?.method, consentRequired:consent?.required,
          consentChecked:consent?.checked, locale:form?.querySelector('[name=locale]')?.value || form?.dataset.emailLocale,
          emailField:form?.querySelector('input[type=email]')?.name,
          privacy:!!document.querySelector('a[href*="/privacy/"]')};
      });
      const kit = process.env.FCMO_EMAIL_PROVIDER === 'kit';
      const expectedForm = kit ? `https://app.kit.com/forms/${process.env[{en:'KIT_FORM_EN','es-419':'KIT_FORM_ES','zh-Hans':'KIT_FORM_ZH'}[locale]]}/subscriptions` : null;
      if (kit && (result.action !== expectedForm || result.emailField !== 'email_address')) throw Error(JSON.stringify({locale,width,result}));
      if (result.width > width || result.method !== 'post' || !result.consentRequired || result.consentChecked || result.locale !== locale || !result.privacy) throw Error(JSON.stringify({locale,width,result}));
      await page.screenshot({path:path.join(preview,`signup-${locale}-${width}.png`),fullPage:true});
      rows.push({surface:'signup',locale,width,...result});
    }
    if (errors.length) throw Error(errors.join('\n'));
    fs.writeFileSync(path.join(preview,'browser-proof.json'),JSON.stringify({status:'PASS',rows,scriptErrors:errors},null,2)+'\n');
    console.log(`Preview and signup browser proof PASS (${rows.length} checks)`);
  } finally { await browser.close(); await new Promise(resolve => server.close(resolve)); }
})().catch(err => { console.error(err); server.close(); process.exitCode=1; });
