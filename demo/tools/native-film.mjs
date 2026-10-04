/** Offline e-paper snapshots and their authored, forward-only film timeline. */
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { existsSync } from 'node:fs';
import { homedir } from 'node:os';
import { spawn } from 'node:child_process';

const packageRoot = dirname(dirname(dirname(fileURLToPath(import.meta.url))));
const checkoutPython = join(packageRoot, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const bundledPython = join(homedir(), '.cache', 'codex-runtimes', 'codex-primary-runtime', 'dependencies', 'python', 'python.exe');
const python = process.env.DOTS_PYTHON || (existsSync(checkoutPython) ? checkoutPython : existsSync(bundledPython) ? bundledPython : 'python');

export const filmDuration = 16;
export const filmFrameSeconds = .5;

export async function nativePerformance(page, opts) {
  const content = await page.evaluate(example => {
    window.dotDemo.setExample(example);
    return { reply: window.dotDemo.state.reply, conversation: window.dotDemo.state.conversation };
  }, opts.example);
  if (opts.reply) content.reply = opts.reply;
  if (!content.reply && !content.conversation) content.reply = { sender: 'heidot', text: 'Good ideas deserve a little paper.' };
  const base = { character: opts.dot || 'cool', dot_name: content.reply?.sender || content.conversation?.sender || 'heidot', title: '' };
  const frames = Array.from({ length: 12 }, (_, frame) => ({ id: `thinking-${frame}`, frame, state: { ...base, status: 'thinking', text: '' } }));
  let segments;
  if (content.reply) {
    frames.push({ id: 'result', frame: 11, state: { ...base, status: 'answer', title: 'Reply', text: content.reply.text } });
    segments = [{ start: 0, end: 6, thinking: true }, { start: 6, end: filmDuration, id: 'result' }];
  } else if (content.conversation) {
    const [draft, reaction, cancelled] = content.conversation.messages;
    const draftText = `${draft.text}\n\n${draft.status}`;
    const reactionText = `${draftText}\n\nYou: ${reaction.text}`;
    frames.push(
      { id: 'draft', frame: 11, state: { ...base, status: 'answer', title: 'Draft ready', text: draftText } },
      { id: 'interruption', frame: 11, state: { ...base, status: 'answer', title: 'Interrupted', text: reactionText } },
      { id: 'result', frame: 11, state: { ...base, status: 'answer', title: 'Conversation', text: `${reactionText}\n\n${cancelled.text}` } },
    );
    segments = [
      { start: 0, end: 3, thinking: true }, { start: 3, end: 7, id: 'draft' },
      { start: 7, end: 9, id: 'interruption' }, { start: 9, end: filmDuration, id: 'result' },
    ];
  } else throw new Error(`No staged reply or conversation for ${opts.example}.`);
  const rendered = await new Promise((resolve, reject) => {
    const child = spawn(python, [join(packageRoot, 'demo', 'tools', 'render-film-frames.py')], { windowsHide: true });
    let output = '', errors = '';
    child.stdout.on('data', chunk => { output += chunk.toString(); });
    child.stderr.on('data', chunk => { errors += chunk.toString(); });
    child.on('error', reject);
    child.on('close', code => {
      if (code !== 0) { reject(new Error(`Native film renderer exited ${code}: ${errors}`)); return; }
      try { resolve(JSON.parse(output)); } catch (error) { reject(new Error(`Native film renderer returned invalid JSON: ${error.message}`)); }
    });
    child.stdin.end(JSON.stringify({ frames }));
  });
  return {
    ...rendered, segments, duration: filmDuration, frameSeconds: filmFrameSeconds,
    resultStartsAt: segments.at(-1).start,
    cadence: 'Accelerated preview: one native snapshot every 0.5 seconds while thinking. Actual refresh is controlled by the display client and hardware.',
  };
}

export function nativeFrameAt(performance, seconds) {
  const time = Math.min(Math.max(0, seconds), performance.duration);
  const segment = performance.segments.find(item => time < item.end) || performance.segments.at(-1);
  const id = segment.thinking ? `thinking-${Math.floor(time / performance.frameSeconds) % 12}` : segment.id;
  return performance.frames.find(frame => frame.id === id);
}

export function nativeProvenance(performance) {
  return {
    source: performance.source, rendererSha256: performance.rendererSha256,
    nativeWidth: performance.width, nativeHeight: performance.height, nativeLevels: performance.levels,
    snapshotIntervalSeconds: performance.frameSeconds, cadence: performance.cadence,
    timeline: performance.segments, resultStartsAt: performance.resultStartsAt,
    resultHoldSeconds: performance.duration - performance.resultStartsAt,
    resultFrameSha256: nativeFrameAt(performance, performance.duration).sha256,
    frames: performance.frames.map(({ uri, ...metadata }) => metadata),
  };
}
