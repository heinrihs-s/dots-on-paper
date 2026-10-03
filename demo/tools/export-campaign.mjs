/**
 * Rebuild the scripted campaign from the actual local demo renderer.
 *
 * Start `node dots-demo/serve.mjs`, then run this script. Playwright may be
 * installed normally or found through DOTS_NODE_MODULES (the desktop bundled
 * runtime is a fallback). DOTS_BROWSER selects an H.264-capable browser;
 * installed Microsoft Edge is preferred on Windows. DOTS_DEMO_URL overrides
 * http://127.0.0.1:9024. Use --skip-video for just stills, or --only=noo,
 * --only=reminders, --only=instinct, or --only=cast to select one export group.
 *
 * PNG provenance records the scripted content and exact source-asset prompt.
 * Films are real 16-second 1600×1200 H.264 MP4s recorded at a requested 24 fps.
 * No account, messaging API, calendar, or Instinct connector is used.
 */
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';
import { homedir } from 'node:os';
import { existsSync } from 'node:fs';
import { mkdir, readFile, writeFile, stat } from 'node:fs/promises';
import { createHash } from 'node:crypto';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const packageRoot = existsSync(resolve(root, '..', 'plugin.json')) ? resolve(root, '..') : resolve(root, '..', 'dots-plugin');
const mediaDir = join(packageRoot, 'campaign', 'media');
const exportsDir = join(root, 'exports');
const baseUrl = process.env.DOTS_DEMO_URL || 'http://127.0.0.1:9024';
const allowedGroups = ['reminders', 'noo', 'instinct', 'cast'];
const allowedDots = ['artist', 'curious', 'bookish', 'cool'];
const assetNames = { artist: 'beret-dot', curious: 'curious-dot', bookish: 'bookish-dot', cool: 'cool-dot' };
const args = process.argv.slice(2);
const skipVideo = args.includes('--skip-video');
const onlyArgs = args.filter(arg => arg.startsWith('--only='));
if (args.includes('--help')) {
  console.log('node dots-demo/tools/export-campaign.mjs [--skip-video] [--only=reminders|noo|instinct|cast]');
  console.log('Optional environment: DOTS_DEMO_URL, DOTS_BROWSER, DOTS_NODE_MODULES.');
  process.exit(0);
}
if (onlyArgs.length > 1 || args.some(arg => arg !== '--skip-video' && !arg.startsWith('--only='))) {
  throw new Error('Use --skip-video and at most one --only=reminders|noo|instinct|cast option.');
}
const only = onlyArgs[0]?.slice('--only='.length);
if (only && !allowedGroups.includes(only)) throw new Error(`Unknown export group: ${only}.`);
const includes = group => !only || only === group;

async function loadPlaywright() {
  try { return await import('playwright'); } catch (error) {
    const bundled = join(homedir(), '.cache', 'codex-runtimes', 'codex-primary-runtime', 'dependencies', 'node', 'node_modules');
    const modules = process.env.DOTS_NODE_MODULES || bundled;
    if (!existsSync(join(modules, 'playwright', 'package.json'))) {
      throw new Error(`Install Playwright or set DOTS_NODE_MODULES to its node_modules directory. ${error.message}`);
    }
    return createRequire(join(modules, 'package.json'))('playwright');
  }
}

