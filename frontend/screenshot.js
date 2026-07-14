const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

async function run() {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  
  // Set larger viewport to see the UI
  await page.setViewport({ width: 1440, height: 900 });
  
  // Go to the narrative notebook view
  await page.goto('http://localhost:3000/narrative-notebook', { waitUntil: 'networkidle2', timeout: 30000 });
  
  // Wait a few extra seconds for the 3D model to download and render
  await new Promise(r => setTimeout(r, 8000));
  
  // Take screenshot
  const screenshotPath = path.join('/Users/adeelarshad/.gemini/antigravity/brain/20173f5a-a1c5-4b06-a470-8ab4b1e0852f/scratch', 'avatar_render.png');
  await page.screenshot({ path: screenshotPath, fullPage: true });
  console.log(`Screenshot saved to ${screenshotPath}`);
  
  await browser.close();
}

run().catch(console.error);
