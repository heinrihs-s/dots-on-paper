/**
 * Generate compact README animations from native bridge-rendered snapshots.
 * Run after `node dots-demo/serve.mjs` from the workspace root:
 *   node dots-demo/tools/export-github.mjs
 * Optional env: DOTS_DEMO_URL, DOTS_BROWSER, DOTS_NODE_MODULES, DOTS_PYTHON.
 * The 16-second GIFs think, show a reply, and stop on the final result.
 * No account, calendar or messaging connector is called.
 */
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve, relative, isAbsolute } from 'node:path';
import { homedir } from 'node:os';
import { existsSync } from 'node:fs';
import { mkdir, mkdtemp, readFile, writeFile, rm } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { spawn } from 'node:child_process';
import { nativePerformance, nativeFrameAt, nativeProvenance } from './native-film.mjs';

const demoRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const packageRoot = existsSync(resolve(demoRoot, '..', 'plugin.json')) ? resolve(demoRoot, '..') : resolve(demoRoot, '..', 'dots-plugin');
const campaignDir = join(packageRoot, 'campaign');
const mediaDir = join(campaignDir, 'media');
const exportsDir = join(demoRoot, 'exports');
const manifestPath = join(campaignDir, 'media-manifest.json');
const bundle = join(homedir(), '.cache', 'codex-runtimes', 'codex-primary-runtime', 'dependencies');
const baseUrl = process.env.DOTS_DEMO_URL || 'http://127.0.0.1:9024';
const checkoutPython = join(packageRoot, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const python = process.env.DOTS_PYTHON || (existsSync(checkoutPython) ? checkoutPython : existsSync(join(bundle, 'python', 'python.exe')) ? join(bundle, 'python', 'python.exe') : 'python');
const dimensions = { width: 960, height: 720 };
const framesPerSecond = 12;
const frameCount = 192;
const performances = [
  { stem: 'dot-reminders', example: 'calendar-chaos', start: 0, hold: true, poster: 'dot-reminders.png' },
  { stem: 'dot-noo', example: 'wife-noo', start: 0, hold: true, poster: 'dot-noo.png' },
  ...['artist', 'curious', 'bookish', 'cool'].map(dot => {
    const suffix = dot === 'artist' ? '' : `-${dot}`;
    return { stem: `dots-on-paper${suffix}`, example: '', dot, start: 0, hold: true, poster: `poster${suffix}.png`, exports: true };
  }),
];
const sourceFiles = [
  join(demoRoot, 'demo.js'),
  ...['beret-dot', 'curious-dot', 'bookish-dot', 'cool-dot'].flatMap(stem => [join(demoRoot, 'assets', `${stem}.png`), join(demoRoot, 'assets', `${stem}.prompt.md`)]),
  join(demoRoot, 'assets', 'Figtree.ttf'),
  join(demoRoot, 'tools', 'native-film.mjs'),
  join(demoRoot, 'tools', 'render-film-frames.py'),
  join(packageRoot, 'src', 'dots_on_paper', 'render.py'),
];
const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');

async function playwright() {
  try { return await import('playwright'); } catch (original) {
    const modules = process.env.DOTS_NODE_MODULES || join(bundle, 'node', 'node_modules');
    if (!existsSync(join(modules, 'playwright', 'package.json'))) {
      throw new Error(`Install Playwright or set DOTS_NODE_MODULES. ${original.message}`);
    }
    return createRequire(join(modules, 'package.json'))('playwright');
  }
}

function browserPath() {
  if (process.env.DOTS_BROWSER) return process.env.DOTS_BROWSER;
  if (process.platform !== 'win32') return undefined;
  return [process.env['ProgramFiles(x86)'] || 'C:/Program Files (x86)', process.env.ProgramFiles || 'C:/Program Files']
    .map(path => join(path, 'Microsoft', 'Edge', 'Application', 'msedge.exe')).find(path => existsSync(path));
}

async function encode(args) {
  return new Promise((resolvePromise, reject) => {
    const process = spawn(python, [join(demoRoot, 'tools', 'make_campaign_gif.py'), ...args], { windowsHide: true });
    let output = '', errorOutput = '';
    process.stdout.on('data', chunk => { output += chunk.toString(); });
    process.stderr.on('data', chunk => { errorOutput += chunk.toString(); });
    process.on('error', reject);
    process.on('close', code => {
      if (code !== 0) { reject(new Error(`GIF encoder exited ${code}: ${errorOutput}`)); return; }
      try { resolvePromise(JSON.parse(output)); } catch (error) { reject(new Error(`GIF encoder returned invalid metadata: ${output}. ${error.message}`)); }
    });
  });
}

await mkdir(mediaDir, { recursive: true });
const sources = [];
for (const path of sourceFiles) sources.push({ path: relative(packageRoot, path).replaceAll('\\', '/'), sha256: sha256(await readFile(path)) });
const { chromium } = await playwright();
const browser = await chromium.launch({ executablePath: browserPath(), headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1120 }, deviceScaleFactor: 1 });
const errors = [];
page.on('pageerror', error => errors.push(error.message));
page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
const manifest = existsSync(manifestPath) ? JSON.parse(await readFile(manifestPath, 'utf8')) : {
  schema_version: 1, project: 'Dots on Paper',
  content_type: 'staged-concept-demo', external_message_sent: false, assets: [],
};
manifest.source_files = sources;
manifest.regeneration = {
  campaign: 'node demo/tools/export-campaign.mjs',
  github_gifs: 'node demo/tools/export-github.mjs',
  verification: 'python tools/finalize_campaign.py',
};
function upsertAsset(item) {
  const existing = manifest.assets.find(asset => asset.path === item.path);
  if (existing) Object.assign(existing, item);
  else manifest.assets.push(item);
}

