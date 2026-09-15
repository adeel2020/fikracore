import assert from 'node:assert/strict';
import puppeteer from 'puppeteer';

const base = process.env.MARK_TEST_URL || 'http://localhost:3000';
const presentation = {
  narrative: { incident_id: 'test-incident', title: 'Voice service degradation', audience: 'noc', lifecycle_state: 'open', claims: [{ id: 'impact', statement: 'Voice setup success declined.', grade: 'confirmed_fact', confidence: 0.9, fcaps: ['fault', 'performance'] }] },
  visual_explanation: { primary_widget: 'domain_impact_map', widgets: [
    { id: 'impact', type: 'domain_impact_map', title: 'Service impact', confidence: 0.9, supports_claim_ids: ['impact'], provenance: [{ source: 'synthetic test', slug: 'evidence/test' }], data: { nodes: [{ id: 'ims', label: 'IMS', kind: 'domain' }, { id: 'voice', label: 'Voice', kind: 'service' }], links: [{ source: 'ims', target: 'voice', relationship: 'impacts' }] } },
    { id: 'timeline', type: 'timeline', title: 'Timeline', data: { events: [{ timestamp: '2026-09-05T10:00:00Z', text: 'Voice setup degraded' }] } },
  ] },
};
const browser = await puppeteer.launch({ headless: true, args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'] });
try {
  const page = await browser.newPage();
  await page.setViewport({ width: 1600, height: 1000 });
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text());
  });
  const intercepted = [];
  await page.evaluateOnNewDocument(() => {
    localStorage.setItem('sidebar_collapsed', 'true');
    window.speechSynthesis.speak = (utterance) => { window.testUtterance = utterance; };
    const RealWebSocket = window.WebSocket;
    class FakeSocket {
      static OPEN = 1;
      readyState = 1;
      constructor(url) {
        if (!String(url).includes('/ws/jarvis-voice/')) {
          return new RealWebSocket(url);
        }
        window.testVoiceSocket = this;
        setTimeout(() => this.onopen?.({}), 20);
      }
      send() {}
      close() { this.readyState = 3; }
    }
    FakeSocket.CONNECTING = RealWebSocket.CONNECTING;
    FakeSocket.OPEN = RealWebSocket.OPEN;
    FakeSocket.CLOSING = RealWebSocket.CLOSING;
    FakeSocket.CLOSED = RealWebSocket.CLOSED;
    window.WebSocket = FakeSocket;
  });
  await page.setRequestInterception(true);
  page.on('request', (request) => {
    if (request.url().includes('/api/jarvis/process')) {
      intercepted.push(`${request.method()} ${request.url()}`);
      if (request.method() === 'OPTIONS') {
        return request.respond({
          status: 204,
          headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
          },
        });
      }
      const general = JSON.parse(request.postData()).message === 'hello';
      return request.respond({
        status: 200,
        contentType: 'application/json',
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify({
          reply: general ? 'Hello.' : '# Voice service degradation\n\nVoice setup success declined.',
          spoken_reply: general ? 'Hello.' : 'Voice service is degraded.',
          ...(general ? {} : presentation),
        }),
      });
    }
    return request.continue();
  });
  await page.goto(`${base}/jarvis`, { waitUntil: 'networkidle2' });
  await page.waitForSelector('input[placeholder^="Ask MARK"]');
  await page.type('input[placeholder^="Ask MARK"]', 'Tell the incident story');
  await page.$eval('[data-testid="mark-command-form"]', (form) => form.requestSubmit());
  try {
    await page.waitForSelector('[data-testid="story-visual"][data-speaking="true"]');
  } catch (error) {
    await page.screenshot({ path: '/tmp/mark-presentation-failure.png' });
    console.error('Intercepted requests:', intercepted);
    console.error('Rendered body:', (await page.evaluate(() => document.body.textContent)).slice(0, 2000));
    throw error;
  }
  await page.waitForFunction(() => !!window.testUtterance);
  assert.equal(await page.evaluate(() => window.testUtterance.text), 'Voice service is degraded.');
  await page.evaluate(() => window.testUtterance.onend?.());
  await page.waitForSelector('[data-testid="story-visual"][data-speaking="false"]');
  await page.click('[title="Replay Voice Audio"]');
  await page.waitForSelector('[data-testid="story-visual"][data-speaking="true"]');
  await page.click('[aria-label="Open investigation workspace"]');
  await page.waitForSelector('dialog[open]');
  assert.ok((await page.$eval('dialog', (el) => el.textContent)).includes('evidence/test'));
  await page.screenshot({ path: '/tmp/mark-investigation-desktop.png' });
  await page.keyboard.press('Escape');
  assert.equal(await page.$('dialog[open]'), null);
  await page.click('[title="Start Hands-Free Realtime Voice Conversation"]');
  await page.waitForFunction(() => !!window.testVoiceSocket?.onmessage);
  await page.evaluate((payload) => {
    window.testVoiceSocket.onmessage({ data: JSON.stringify({ type: 'response', generation_id: 2, answer: 'Live voice answer', spoken_answer: 'Live brief.', ...payload }) });
    window.testVoiceSocket.onmessage({ data: JSON.stringify({ type: 'state', state: 'speaking' }) });
  }, presentation);
  await page.waitForSelector('[data-testid="story-visual"][data-speaking="true"]');
  await page.evaluate(() => window.testVoiceSocket.onmessage({ data: JSON.stringify({ type: 'interrupted', generation_id: 2 }) }));
  await page.waitForSelector('[data-testid="story-visual"][data-speaking="false"]');
  await page.evaluate(() => window.testVoiceSocket.onmessage({ data: JSON.stringify({ type: 'response', generation_id: 1, answer: 'Stale answer' }) }));
  assert.equal(await page.evaluate(() => document.body.textContent.includes('Stale answer')), false);
  await page.click('[title="Turn off Live Voice Mode"]');
  await page.setViewport({ width: 390, height: 844 });
  await page.click('[aria-label="Open investigation workspace"]');
  await page.screenshot({ path: '/tmp/mark-investigation-mobile.png' });
  assert.ok(await page.$eval('dialog', (el) => el.getBoundingClientRect().width <= innerWidth));
  await page.keyboard.press('Escape');
  await page.$eval('input[placeholder^="Ask MARK"]', (el) => el.focus());
  await page.type('input[placeholder^="Ask MARK"]', 'hello');
  await page.$eval('[data-testid="mark-command-form"]', (form) => form.requestSubmit());
  await page.waitForFunction(() => !document.querySelector('[data-testid="story-visual"]'));
  assert.deepEqual(errors, []);
  console.log('PASS: HTTP visuals, replay, live payload, interruption, stale response, investigation, mobile dialog, general-chat reset.');
} finally {
  await browser.close();
}
