import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { mkdir } from 'node:fs/promises';
const require = createRequire(import.meta.url);
let playwright;
try { playwright = require('playwright'); }
catch { playwright = require(join(process.env.USERPROFILE, '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright')); }
const root = dirname(dirname(fileURLToPath(import.meta.url)));
const credentials = process.env.DOTS_CONFIG_FILE || join(root, 'data', 'credentials.json');
const review = join(root, 'tests', 'artifacts');
await mkdir(review, {recursive:true});
const browser = await playwright.chromium.launch({channel:'chrome',headless:true});
const page = await browser.newPage({viewport:{width:1440,height:1100}});
const errors=[];
page.on('pageerror', e=>errors.push(e.message));
await page.goto(process.env.DOTS_VERIFY_URL || 'http://127.0.0.1:9035');
await page.locator('#credentials').setInputFiles(credentials);
await page.waitForFunction(()=>document.querySelector('#status').classList.contains('connected'));
await page.waitForFunction(()=>document.querySelector('#screen').naturalWidth===1872);
for(const character of ['artist','curious','bookish','cool']) {
  await page.locator(`[data-dot="${character}"]`).click();
  await page.waitForFunction(id=>document.querySelector(`[data-dot="${id}"]`).getAttribute('aria-pressed')==='true'&&document.querySelector('#screen').dataset.character===id,character);
}
await page.screenshot({path:join(review,'bridge-desktop.png'),fullPage:true});
await page.locator('#profile').selectOption('oep_296');
await page.waitForFunction(()=>document.querySelector('#screen').naturalWidth===296);
await page.setViewportSize({width:390,height:844});
await page.locator('#profile').selectOption('trmnl_x');
await page.waitForFunction(()=>document.querySelector('#screen').naturalWidth===1872);
await page.screenshot({path:join(review,'bridge-mobile.png'),fullPage:true});
assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'Mobile overflow');
await page.locator('[data-dot="artist"]').click();
await page.waitForFunction(()=>document.querySelector('[data-dot="artist"]').getAttribute('aria-pressed')==='true'&&document.querySelector('#screen').dataset.character==='artist');
assert.equal(errors.length,0,'Browser errors occurred');
assert.equal(await page.locator('#token').inputValue(),'','Token field should clear');
await browser.close();
console.log('Bridge preview passed: credential connection, four character switches, profile resize, mobile overflow and browser errors.');
