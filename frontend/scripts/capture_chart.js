const puppeteer = require('puppeteer');
const path = require('path');

async function capture() {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    console.error('Usage: node capture_chart.js <elementId> <outputPath> [port]');
    process.exit(1);
  }

  const elementId = args[0];
  const outputPath = path.resolve(args[1]);
  const port = args[2] || '3000';
  const url = `http://localhost:${port}/complaint-dashboard/print`;

  console.log(`Launching Puppeteer to capture #${elementId} from ${url}...`);

  let browser;
  try {
    browser = await puppeteer.launch({
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    
    // Set a standard desktop viewport
    await page.setViewport({ width: 1280, height: 1020 });

    // Navigate and wait for DOMContentLoaded to ensure scripts start executing
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });

    //Puppeteer can generate very high-resolution screenshots,
    await page.setViewport({
      width: 1920,
      height: 1080,
      deviceScaleFactor: 3,
    });

    // Wait for the specific element card to appear
    const selector = `#${elementId}`;
    console.log(`Waiting for selector ${selector}...`);
    await page.waitForSelector(selector, { timeout: 10000 });

    // Give charts 1 second to render fully (Recharts animations are disabled, but standard rendering needs a tick)
    await page.evaluate(() => new Promise(resolve => setTimeout(resolve, 1000)));

    const element = await page.$(selector);
    if (!element) {
      throw new Error(`Element #${elementId} not found on the page`);
    }

    console.log(`Taking screenshot of #${elementId} and saving to ${outputPath}...`);
    await element.screenshot({
      path: outputPath,
      type: 'png'
    });

    console.log('Capture completed successfully.');
  } catch (error) {
    console.error('Error during capture:', error);
    process.exit(2);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

capture();
