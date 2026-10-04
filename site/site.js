(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const characters = ['artist', 'curious', 'bookish', 'cool'];
  const modes = ['last_reply', 'full_conversation'];
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const examples = {
    reminders: {
      text: 'Here are your reminders. Tonight: Date with Paula. Tomorrow morning: Breakfast with Amy. Lunch: With your wife. Your calendar needs a lawyer.',
      punchline: '“Your calendar needs a lawyer.”',
      labels: ['Your question', 'Dot’s reply'],
      turns: ['You: What do I have coming up?', 'You: What do I have coming up? heidot: Here are your reminders. Tonight: Date with Paula. Tomorrow morning: Breakfast with Amy. Lunch: With your wife. Your calendar needs a lawyer.'],
    },
    interruption: {
      text: 'Cancelled. Nothing sent.',
      punchline: '“Cancelled. Nothing sent.”',
      labels: ['The draft', 'Your reply', 'Dot’s reply'],
      turns: [
        'heidot: Okay, understood. Texting your wife about your date with Paula tonight. Draft ready, waiting for approval.',
        'heidot: Okay, understood. Texting your wife about your date with Paula tonight. Draft ready, waiting for approval. You: NOO.',
        'heidot: Okay, understood. Texting your wife about your date with Paula tonight. Draft ready, waiting for approval. You: NOO. heidot: Cancelled. Nothing sent.',
      ],
    },
  };
  let character = 'cool', example = 'reminders', mode = 'last_reply';
  let timer = null, generation = 0, playing = false, inView = false;
  const loaded = new Map();
  const frameUrl = (id, index) => `./assets/frames/${id}-thinking-${index}.png`;
  const resultUrl = (index = examples[example].turns.length) => mode === 'full_conversation'
    ? `./assets/frames/${character}-${example}-full_conversation-${index}.png`
    : `./assets/frames/${character}-${example}-last_reply.png`;
  function stop() { clearTimeout(timer); timer = null; playing = false; generation++; }
  function setScreen(url, alt) { $('screen').src = url; $('screen').alt = alt; }
  function resetReplay() {
    $('replay').disabled = false;
    $('skip-preview').hidden = true;
    $('replay').querySelector('span').textContent = mode === 'full_conversation' ? 'Replay conversation' : 'Replay thinking';
  }
  function setTurn(index) {
    const data = examples[example];
    if (index < 1 || index > data.turns.length) return;
    setScreen(resultUrl(index), data.turns[index - 1]);
    document.querySelectorAll('[data-turn]').forEach(button => button.setAttribute('aria-pressed', String(Number(button.dataset.turn) === index)));
    $('demo-status').textContent = index === data.turns.length ? 'Conversation retained' : data.labels[index - 1];
  }
  function showResult() {
    playing = false; timer = null;
    if (mode === 'full_conversation') setTurn(examples[example].turns.length);
    else {
      setScreen(resultUrl(), `heidot’s reply: ${examples[example].text}`);
      $('demo-status').textContent = 'Answer retained';
    }
    resetReplay();
  }
  function updateControls() {
    $('conversation-controls').hidden = mode !== 'full_conversation';
    $('mode-description').textContent = mode === 'full_conversation' ? 'Both sides, kept in view.' : 'One answer, kept on paper.';
    $('demo-punchline').textContent = examples[example].punchline;
    document.querySelectorAll('[data-turn]').forEach(button => {
      const label = examples[example].labels[Number(button.dataset.turn) - 1];
      button.hidden = !label;
      if (label) button.textContent = label;
    });
  }
  function loadFrames(id) {
    if (!loaded.has(id)) {
      const promise = Promise.all(Array.from({ length: 12 }, (_, index) => new Promise((resolve, reject) => {
        const image = new Image();
        image.onload = () => resolve(image);
        image.onerror = () => reject(new Error('Thinking frames could not load.'));
        image.src = frameUrl(id, index);
      }))).catch(error => { loaded.delete(id); throw error; });
      loaded.set(id, promise);
    }
    return loaded.get(id);
  }
  async function replay() {
    stop();
    if (reducedMotion.matches) { showResult(); return; }
    const token = generation;
    $('replay').disabled = true;
    $('skip-preview').hidden = false;
    $('replay').querySelector('span').textContent = 'Loading frames…';
    $('demo-status').textContent = 'Preparing the preview';
    try { await loadFrames(character); }
    catch {
      if (token !== generation) return;
      showResult();
      $('demo-status').textContent = 'Couldn’t load frames. Try replay again.';
      return;
    }
    if (token !== generation) return;
    if (reducedMotion.matches || document.hidden) { showResult(); return; }
    playing = true;
    $('replay').querySelector('span').textContent = 'Thinking…';
    $('demo-status').textContent = 'Thinking · accelerated preview';
    let frame = 0;
    const advance = index => {
      if (token !== generation) return;
      setTurn(index);
      if (index === examples[example].turns.length) { playing = false; timer = null; resetReplay(); return; }
      $('replay').querySelector('span').textContent = 'Conversation…';
      timer = setTimeout(() => advance(index + 1), example === 'interruption' && index === 1 ? 2200 : 1400);
    };
    const tick = () => {
      if (token !== generation) return;
      if (frame >= 12) {
        if (mode === 'full_conversation') advance(1);
        else showResult();
        return;
      }
      setScreen(frameUrl(character, frame++), `${character} companion thinking. Accelerated demonstration.`);
      timer = setTimeout(tick, 500);
    };
    tick();
  }
  function changed() {
    stop(); updateControls(); showResult();
    if (inView && !reducedMotion.matches && !document.hidden) replay();
  }
  $('replay').addEventListener('click', replay);
  $('skip-preview').addEventListener('click', () => { stop(); showResult(); });
  document.querySelectorAll('[data-turn]').forEach(button => button.addEventListener('click', () => {
    if (mode !== 'full_conversation') return;
    stop(); setTurn(Number(button.dataset.turn)); resetReplay();
  }));
  for (const [attribute, valid, set] of [
    ['character', characters, value => { character = value; }],
    ['mode', modes, value => { mode = value; }],
    ['example', Object.keys(examples), value => { example = value; }],
  ]) {
    document.querySelectorAll(`[data-${attribute}]`).forEach(button => button.addEventListener('click', () => {
      const value = button.dataset[attribute];
      if (!valid.includes(value) || button.getAttribute('aria-pressed') === 'true') return;
      set(value);
      document.querySelectorAll(`[data-${attribute}]`).forEach(choice => choice.setAttribute('aria-pressed', String(choice === button)));
      changed();
    }));
  }
  reducedMotion.addEventListener('change', () => { if (playing || timer || $('replay').disabled) { stop(); showResult(); } });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden && (playing || $('replay').disabled)) { stop(); showResult(); }
  });
  // Observe the screen, so mobile visitors can actually see the sequence.
  // Each entry plays once and settles; there is no background animation loop.
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      const visible = entries[0].isIntersecting && entries[0].intersectionRatio >= .2;
      if (visible === inView) return;
      inView = visible;
      if (visible && !document.hidden && !reducedMotion.matches) replay();
      else if (playing || $('replay').disabled) { stop(); showResult(); }
    }, { threshold: [0, .2], rootMargin: '0px 0px -5% 0px' });
    observer.observe($('demo-device'));
  }
  updateControls();

  document.querySelectorAll('[data-os]').forEach(button => button.addEventListener('click', () => {
    document.querySelectorAll('[data-os]').forEach(choice => choice.setAttribute('aria-pressed', String(choice === button)));
    $('launch-code').textContent = button.dataset.os === 'windows' ? '.\\run.ps1' : '.venv/bin/python -m dots_on_paper --data-dir ./data';
  }));
  const tabs = [...document.querySelectorAll('[role="tab"]')];
  function activateTab(tab, focus = false) {
    tabs.forEach(choice => {
      const selected = choice === tab;
      choice.setAttribute('aria-selected', String(selected));
      choice.tabIndex = selected ? 0 : -1;
      $(choice.getAttribute('aria-controls')).hidden = !selected;
    });
    if (focus) tab.focus();
  }
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => activateTab(tab));
    tab.addEventListener('keydown', event => {
      let next;
      if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      if (event.key === 'ArrowLeft') next = (index - 1 + tabs.length) % tabs.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = tabs.length - 1;
      if (next !== undefined) { event.preventDefault(); activateTab(tabs[next], true); }
    });
  });
  document.querySelectorAll('[data-copy]').forEach(button => {
    const original = button.innerHTML;
    let restoreTimer;
    button.addEventListener('click', async () => {
    const value = $(button.dataset.copy).textContent;
    try {
      if (!navigator.clipboard) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(value);
      clearTimeout(restoreTimer);
      button.textContent = 'Copied';
      $('copy-status').textContent = 'Command copied to clipboard.';
      restoreTimer = setTimeout(() => { button.innerHTML = original; }, 1800);
    } catch {
      const range = document.createRange();
      range.selectNodeContents($(button.dataset.copy));
      const selection = window.getSelection();
      selection.removeAllRanges(); selection.addRange(range);
      $('copy-status').textContent = 'Clipboard is unavailable. The command is selected; copy it manually.';
    }
    });
  });
})();
