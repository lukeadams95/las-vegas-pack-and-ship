/**
 * Exercises functions/send-lead-notification.js without calling Resend.
 * Run: node build/test-lead-notification.mjs
 */
import { onRequestOptions, onRequestPost } from '../functions/send-lead-notification.js';

const FROM = 'Las Vegas Pack and Ship <leads@newleadrelay.com>';
const TO = [
  'maryjanemurphy@lasvegascrating.com',
  'tyler@lasvegascrating.com',
  'chrislong@lasvegascrating.com',
];

let calls = [];
const realFetch = globalThis.fetch;
globalThis.fetch = async (url, opts) => {
  calls.push({ url, opts });
  return new Response(JSON.stringify({ id: 'email_123' }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
};

const fail = [];
const check = (cond, msg) => {
  if (!cond) fail.push(msg);
};

const post = (body, env = { RESEND_API_KEY: 're_test' }) =>
  onRequestPost({
    request: new Request('https://las-vegas-pack-and-ship.pages.dev/send-lead-notification', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Origin: 'https://las-vegas-pack-and-ship.pages.dev' },
      body: typeof body === 'string' ? body : JSON.stringify(body),
    }),
    env,
  });

const options = await onRequestOptions();
check(options.status === 204, 'OPTIONS status');
check(options.headers.get('Access-Control-Allow-Origin') === '*', 'OPTIONS CORS');

const ok = await post({
  name: 'Jane Smith',
  email: 'jane@email.com',
  phone: '(702) 555-0100',
  message: 'Need a crate\nfor a painting',
  item: 'Fine art',
  page: '/free-quote.html',
});
const okBody = await ok.json();
check(ok.status === 200 && okBody.ok === true && okBody.id === 'email_123', 'success JSON');
check(ok.headers.get('Access-Control-Allow-Origin') === '*', 'POST CORS');
check(calls.length === 1 && calls[0].url === 'https://api.resend.com/emails', 'Resend URL');

const sent = JSON.parse(calls[0].opts.body);
check(sent.from === FROM, 'from');
check(JSON.stringify(sent.to) === JSON.stringify(TO), 'to');
check(sent.reply_to === 'jane@email.com', 'reply_to');
check(sent.subject === 'New Lead - Jane Smith', 'subject');
check(sent.html.includes('CONTACT THIS LEAD'), 'contact heading');
check(sent.html.includes('<strong style="color:#0C0B09;">Jane Smith</strong>'), 'bold name');
check(sent.html.includes('href="mailto:jane@email.com"'), 'mailto');
check(sent.html.includes('href="tel:7025550100"'), 'tel');
check(sent.html.includes('font-size:20px'), 'tap-friendly link size');
check(sent.html.includes('>Name<') && sent.html.includes('Jane Smith'), 'name row');
check(sent.html.includes('What Needs to Ship') && sent.html.includes('Fine art'), 'extra field');
check(sent.html.includes('Need a crate\nfor a painting') || sent.html.includes('Need a crate'), 'message');
check(sent.html.indexOf('CONTACT THIS LEAD') < sent.html.indexOf('<table'), 'contact section above table');
check(!sent.html.includes('re_test'), 'key not in email');

calls = [];
const phoneOnly = await post({ name: 'Sam', phone: '702-555-0199' });
check((await phoneOnly.json()).ok === true, 'phone-only accepted');
const phoneSent = JSON.parse(calls[0].opts.body);
check(phoneSent.reply_to === undefined, 'no reply_to without email');
check(phoneSent.html.includes('href="tel:7025550199"'), 'phone-only tel');

calls = [];
const noName = await post({ email: 'jane@email.com' });
check(noName.status === 400 && calls.length === 0, 'name required');

const badJson = await post('{');
check(badJson.status === 400, 'invalid JSON');

const unconfigured = await post({ name: 'Jane', email: 'jane@email.com' }, {});
check(unconfigured.status === 500 && calls.length === 0, 'missing API key');

calls = [];
const nasty = await post({ name: 'A<b>\r\nX', email: 'a@b.co', message: '<script>alert(1)</script>' });
const nastySent = JSON.parse(calls[0].opts.body);
check(nastySent.subject === 'New Lead - A<b> X', 'subject strips newlines');
check(nastySent.html.includes('A&lt;b&gt;') && !nastySent.html.includes('<script>'), 'escapes html');
check(nastySent.reply_to === 'a@b.co', 'reply_to from lead email');

calls = [];
const bot = await post({ name: 'Bot', email: 'bot@spam.test', company: 'Acme' });
check((await bot.json()).ok === true && calls.length === 0, 'honeypot dropped');

globalThis.fetch = async () => {
  throw new Error('network down');
};
const down = await post({ name: 'Jane', email: 'jane@email.com' });
check(down.status === 502, 'resend unreachable');

globalThis.fetch = realFetch;

if (fail.length) {
  console.error('FAILURES (' + fail.length + '):');
  fail.forEach((f) => console.error('  ' + f));
  process.exit(1);
}
console.log('send-lead-notification: all checks passed');