try {
  await page.goto(baseUrl, { waitUntil: 'networkidle' });
  await page.evaluate(async () => { await window.dotDemo.ready; await window.dotDemo.allDotsReady; window.dotDemo.pause(); });
  for (const performance of performances) {
    const native = await nativePerformance(page, { dot: performance.dot || 'cool', example: performance.example });
    const outputDir = performance.exports ? exportsDir : mediaDir;
    const framesDir = await mkdtemp(join(mediaDir, '.github-gif-frames-'));
    const destination = join(outputDir, `${performance.stem}.gif`);
    const metadataPath = join(framesDir, 'provenance.json');
    const sourceVideo = await readFile(join(outputDir, `${performance.stem}.mp4`));
    const sourceVideoMetadata = JSON.parse(await readFile(join(outputDir, `${performance.stem}.provenance.json`), 'utf8'));
    if (!sourceVideo.includes(Buffer.from('avc1')) || sha256(sourceVideo) !== sourceVideoMetadata.sha256) throw new Error('Source H.264 film does not match its recorded provenance.');
    if (sourceVideoMetadata.native?.rendererSha256 !== native.rendererSha256 || sourceVideoMetadata.native?.resultFrameSha256 !== nativeProvenance(native).resultFrameSha256) throw new Error('Re-export the MP4: its native renderer/result does not match this checkout.');
    const provenance = {
      ...sourceVideoMetadata,
      source: native.source, native: nativeProvenance(native),
      asset: { ...sourceVideoMetadata.asset, path: sourceVideoMetadata.asset.path.replace('dots-demo/', 'demo/') },
      sourceFiles: sources,
      reproduction: 'node demo/tools/export-github.mjs',
      format: 'GIF', fictional: true,
      width: dimensions.width, height: dimensions.height,
      framesPerSecond, sourceFrames: frameCount,
      loopStartSourceSeconds: 0, loop: null, endsOnRetainedResult: true,
      timeline: 'Forward-only native snapshots: thinking, then a settled reply retained after playback ends. No GIF loop extension.',
      sourceFilm: { name: `${performance.stem}.mp4`, sha256: sha256(sourceVideo) },
    };
    delete provenance.bytes;
    delete provenance.sha256;
    delete provenance.codec;
    delete provenance.duration;
    try {
      console.log(`Rendering ${performance.stem}: ${frameCount} deterministic frames at ${dimensions.width}×${dimensions.height}.`);
      for (let index = 0; index < frameCount; index++) {
        const data = await page.evaluate(async args => {
          await window.dotDemo.renderNativeAt(args.index / 12, {
            format: 'scene', mode: 'ink', dot: args.dot || 'cool', example: args.example,
            hold: args.hold, export: true,
          }, args.uri);
          const scaled = document.createElement('canvas');
          scaled.width = args.width;
          scaled.height = args.height;
          const context = scaled.getContext('2d', { alpha: false });
          context.drawImage(window.dotDemo.canvas, 0, 0, args.width, args.height);
          return scaled.toDataURL('image/png').split(',')[1];
        }, { ...performance, index, ...dimensions, uri: nativeFrameAt(native, index / 12).uri });
        await writeFile(join(framesDir, `frame-${String(index).padStart(4, '0')}.png`), Buffer.from(data, 'base64'));
      }
      await writeFile(metadataPath, JSON.stringify(provenance));
      const encoded = await encode([framesDir, destination, metadataPath]);
      if (encoded.bytes > 6_000_000) throw new Error(`${destination} exceeds the 6 MB README budget (${encoded.bytes} bytes).`);
      const gifProvenance = { ...provenance, ...encoded, sha256: sha256(await readFile(destination)) };
      await writeFile(join(outputDir, `${performance.stem}.gif.provenance.json`), JSON.stringify(gifProvenance, null, 2) + '\n');
      if (performance.stem === 'dots-on-paper') await writeFile(join(outputDir, 'dots-on-paper.gif.json'), JSON.stringify(gifProvenance, null, 2) + '\n');
      if (!performance.exports) upsertAsset({
        id: `${performance.stem === 'dot-reminders' ? 'reminders' : 'noo'}-gif`,
        path: `media/${performance.stem}.gif`, kind: 'animation', status: 'verified',
        width: encoded.width, height: encoded.height, bytes: encoded.bytes,
        encoded_frames: encoded.encodedFrames, distinct_frames: encoded.distinctFrames,
        duration_seconds: encoded.durationSeconds, loop: encoded.loop, embedded_provenance: true,
        ends_on_retained_result: true, result_hold_seconds: native.duration - native.resultStartsAt,
        sha256: gifProvenance.sha256, source_film: provenance.sourceFilm,
        loop_start_source_seconds: performance.start, poster: `media/${performance.poster}`,
        provenance: `media/${performance.stem}.gif.provenance.json`,
      });
      if (!performance.exports) upsertAsset({
        id: `${performance.stem === 'dot-reminders' ? 'reminders' : 'noo'}-film`,
        path: `media/${performance.stem}.mp4`, kind: 'video', status: 'verified',
        width: sourceVideoMetadata.width, height: sourceVideoMetadata.height,
        duration_seconds: sourceVideoMetadata.duration, bytes: sourceVideo.length, codec: 'H.264 / avc1',
        sha256: sha256(sourceVideo), provenance: `media/${performance.stem}.provenance.json`,
        ends_on_retained_result: true, result_hold_seconds: native.duration - native.resultStartsAt,
      });
      console.log('GIF verified:', { file: destination, ...encoded });
    } finally {
      const resolvedFrames = resolve(framesDir);
      const insideMedia = relative(resolve(mediaDir), resolvedFrames);
      if (!insideMedia || isAbsolute(insideMedia) || insideMedia.startsWith('..') || dirname(resolvedFrames) !== resolve(mediaDir) || !insideMedia.startsWith('.github-gif-frames-')) {
        throw new Error(`Refusing to remove an intermediate directory outside campaign/media: ${resolvedFrames}`);
      }
      await rm(resolvedFrames, { recursive: true, force: true });
    }
  }
  if (errors.length) throw new Error(`Browser errors: ${errors.join(' | ')}`);
  await writeFile(manifestPath, JSON.stringify(manifest, null, 2) + '\n');
  console.log('GIF export complete. All six stop on their result. No browser errors or live connectors used.');
} finally {
  await browser.close();
}
