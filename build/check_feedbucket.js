/* Verifies the Feedbucket widget loads on the staging host and nowhere else.
 * Serves docs/ from disk under a fake https origin per hostname and watches
 * for the request to the Feedbucket CDN. */
const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

const SITE = path.join(__dirname, '..', 'docs');
const TYPES = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript',
  '.png': 'image/png', '.webp': 'image/webp', '.ico': 'image/x-icon',
  '.svg': 'image/svg+xml', '.webmanifest': 'application/manifest+json' };

// hostname -> should the widget load?
const CASES = [
  ['las-vegas-pack-and-ship.pages.dev', true],
  ['lasvegaspackandship.com', false],
  ['www.lasvegaspackandship.com', false],
  ['eee41df3.las-vegas-pack-and-ship.pages.dev', false],
  ['localhost', false]
];

(async () => {
  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
  });

  let failures = 0;
  for (const [host, expected] of CASES) {
    const ctx = await browser.newContext();
    await ctx.route('**/*', (route) => {
      const u = new URL(route.request().url());
      if (u.hostname === 'cdn.feedbucket.app') return route.fulfill({ status: 200, body: '' });
      if (u.hostname !== host) return route.abort();
      const file = path.join(SITE, decodeURIComponent(u.pathname) === '/' ? '/index.html' : decodeURIComponent(u.pathname));
      if (!file.startsWith(SITE) || !fs.existsSync(file)) return route.fulfill({ status: 404, body: '' });
      return route.fulfill({
        status: 200,
        contentType: TYPES[path.extname(file)] || 'application/octet-stream',
        body: fs.readFileSync(file)
      });
    });

    const p = await ctx.newPage();
    let loaded = false;
    p.on('request', (r) => { if (r.url().includes('cdn.feedbucket.app')) loaded = true; });
    await p.goto(`https://${host}/index.html`, { waitUntil: 'domcontentloaded' });
    await p.waitForTimeout(600);

    const ok = loaded === expected;
    if (!ok) failures++;
    console.log(
      `${ok ? 'PASS' : 'FAIL'}  ${host.padEnd(45)} widget ${loaded ? 'loaded' : 'did not load'}` +
      ` (expected ${expected ? 'loaded' : 'not loaded'})`
    );
    await ctx.close();
  }

  await browser.close();
  process.exit(failures ? 1 : 0);
})();