function browserExecutable() {
  if (process.env.DOTS_BROWSER) return process.env.DOTS_BROWSER;
  if (process.platform === 'win32') {
    const candidates = [
      join(process.env['ProgramFiles(x86)'] || 'C:/Program Files (x86)', 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
      join(process.env.ProgramFiles || 'C:/Program Files', 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
    ];
    return candidates.find(candidate => existsSync(candidate));
  }
  return undefined;
}

function crc32(bytes) {
  let crc = 0xffffffff;
  for (const byte of bytes) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit++) crc = (crc >>> 1) ^ ((crc & 1) ? 0xedb88320 : 0);
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function addPngProvenance(bytes, metadata) {
  if (bytes.subarray(0, 8).toString('hex') !== '89504e470d0a1a0a') throw new Error('Canvas output is not PNG.');
  let position = 8;
  let endPosition;
  while (position + 12 <= bytes.length) {
    const length = bytes.readUInt32BE(position);
    const type = bytes.subarray(position + 4, position + 8).toString('ascii');
    if (type === 'IEND') { endPosition = position; break; }
    position += 12 + length;
  }
  if (endPosition === undefined) throw new Error('PNG is missing its final IEND chunk.');
  const type = Buffer.from('iTXt');
  const data = Buffer.concat([
    Buffer.from('dots:provenance\0', 'ascii'),
    // Uncompressed UTF-8 text; empty language and translated keyword.
    Buffer.from([0, 0, 0, 0]),
    Buffer.from(JSON.stringify(metadata), 'utf8'),
  ]);
  const chunk = Buffer.alloc(data.length + 12);
  chunk.writeUInt32BE(data.length, 0);
  type.copy(chunk, 4);
  data.copy(chunk, 8);
  chunk.writeUInt32BE(crc32(Buffer.concat([type, data])), data.length + 8);
  return Buffer.concat([bytes.subarray(0, endPosition), chunk, bytes.subarray(endPosition)]);
}

async function provenance(dot, label, opts) {
  const stem = assetNames[dot];
  const asset = await readFile(join(root, 'assets', `${stem}.png`));
  const prompt = await readFile(join(root, 'assets', `${stem}.prompt.md`), 'utf8');
  return {
    title: label,
    fictional: true,
    output: 'Scripted demo output; no calendar or message was accessed or sent.',
    connector: opts.reply?.sender === 'Instinct' ? 'Instinct-inspired concept; no Instinct connector.' : 'No live dot connector used for this export.',
    source: 'dots-demo/demo.js canvas renderer',
    example: opts.example,
    scriptedReply: opts.reply || undefined,
    character: dot,
    asset: { path: `dots-demo/assets/${stem}.png`, sha256: createHash('sha256').update(asset).digest('hex'), generator: 'OpenAI image generation', prompt },
    font: { name: 'Figtree', license: 'SIL Open Font License 1.1' },
    reproduction: 'node dots-demo/tools/export-campaign.mjs',
  };
}

await mkdir(mediaDir, { recursive: true });
await mkdir(exportsDir, { recursive: true });
const { chromium } = await loadPlaywright();
const browser = await chromium.launch({
  executablePath: browserExecutable(), headless: true,
  args: ['--disable-background-timer-throttling', '--disable-backgrounding-occluded-windows', '--disable-renderer-backgrounding'],
});
const context = await browser.newContext({ viewport: { width: 1440, height: 1120 }, deviceScaleFactor: 1 });
const page = await context.newPage();
const errors = [];
page.on('pageerror', error => errors.push(error.message));
page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });

async function render(seconds, opts) {
  return page.evaluate(async args => {
    await window.dotDemo.renderAt(args.seconds, { ...args.opts, mode: 'smooth', export: true });
    return { width: window.dotDemo.canvas.width, height: window.dotDemo.canvas.height };
  }, { seconds, opts });
}

async function savePng(path, seconds, opts, label) {
  const size = await render(seconds, opts);
  const expected = opts.format === 'screen' ? { width: 1872, height: 1404 } : { width: 1600, height: 1200 };
  if (size.width !== expected.width || size.height !== expected.height) throw new Error(`Wrong dimensions for ${path}: ${JSON.stringify(size)}`);
  const base64 = await page.evaluate(() => window.dotDemo.canvas.toDataURL('image/png').split(',')[1]);
  const metadata = { ...await provenance(opts.dot, label, opts), frameSeconds: seconds, ...size };
  await writeFile(path, addPngProvenance(Buffer.from(base64, 'base64'), metadata));
  console.log('PNG:', { path, ...size, bytes: (await stat(path)).size });
}

async function saveFilm(path, opts, label) {
  console.log(`Recording ${label}: 16 seconds, 1600×1200, H.264, requested 24 fps.`);
  const result = await page.evaluate(async options => {
    const demo = window.dotDemo;
    demo.pause();
    const renderOptions = { ...options, format: 'scene', mode: 'smooth', export: true };
    await demo.renderAt(0, renderOptions);
    await new Promise(resolve => setTimeout(resolve, 300));
    const stream = demo.canvas.captureStream(24);
    const codec = 'video/mp4;codecs=avc1';
    if (!MediaRecorder.isTypeSupported(codec)) throw new Error('This browser cannot record H.264 MP4. Set DOTS_BROWSER to Microsoft Edge or another H.264-capable browser.');
    const recorder = new MediaRecorder(stream, { mimeType: codec, videoBitsPerSecond: 12000000 });
    const chunks = [];
    recorder.ondataavailable = event => { if (event.data.size) chunks.push(event.data); };
    const stopped = new Promise((resolve, reject) => {
      recorder.onstop = resolve;
      recorder.onerror = event => reject(event.error || new Error('MediaRecorder failed.'));
    });
    recorder.start(1000);
    const started = performance.now();
    let lastFrame = -1;
    try {
      await new Promise((resolve, reject) => {
        const tick = async now => {
          try {
            const elapsed = (now - started) / 1000;
            if (elapsed >= 16) { resolve(); return; }
            const frame = Math.floor(elapsed * 24);
            if (frame !== lastFrame) {
              lastFrame = frame;
              await demo.renderAt(frame / 24, renderOptions);
            }
            requestAnimationFrame(tick);
          } catch (error) { reject(error); }
        };
        requestAnimationFrame(tick);
      });
      recorder.stop();
      await stopped;
    } finally {
      if (recorder.state !== 'inactive') recorder.stop();
      stream.getTracks().forEach(track => track.stop());
    }
    const blob = new Blob(chunks, { type: recorder.mimeType });
    if (blob.size < 10000) throw new Error(`The recording is unexpectedly small: ${blob.size} bytes.`);
    const video = document.createElement('video');
    video.muted = true;
    const url = URL.createObjectURL(blob);
    video.src = url;
    const metadata = await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error('Recorded video metadata did not load.')), 15000);
      video.onloadedmetadata = () => { clearTimeout(timeout); resolve({ width: video.videoWidth, height: video.videoHeight, duration: video.duration }); };
      video.onerror = () => { clearTimeout(timeout); reject(new Error('The browser could not decode the recorded MP4.')); };
      video.load();
    });
    URL.revokeObjectURL(url);
    const dataUrl = await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
    return { base64: dataUrl.split(',')[1], bytes: blob.size, mime: recorder.mimeType, metadata };
  }, opts);
  const bytes = Buffer.from(result.base64, 'base64');
  if (!bytes.includes(Buffer.from('avc1'))) throw new Error('MP4 has no H.264 avc1 sample entry.');
  if (result.metadata.width !== 1600 || result.metadata.height !== 1200 || !Number.isFinite(result.metadata.duration) || Math.abs(result.metadata.duration - 16) > .5) {
    throw new Error(`Unexpected film metadata: ${JSON.stringify(result.metadata)}`);
  }
  await writeFile(path, bytes);
  const metadata = {
    ...await provenance(opts.dot, label, opts),
    ...result.metadata, codec: 'H.264 / avc1', requestedFramesPerSecond: 24,
    bytes: result.bytes, sha256: createHash('sha256').update(bytes).digest('hex'),
  };
  await writeFile(path.replace(/\.mp4$/, '.provenance.json'), JSON.stringify(metadata, null, 2) + '\n');
  console.log('MP4 verified:', { path, bytes: result.bytes, codec: 'H.264 / avc1', ...result.metadata });
}

