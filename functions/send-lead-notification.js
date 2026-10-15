/**
 * Cloudflare Pages Function: POST /send-lead-notification
 *
 * Emails each form submission to Las Vegas Pack and Ship through Resend.
 * The browser fires this in addition to any webhook a form already uses.
 *
 * RESEND_API_KEY is a Pages secret (production and preview). It is not stored
 * in the repo. For `wrangler pages dev`, put it in `.dev.vars` (gitignored).
 */

const FROM = 'Las Vegas Pack and Ship <leads@newleadrelay.com>';
const TO = [
  'maryjanemurphy@lasvegascrating.com',
  'tyler@lasvegascrating.com',
  'chrislong@lasvegascrating.com',
];

const MAX_FIELDS = 30;
const MAX_LEN = 2000;

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Max-Age': '86400',
};

const LABELS = {
  name: 'Name',
  email: 'Email',
  phone: 'Phone',
  message: 'Message',
  item: 'What Needs to Ship',
  subject: 'Subject',
  form: 'Form',
  page: 'Page',
  source: 'Form',
};

const FIRST = ['name', 'email', 'phone', 'message'];

const json = (body, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS, 'Content-Type': 'application/json' },
  });

const label = (key) =>
  LABELS[key] ?? key.replace(/[_-]+/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

const esc = (s) =>
  s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

const isEmail = (s) => /^[^@\s<>"]+@[^@\s<>"]+\.[^@\s<>"]+$/.test(s);

function buildHtml(fields) {
  const name = fields.name || '';
  const email = fields.email || '';
  const phone = fields.phone || '';
  const telHref = phone.replace(/[^\d+]/g, '');
  const link =
    'color:#0C0B09;font-size:20px;font-weight:700;text-decoration:underline;display:inline-block;padding:12px 4px;line-height:1.35;';

  const contact = [
    `<div style="font-size:24px;line-height:1.3;margin:0 0 10px;"><strong style="color:#0C0B09;">${esc(name)}</strong></div>`,
    email && isEmail(email)
      ? `<div><a href="mailto:${esc(email)}" style="${link}">${esc(email)}</a></div>`
      : email
        ? `<div style="${link}">${esc(email)}</div>`
        : '',
    phone
      ? `<div><a href="tel:${esc(telHref || phone)}" style="${link}">${esc(phone)}</a></div>`
      : '',
  ].join('');

  const keys = [...FIRST, ...Object.keys(fields).filter((k) => !FIRST.includes(k))].filter((k) => fields[k]);
  const rows = keys
    .map(
      (k, i) => `<tr style="background:${i % 2 ? '#ffffff' : '#f7f4ee'};">
        <td style="padding:12px 14px;font-weight:700;color:#0C0B09;vertical-align:top;white-space:nowrap;border-bottom:1px solid #e8e4da;">${esc(label(k))}</td>
        <td style="padding:12px 14px;color:#111;vertical-align:top;border-bottom:1px solid #e8e4da;white-space:pre-wrap;word-break:break-word;">${esc(fields[k])}</td>
      </tr>`,
    )
    .join('');

  return `<!doctype html><html><body style="margin:0;padding:0;background:#f3efe6;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:600px;margin:0 auto;padding:16px;">
    <div style="background:#ffffff;border:3px solid #D6A441;border-radius:12px;padding:22px 22px 16px;margin:0 0 20px;">
      <div style="font-size:14px;font-weight:800;letter-spacing:0.12em;color:#8a6418;margin:0 0 14px;">CONTACT THIS LEAD</div>
      ${contact}
    </div>
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse;background:#ffffff;border-radius:12px;overflow:hidden;font-size:16px;line-height:1.45;">
      ${rows}
    </table>
  </div>
</body></html>`;
}

export const onRequestOptions = () => new Response(null, { status: 204, headers: CORS });

export const onRequestPost = async ({ request, env }) => {
  if (!env.RESEND_API_KEY) {
    console.error('[send-lead-notification] RESEND_API_KEY is not set');
    return json({ ok: false, error: 'Email is not configured' }, 500);
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ ok: false, error: 'Invalid JSON' }, 400);
  }
  if (!body || typeof body !== 'object' || Array.isArray(body)) {
    return json({ ok: false, error: 'Expected a JSON object' }, 400);
  }

  const fields = {};
  for (const [k, v] of Object.entries(body).slice(0, MAX_FIELDS)) {
    if (v === null || v === undefined || typeof v === 'object') continue;
    fields[k.slice(0, 60)] = String(v).trim().slice(0, MAX_LEN);
  }

  // Honeypot: bots fill a hidden "company" field. Accept and drop.
  if (fields.company) return json({ ok: true });
  delete fields.company;

  fields.name ??= '';
  fields.email ??= '';
  fields.phone ??= '';
  fields.message ??= '';
  if (!fields.name) return json({ ok: false, error: 'Name is required' }, 400);
  if (!fields.email && !fields.phone) return json({ ok: false, error: 'Email or phone is required' }, 400);

  const email = {
    from: FROM,
    to: TO,
    subject: `New Lead - ${fields.name.replace(/[\r\n]+/g, ' ').slice(0, 200)}`,
    html: buildHtml(fields),
  };
  if (isEmail(fields.email)) email.reply_to = fields.email;

  try {
    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${env.RESEND_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(email),
    });
    const out = await res.json().catch(() => ({}));
    if (!res.ok) {
      console.error('[send-lead-notification] Resend error', res.status, out);
      return json({ ok: false, error: out.message ?? `Resend returned ${res.status}` }, 502);
    }
    return json({ ok: true, id: out.id });
  } catch (err) {
    console.error('[send-lead-notification] Resend request failed', err);
    return json({ ok: false, error: 'Could not reach the email service' }, 502);
  }
};
