const { resolve } = require('path');

/**
 * @type {import("puppeteer").Configuration}
 */
module.exports = {
  cacheDirectory: resolve(__dirname, '..', '..', 'frontend', '.cache', 'puppeteer'),
};
