(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const characters = ['artist', 'curious', 'bookish', 'cool'];
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const replies = {
    reminders: 'heidot’s reply: Here are your reminders. Tonight: Date with Paula. Tomorrow morning: Breakfast with Amy. Lunch: With your wife. Your calendar needs a lawyer.',
    conversation: 'heidot: Okay, understood. Texting your wife about your date with Paula tonight. Draft ready, waiting for approval. You: NOO. heidot: Cancelled. Nothing sent.',
  };
  const turns = [
    'heidot: Okay, understood. Texting your wife about your date with Paula tonight. Draft ready, waiting for approval.',
    'heidot: Okay, understood. Texting your wife about your date with Paula tonight. Draft ready, waiting for approval. You: NOO.',
    replies.conversation,
  ];
  let character = 'cool', example = 'reminders', frame = 11, turn = 3;
  let timer = null, generation = 0, playing = false;
  const loaded = new Map();
  const frameUrl = (id, index) => `./assets/frames/${id}-thinking-${index}.png`;
  function stop() { clearTimeout(timer); timer = null; playing = false; generation++; }
  function setScreen(url, alt) { $('screen').src = url; $('screen').alt = alt; }
  function setTurn(index) {
    turn = index;
    setScreen(`./assets/frames/${character}-conversation-${turn}.png`, turns[turn - 1]);
    document.querySelectorAll('[data-turn]').forEach(button => button.setAttribute('aria-pressed', String(Number(button.dataset.turn) === turn)));
    $('demo-status').textContent = ['Draft ready', 'Your reply', 'Conversation retained'][turn - 1];
  }
  function resetReplay() {
    $('replay').disabled = false;
    $('replay').querySelector('span').textContent = example === 'conversation' ? 'Replay conversation' : 'Replay thinking';
  }
  function showResult() {
    playing = false;
    if (example === 'conversation') setTurn(3);
    else {
      setScreen(`./assets/frames/${character}-${example}.png`, replies[example]);
      $('demo-status').textContent = 'Answer retained';
    }
    resetReplay();
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
    closeFilm(false);
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
      if (frame >= 12) {
        if (example !== 'conversation') { showResult(); return; }
        const advance = index => {
          if (token !== generation) return;
          setTurn(index);
          if (index === 3) { playing = false; resetReplay(); return; }
          $('replay').querySelector('span').textContent = 'Conversation…';
          timer = setTimeout(() => advance(index + 1), index === 1 ? 2200 : 1400);
        };
        advance(1);
        return;
      }
      setScreen(frameUrl(character, frame++), `${character} companion thinking. Accelerated demonstration.`);
      timer = setTimeout(tick, 500);
    };
    tick();
  }
  $('replay').addEventListener('click', replay);
  document.querySelectorAll('[data-turn]').forEach(button => button.addEventListener('click', () => {
    if (example !== 'conversation') return;
    stop(); setTurn(Number(button.dataset.turn)); resetReplay();
  }));
  document.querySelectorAll('[data-character]').forEach(button => button.addEventListener('click', () => {
    if (!characters.includes(button.dataset.character)) return;
    stop(); character = button.dataset.character;
    document.querySelectorAll('[data-character]').forEach(choice => choice.setAttribute('aria-pressed', String(choice === button)));
    showResult();
  }));
  document.querySelectorAll('[data-example]').forEach(button => button.addEventListener('click', () => {
    if (!Object.hasOwn(replies, button.dataset.example)) return;
    stop(); example = button.dataset.example;
    document.querySelectorAll('[data-example]').forEach(choice => choice.setAttribute('aria-pressed', String(choice === button)));
    $('demo-punchline').textContent = example === 'reminders' ? '“Your calendar needs a lawyer.”' : '“Cancelled. Nothing sent.”';
    $('conversation-controls').hidden = example !== 'conversation';
    closeFilm(false);
    showResult();
  }));
  const film = $('film');
  function closeFilm(restoreFocus = true) {
    film.pause();
    $('film-panel').hidden = true;
    $('film-link').setAttribute('aria-expanded', 'false');
    if (restoreFocus) $('film-link').focus({ preventScroll: true });
  }
  $('film-link').addEventListener('click', () => {
    if (!$('film-panel').hidden) { closeFilm(); return; }
    stop(); showResult();
    const source = `./assets/dot-${example}.mp4`;
    $('film-title').textContent = example === 'conversation' ? 'The whole conversation.' : 'A reply that stays.';
    $('film-status').textContent = '';
    film.poster = `./assets/frames/cool-${example}.png`;
    if (film.getAttribute('src') !== source) { film.src = source; film.load(); }
    else film.currentTime = 0;
    $('film-panel').hidden = false;
    $('film-link').setAttribute('aria-expanded', 'true');
    $('film-panel').scrollIntoView({ block: 'nearest', behavior: reducedMotion.matches ? 'instant' : 'smooth' });
    film.focus({ preventScroll: true });
    film.play().catch(() => { if (!$('film-panel').hidden) $('film-status').textContent = 'Press play to start the film.'; });
  });
  $('close-film').addEventListener('click', () => closeFilm());
  $('film-panel').addEventListener('keydown', event => { if (event.key === 'Escape') { event.preventDefault(); closeFilm(); } });
  film.addEventListener('error', () => { $('film-status').textContent = 'The film couldn’t load. Close it and try again.'; });
  film.addEventListener('ended', () => { $('film-status').textContent = 'The result stays on the screen.'; });
  reducedMotion.addEventListener('change', () => { if (playing || timer || $('replay').disabled) { stop(); showResult(); } });
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) return;
    film.pause();
    if (playing || $('replay').disabled) { stop(); showResult(); }
  });

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
