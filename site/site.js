(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const characters = ['artist', 'curious', 'bookish', 'cool'];
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const replies = {
    reminders: 'heidot’s reply: Here are your reminders. Tonight: Date with Paula. Tomorrow morning: Breakfast with Amy. Lunch: With your wife. Your calendar needs a lawyer.',
    noo: 'heidot: Okay, understood. Texting your wife about your date with Paula tonight. Draft ready, waiting for approval. You: NOO. Cancelled. Nothing sent.',
  };
  let character = 'cool', example = 'reminders', frame = 11;
  let timer = null, generation = 0, playing = false;
  const loaded = new Map();
  const frameUrl = (id, index) => `./assets/frames/${id}-thinking-${index}.png`;
  function stop() { clearTimeout(timer); timer = null; playing = false; generation++; }
  function setScreen(url, alt) { $('screen').src = url; $('screen').alt = alt; }
  function showResult() {
    playing = false;
    setScreen(`./assets/frames/${character}-${example}.png`, replies[example]);
    $('demo-status').textContent = 'Answer retained';
    $('replay').disabled = false;
    $('replay').querySelector('span').textContent = 'Replay thinking';
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
    if (reducedMotion.matches) {
      showResult();
      $('demo-status').textContent = 'Answer retained · reduced motion';
      return;
    }
    const token = generation;
    $('replay').disabled = true;
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
    if (reducedMotion.matches) {
      showResult();
      $('demo-status').textContent = 'Answer retained · reduced motion';
      return;
    }
    playing = true; frame = 0;
    $('replay').querySelector('span').textContent = 'Thinking…';
    $('demo-status').textContent = 'Thinking · accelerated preview';
    const tick = () => {
      if (token !== generation) return;
      if (frame >= 12) { showResult(); return; }
      setScreen(frameUrl(character, frame++), `${character} companion thinking. Accelerated demonstration.`);
      timer = setTimeout(tick, 500);
    };
    tick();
  }
  $('replay').addEventListener('click', replay);
  document.querySelectorAll('[data-character]').forEach(button => button.addEventListener('click', () => {
    if (!characters.includes(button.dataset.character)) return;
    stop(); character = button.dataset.character;
    document.querySelectorAll('[data-character]').forEach(choice => choice.setAttribute('aria-pressed', String(choice === button)));
    showResult();
  }));
  document.querySelectorAll('[data-example]').forEach(button => button.addEventListener('click', () => {
    stop(); example = button.dataset.example;
    document.querySelectorAll('[data-example]').forEach(choice => choice.setAttribute('aria-pressed', String(choice === button)));
    $('demo-punchline').textContent = example === 'reminders' ? '“Your calendar needs a lawyer.”' : '“Cancelled. Nothing sent.”';
    $('film-link').href = `./assets/dot-${example}.mp4`;
    showResult();
  }));
  reducedMotion.addEventListener('change', () => { if (playing || timer || $('replay').disabled) { stop(); showResult(); } });
  document.addEventListener('visibilitychange', () => { if (document.hidden && (playing || $('replay').disabled)) { stop(); showResult(); } });

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
