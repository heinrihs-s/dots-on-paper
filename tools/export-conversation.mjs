/** Record the structured native conversation as a 16-second H.264 film.
 * First run tools/export_conversation.py and start node demo/serve.mjs.
 * DOTS_DEMO_URL, DOTS_BROWSER and DOTS_NODE_MODULES can override local tooling.
 */
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { homedir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { existsSync } from 'node:fs';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const native = JSON.parse(await readFile(join(root, '.impeccable', 'conversation-frames.json'), 'utf8'));
const modules = process.env.DOTS_NODE_MODULES || join(homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
let playwright;
try { playwright = await import('playwright'); }
catch { playwright = createRequire(join(modules, 'package.json'))('playwright'); }
const executablePath = process.env.DOTS_BROWSER || (process.platform === 'win32' ? [
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
].find(existsSync) : undefined);
const output = join(root, 'campaign', 'media', 'dot-conversation.mp4');
function provenancePng(bytes, metadata) {
  const type = Buffer.from('iTXt');
  const data = Buffer.concat([Buffer.from('dots:provenance\0'), Buffer.from([0, 0, 0, 0]), Buffer.from(JSON.stringify(metadata))]);
  const chunk = Buffer.alloc(data.length + 12);
  chunk.writeUInt32BE(data.length); type.copy(chunk, 4); data.copy(chunk, 8);
  let crc = 0xffffffff;
  for (const byte of Buffer.concat([type, data])) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit++) crc = (crc >>> 1) ^ ((crc & 1) ? 0xedb88320 : 0);
  }
  chunk.writeUInt32BE((crc ^ 0xffffffff) >>> 0, data.length + 8);
  // The canvas produces a standard PNG, whose final chunk is its IEND.
  return Buffer.concat([bytes.subarray(0, bytes.length - 12), chunk, bytes.subarray(bytes.length - 12)]);
}
const browser = await playwright.chromium.launch({ executablePath, headless: true, args: ['--disable-background-timer-throttling', '--disable-renderer-backgrounding'] });
try {
  const page = await browser.newPage({ viewport: { width: 1600, height: 1200 } });
  await page.goto(process.env.DOTS_DEMO_URL || 'http://127.0.0.1:9024', { waitUntil: 'networkidle' });
  await page.waitForFunction(() => Boolean(window.dotDemo));
  await page.evaluate(async () => { await window.dotDemo.ready; await window.dotDemo.allDotsReady; window.dotDemo.pause(); });
  const recorded = await page.evaluate(async native => {
    const demo = window.dotDemo;
    const options = { dot: native.character, format: 'scene', mode: 'ink', export: true };
    const frameAt = seconds => {
      const segment = native.segments.find(item => seconds < item.end) || native.segments.at(-1);
      const id = segment.thinking ? `thinking-${Math.floor(seconds / native.frameSeconds) % 12}` : segment.id;
      return native.frames.find(frame => frame.id === id);
    };
    for (const frame of native.frames) await demo.renderNativeAt(0, options, frame.uri);
    await demo.renderNativeAt(0, options, frameAt(0).uri);
    const stream = demo.canvas.captureStream(24);
    const mimeType = 'video/mp4;codecs=avc1';
    if (!MediaRecorder.isTypeSupported(mimeType)) throw new Error('Select an H.264-capable browser with DOTS_BROWSER.');
    const recorder = new MediaRecorder(stream, { mimeType, videoBitsPerSecond: 12000000 });
    const chunks = [];
    recorder.ondataavailable = event => { if (event.data.size) chunks.push(event.data); };
    const stopped = new Promise((resolve, reject) => { recorder.onstop = resolve; recorder.onerror = event => reject(event.error); });
    recorder.start(1000);
    try {
      const started = performance.now();
      await new Promise((resolve, reject) => {
        const tick = async now => {
          try {
            const seconds = Math.max(0, (now - started) / 1000);
            if (seconds >= native.duration) { resolve(); return; }
            await demo.renderNativeAt(seconds, options, frameAt(seconds).uri);
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
    const blob = new Blob(chunks, { type: mimeType });
    const video = document.createElement('video');
    video.muted = true;
    video.src = URL.createObjectURL(blob);
    await new Promise((resolve, reject) => {
      video.onloadedmetadata = resolve;
      video.onerror = () => reject(new Error('Recorded MP4 cannot be decoded.'));
      video.load();
    });
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth; canvas.height = video.videoHeight;
    const context = canvas.getContext('2d');
    async function pixels(seconds) {
      await new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error('Film seek timed out.')), 15000);
        video.onseeked = () => { clearTimeout(timer); resolve(); };
        video.currentTime = seconds;
      });
      context.drawImage(video, 0, 0);
      return context.getImageData(0, 0, canvas.width, canvas.height).data;
    }
    const result = await pixels(10);
    const final = await pixels(video.duration - .1);
    const delta = (one, two) => one.reduce((sum, value, index) => sum + Math.abs(value - two[index]), 0) / one.length;
    await demo.renderNativeAt(16, options, frameAt(16).uri);
    const expected = demo.canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data;
    const stability = delta(result, final);
    const accuracy = delta(final, expected);
    if (stability > 1 || accuracy > 3) throw new Error(`Final frame verification failed: ${stability}, ${accuracy}`);
    const metadata = { width: video.videoWidth, height: video.videoHeight, duration: video.duration, stability, accuracy };
    URL.revokeObjectURL(video.src);
    const base64 = await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result.split(',')[1]); reader.onerror = reject; reader.readAsDataURL(blob);
    });
    return { base64, metadata, poster: demo.canvas.toDataURL('image/png').split(',')[1] };
  }, native);
  const bytes = Buffer.from(recorded.base64, 'base64');
  if (!bytes.includes(Buffer.from('avc1')) || Math.abs(recorded.metadata.duration - 16) > .5) throw new Error('Unexpected MP4 container or duration.');
  await mkdir(dirname(output), { recursive: true });
  await writeFile(output, bytes);
  await writeFile(output.replace('.mp4', '.png'), provenancePng(Buffer.from(recorded.poster, 'base64'), {
    fictional: true, source: native.source, demonstration: native.demonstration,
    rendererSha256: native.rendererSha256, frame: native.frames.at(-1).state,
  }));
  await writeFile(output.replace('.mp4', '.provenance.json'), JSON.stringify({
    ...recorded.metadata, codec: 'H.264 / avc1', source: native.source,
    rendererSha256: native.rendererSha256, demonstration: native.demonstration,
    nativeWidth: native.width, nativeHeight: native.height, levels: native.levels,
    snapshotIntervalSeconds: native.frameSeconds, timeline: native.segments,
    endsOnRetainedResult: true, resultHoldSeconds: 7,
    native: {
      source: native.source, rendererSha256: native.rendererSha256,
      nativeWidth: native.width, nativeHeight: native.height, nativeLevels: native.levels,
      snapshotIntervalSeconds: native.frameSeconds, timeline: native.segments,
      resultStartsAt: native.resultStartsAt, resultHoldSeconds: 7,
      resultFrameSha256: native.frames.at(-1).sha256,
    },
    resultFrameBrowserDecode: {
      stableMeanPixelDifference: recorded.metadata.stability,
      expectedResultMeanPixelDifference: recorded.metadata.accuracy,
    },
    sha256: createHash('sha256').update(bytes).digest('hex'),
    frames: native.frames.map(({ uri, ...frame }) => frame),
    reproduction: 'python tools/export_conversation.py; node demo/serve.mjs; node tools/export-conversation.mjs',
  }, null, 2) + '\n');
  console.log('Conversation MP4 verified:', { output, bytes: bytes.length, ...recorded.metadata });
} finally { await browser.close(); }