try {
  await page.goto(baseUrl, { waitUntil: 'networkidle' });
  await page.waitForFunction(() => Boolean(window.dotDemo));
  await page.evaluate(async () => {
    await window.dotDemo.ready;
    await window.dotDemo.allDotsReady;
    window.dotDemo.pause();
  });
  const calendar = { dot: 'cool', example: 'calendar-chaos', hold: true };
  const noo = { dot: 'cool', example: 'wife-noo' };
  if (includes('reminders')) {
    await savePng(join(mediaDir, 'dot-reminders.png'), 9, { ...calendar, format: 'scene' }, 'Calendar reminders — scripted reply');
    await savePng(join(mediaDir, 'dot-reminders-native.png'), 9, { ...calendar, format: 'screen' }, 'Calendar reminders — native scripted reply');
    if (!skipVideo) await saveFilm(join(mediaDir, 'dot-reminders.mp4'), calendar, 'Calendar reminders — scripted reply');
  }
  if (includes('noo')) {
    await savePng(join(mediaDir, 'dot-noo.png'), 12, { ...noo, format: 'scene' }, 'NOO — fictional conversation, nothing sent');
    await savePng(join(mediaDir, 'dot-noo-native.png'), 12, { ...noo, format: 'screen' }, 'NOO — native fictional conversation, nothing sent');
    if (!skipVideo) await saveFilm(join(mediaDir, 'dot-noo.mp4'), noo, 'NOO — fictional conversation, nothing sent');
  }
  if (includes('cast')) {
    for (const dot of allowedDots) {
      await savePng(join(exportsDir, `wife-noo-poster-${dot}.png`), 12, { ...noo, dot, format: 'scene' }, `NOO — ${dot} fictional conversation`);
      await savePng(join(exportsDir, `wife-noo-screen-1872x1404-${dot}.png`), 12, { ...noo, dot, format: 'screen' }, `NOO — ${dot} native fictional conversation`);
    }
  }
  if (includes('instinct')) {
    const concept = {
      dot: 'cool', example: '', hold: true,
      reply: { sender: 'Instinct', text: 'You’ve got a date with Paula tonight, breakfast with Amy tomorrow, and lunch with your wife.\n\nI’d suggest a calendar review. And possibly legal counsel.' },
      notice: 'INSTINCT-INSPIRED CONCEPT · SCRIPTED OUTPUT',
      studioNotice: 'INSTINCT-INSPIRED CONCEPT / NO CONNECTOR',
    };
    await savePng(join(mediaDir, 'instinct-on-paper.png'), 9, { ...concept, format: 'scene' }, 'Instinct-inspired concept — scripted output, no connector');
    await savePng(join(mediaDir, 'instinct-on-paper-native.png'), 9, { ...concept, format: 'screen' }, 'Instinct-inspired native concept — scripted output, no connector');
  }
  if (errors.length) throw new Error(`Browser errors: ${errors.join(' | ')}`);
  console.log('Campaign exports complete. No page errors. All content is fictional/scripted.');
} finally {
  await browser.close();
}
