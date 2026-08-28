/* Headless smoke test for the built static site.
 * Verifies every page loads clean and that the ported interactions work. */
const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

const SITE = path.join(__dirname, '..', 'docs');
const url = (f) => 'file://' + path.join(SITE, f);

const fail = [];
const note = (page, msg) => fail.push(`${page}: ${msg}`);

(async () => {
  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
  });
  const pages = fs.readdirSync(SITE).filter((f) => f.endsWith('.html')).sort();

  for (const file of pages) {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const p = await ctx.newPage();
    p.setDefaultTimeout(5000);
    const errors = [];
    p.on('pageerror', (e) => errors.push('JS error: ' + e.message));
    p.on('console', (m) => {
      // ERR_FAILED is this test aborting the external font/map requests
      if (m.type() === 'error' && !/ERR_FAILED/.test(m.text())) errors.push('console: ' + m.text());
    });
    p.on('requestfailed', (r) => {
      const u = r.url();
      if (u.startsWith('file://')) errors.push('missing file: ' + u.replace('file://' + SITE, ''));
    });
    // keep the run hermetic: no Google Fonts / maps fetches from the sandbox
    await p.route('**/*', (route) =>
      route.request().url().startsWith('file://') ? route.continue() : route.abort()
    );

    await p.goto(url(file), { waitUntil: 'domcontentloaded' });
    await p.waitForLoadState('networkidle').catch(() => {});
    await p.waitForTimeout(400);
    try {

    // images that resolved but decoded to nothing
    // the lightbox <img> has no src until it opens — not a broken image
    const broken = await p.$$eval('img:not(#lightbox-img)', (imgs) =>
      imgs.filter((i) => !i.complete || i.naturalWidth === 0).map((i) => i.getAttribute('src'))
    );
    broken.forEach((b) => note(file, 'broken image ' + b));

    // header + footer present on every page
    const chrome = await p.evaluate(() => ({
      header: !!document.querySelector('header'),
      footer: !!document.querySelector('footer'),
      hero: !!document.getElementById('home'),
      hposts: document.querySelectorAll('.nav-dropdown a').length
    }));
    if (!chrome.header) note(file, 'no <header>');
    if (!chrome.footer) note(file, 'no <footer>');
    if (chrome.hposts < 4) note(file, 'nav dropdown links missing');

    // sticky bar reveals after scrolling past the hero
    if (chrome.hero) {
      const before = await p.$eval('#sticky-bar', (e) => e.style.transform);
      await p.evaluate(() => window.scrollTo(0, document.body.scrollHeight / 2));
      await p.waitForTimeout(250);
      const after = await p.$eval('#sticky-bar', (e) => e.style.transform);
      if (!/translateY\(-100%\)/.test(before) || !/translateY\(0(px)?\)/.test(after)) {
        note(file, `sticky bar did not reveal (before=${before} after=${after})`);
      }
      await p.evaluate(() => window.scrollTo(0, 0));
      await p.waitForTimeout(150);
    }

    // mobile nav toggles
    await p.setViewportSize({ width: 800, height: 900 });
    await p.waitForTimeout(150);
    const panel = '.dc-if[data-cond="mobileNavOpen"]';
    const shown = () =>
      p.$eval('#mobile-nav-panel', (e) => getComputedStyle(e).display !== 'none');
    if (await p.$(panel)) {
      // generated page: visibility is the [hidden] attribute on the wrapper
      if (await p.$eval(panel, (e) => !e.hidden)) note(file, 'mobile nav open before click');
      await p.click('#nav-hamburger');
      if (await p.$eval(panel, (e) => e.hidden)) note(file, 'hamburger did not open nav');
      await p.click('#nav-hamburger');
      if (await p.$eval(panel, (e) => !e.hidden)) note(file, 'hamburger did not close nav');
    } else if (await p.$('#mobile-nav-panel')) {
      // hand-authored page: its own script toggles display directly
      if (await shown()) note(file, 'mobile nav open before click');
      await p.click('#nav-hamburger');
      if (!(await shown())) note(file, 'hamburger did not open nav');
      await p.click('#nav-hamburger');
      if (await shown()) note(file, 'hamburger did not close nav');
    } else {
      note(file, 'no mobile nav panel');
    }
    await p.setViewportSize({ width: 1440, height: 900 });

    // testimonial / gallery slide carousels
    for (const [group, label] of [['t', 'testimonial'], ['g', 'gallery']]) {
      const dots = await p.$$(`.dc-dot[data-dot-group="${group}"]`);
      if (!dots.length) continue;
      const cond = group === 't' ? 'isT' : 'isG';
      const visible = () =>
        p.evaluate((c) => {
          const el = [...document.querySelectorAll('.dc-if')].filter((e) => e.dataset.cond.startsWith(c) && !e.hidden);
          return el.length ? el[0].dataset.cond : null;
        }, cond);
      if ((await visible()) !== cond + '0') note(file, `${label} does not start on slide 0`);
      await dots[2].click();
      if ((await visible()) !== cond + '2') note(file, `${label} dot 2 did not activate`);
      const activeDot = await p.$$eval(`.dc-dot[data-dot-group="${group}"].is-active`, (e) => e.length);
      if (activeDot !== 1) note(file, `${label} active dot count = ${activeDot}`);
      await dots[0].click();
    }

    // arrow gallery scrolls
    const track = await p.$('[id$="-track"]');
    if (track) {
      const prefix = await track.evaluate((e) => e.id.replace(/-track$/, ''));
      const next = await p.$(`[data-dc-click="${prefix}Next"]`);
      if (!next) note(file, `gallery ${prefix} has no next button`);
      else {
        const before = await track.evaluate((e) => e.scrollLeft);
        await next.click();
        await p.waitForTimeout(700);
        const after = await track.evaluate((e) => e.scrollLeft);
        if (after === before) note(file, `gallery ${prefix} did not scroll (${before} -> ${after})`);
      }
    }

    // price-list lightbox
    if (await p.$('[data-dc-click="openLightbox1"]')) {
      const box = '.dc-if[data-cond="lightboxSrc"]';
      await p.click('[data-dc-click="openLightbox1"]');
      if (await p.$eval(box, (e) => e.hidden)) note(file, 'lightbox did not open');
      const src = await p.$eval('#lightbox-img', (e) => e.getAttribute('src'));
      if (!src) note(file, 'lightbox image has no src');
      await p.keyboard.press('Escape');
      await p.waitForTimeout(100);
      if (await p.$eval(box, (e) => !e.hidden)) note(file, 'lightbox did not close on Escape');
    }

    // hand-authored quote form: submitting swaps the form for the success card
    if (await p.$('#quote-form')) {
      await p.fill('#quote-form input[name="name"]', 'Test');
      await p.fill('#quote-form input[name="email"]', 'test@example.com');
      await p.evaluate(() => document.getElementById('quote-form').requestSubmit());
      await p.waitForTimeout(200);
      const state = await p.evaluate(() => ({
        form: getComputedStyle(document.getElementById('quote-form')).display,
        ok: getComputedStyle(document.getElementById('quote-success')).display
      }));
      if (state.form !== 'none') note(file, 'form still visible after submit');
      if (state.ok === 'none') note(file, 'success card not shown after submit');
    }

    // quote form submitted state
    if (await p.$('form[data-dc-submit]')) {
      await p.fill('form[data-dc-submit] input[type="text"]', 'Test');
      const email = await p.$('form[data-dc-submit] input[type="email"]');
      if (email) await email.fill('test@example.com');
      await p.evaluate(() => document.querySelector('form[data-dc-submit]').requestSubmit());
      await p.waitForTimeout(200);
      if (await p.$eval('.dc-if[data-cond="submitted"]', (e) => e.hidden)) {
        note(file, 'form did not show submitted state');
      }
    }

    // image-slot geometry applied
    const slots = await p.$$eval('.img-slot-img', (imgs) =>
      imgs.map((i) => ({ w: i.style.width, fit: i.style.objectFit }))
    );
    slots.forEach((s, i) => {
      if (!s.w || s.fit !== 'fill') note(file, `image slot ${i} not laid out`);
    });

    } catch (err) {
      note(file, 'check threw: ' + err.message.split('\n')[0]);
    }

    errors.forEach((e) => note(file, e));
    await ctx.close();
    process.stdout.write('checked ' + file + '\n');
  }

  await browser.close();

  if (fail.length) {
    console.log('FAILURES (' + fail.length + '):');
    fail.forEach((f) => console.log('  ' + f));
    process.exit(1);
  }
  console.log('All ' + fs.readdirSync(SITE).filter((f) => f.endsWith('.html')).length + ' pages passed.');
})();
