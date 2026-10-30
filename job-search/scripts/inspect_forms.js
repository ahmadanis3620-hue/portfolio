// READ-ONLY: loads each apply URL, records what the form asks. Never submits, never creates accounts.
const { chromium } = require('playwright');
const fs = require('fs');
const jobs = JSON.parse(fs.readFileSync('jds.json','utf8'));

(async () => {
  const browser = await chromium.launch({ args:['--no-sandbox'] });
  const out = [];
  for (const j of jobs) {
    const applyUrl = j.url.includes('/job/') ? j.url.replace(/\/apply.*$/,'') + '/apply' : j.url;
    const ctx = await browser.newContext({ userAgent:'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36' });
    const page = await ctx.newPage();
    const rec = { idx:j.idx, company:j.company, title:j.title, url:j.url, applyUrl, status:null, wall:null, fields:[], notes:[] };
    try {
      const resp = await page.goto(applyUrl, { waitUntil:'domcontentloaded', timeout:45000 });
      rec.status = resp ? resp.status() : null;
      await page.waitForTimeout(3500);
      const body = (await page.content()).toLowerCase();
      // detect the common gates
      if (/create account|sign in|signin|log in to apply|already have an account/.test(body)) rec.wall = 'account required';
      if (/captcha|recaptcha|hcaptcha|are you a robot|cloudflare/.test(body)) rec.wall = (rec.wall? rec.wall+' + ':'') + 'bot protection';
      if (/no longer (accepting|available)|position (has been )?(closed|filled)|requisition is closed/.test(body)) rec.wall = 'posting closed';
      rec.fields = await page.evaluate(() => {
        const vis = e => { const r=e.getBoundingClientRect(); const s=getComputedStyle(e);
          return r.width>0 && r.height>0 && s.visibility!=='hidden' && s.display!=='none'; };
        const label = e => {
          if (e.getAttribute('aria-label')) return e.getAttribute('aria-label');
          if (e.id) { const l=document.querySelector(`label[for="${CSS.escape(e.id)}"]`); if (l) return l.innerText; }
          const w=e.closest('label'); if (w) return w.innerText;
          return e.getAttribute('placeholder') || e.getAttribute('name') || '';
        };
        return [...document.querySelectorAll('input,select,textarea')]
          .filter(e => vis(e) && !['hidden','submit','button'].includes(e.type))
          .slice(0,60)
          .map(e => ({ tag:e.tagName.toLowerCase(), type:e.type||'', required: e.required || e.getAttribute('aria-required')==='true',
                       label:(label(e)||'').replace(/\s+/g,' ').trim().slice(0,90) }))
          .filter(f => f.label);
      });
    } catch (e) { rec.notes.push(String(e).split('\n')[0].slice(0,120)); }
    await ctx.close();
    out.push(rec);
    console.log(`${rec.idx} ${rec.company} | status=${rec.status} wall=${rec.wall||'-'} fields=${rec.fields.length}`);
  }
  await browser.close();
  fs.writeFileSync('formmap/forms.json', JSON.stringify(out,null,1));
})();
