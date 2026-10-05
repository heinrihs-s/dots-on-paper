# Dots on Paper: usefulness, adoption, and GitHub growth

Prepared 5 October 2026, Europe/Riga. Based on source commit `a36a2c4`, repository analytics, current platform documentation, and an independent website review. This is a proposed strategy; the roadmap features and launch activities below have not been implemented or published.

Implementation update: the first engineering beta implements the software and repository preparation described below. See the [current roadmap and outstanding evidence gates](roadmap.md), [beta release notes](release-notes-0.2.0-beta.1.md), and [verification record](verification.md). The original audit and estimated schedule remain below as dated planning evidence; physical delivery, observed users and promotion are still pending.

## The decision

Make Dots on Paper **a small, dependable place for your assistant's useful results to stay visible**. Start with people who already use an AI assistant at their desk and enjoy self-hosted tools, especially existing TRMNL owners. Let everyone else experience it in a browser before requiring hardware.

Suggested positioning: **“Your AI's useful updates, on your desk.”**

The first promise should be specific: an assistant finishes a task, publishes a short result, and that result remains readable when you look away from the computer. Next, support a daily brief and a decision that needs your attention. Keep the four characters, paper identity, latest-reply mode, and conversation mode. Their personality makes a useful object recognizable and shareable.

The strongest next investment is a complete first-use experience and verified hardware delivery. More campaign films, more characters, and more theoretical device profiles can wait.

## What the audit establishes

| Observed evidence | Product implication |
| --- | --- |
| The current source passes **69 Python tests and 15 Node MCP tests**. Hosted CI passed for the inspected commit. | There is a useful engineering foundation to build on. |
| The local `.venv` contains an older installed package. Running current tests against it produced six failures/errors; explicitly testing current `src` passed. | Updating the checkout does not reliably update the running product. Installation/version diagnostics and a tested upgrade path matter. |
| The docs explicitly leave live dot access, physical display delivery, and a real HA runtime unverified. | The core promise needs a recorded, repeatable end-to-end demonstration. Source tests do not prove that experience. |
| First use requires installation, launch, credentials-file selection, source connection, then display/network configuration. The preview initially waits for a dot. | A newcomer does considerable work before seeing a personally useful result. |
| `StateStore` keeps one current state and one active run. A newer run supersedes the older one. Thinking has no automatic expiry. | A missed completion can leave a permanent thinking screen; concurrent sources need an explicit policy. |
| The public demo has prepared scenarios; the editable standalone demo is a separate local path. | Visitors can admire the product more easily than try their own use case. |
| GitHub: **0 stars, 0 forks, 0 releases**, homepage unset, Discussions off. The repository was created on 3 October. | This is a new project awaiting a usable release and distribution, not evidence of rejected demand. |
| GitHub's rolling traffic snapshot shows **4 views / 1 unique visitor** and **119 clones / 58 unique cloners**. | Clones are not installed or retained users. These small, potentially automated/maintainer-influenced counts cannot establish demand. |

Detailed reproduction notes, source references, and review limits are in [strategy-evidence.md](strategy-evidence.md). No interviews or retention study have been run, so the audience and use cases below are hypotheses to test.

## Choose one audience and three useful jobs

**First audience:** a technical person who uses an assistant for real work, wants fewer reasons to reopen a chat, and can run a local service. Existing TRMNL ownership is a good recruitment filter, not a requirement to try the product.

| Order | Useful job | Example screen | Why it can earn repeat use |
| --- | --- | --- | --- |
| 1 | Keep a completed task visible | “Site review finished. Two broken links found. Report ready.” | The useful output remains available after the chat disappears behind other windows. |
| 2 | Keep one daily brief visible | “Today: client call at 11, invoice to check, bring the parcel.” | A scheduled, predictable reason to glance at the display. |
| 3 | Surface a decision or exception | “The backup failed. Check the storage connection.” | A meaningful change earns attention without streaming every event. |

Each recipe must name its real source. A calendar brief requires a connected source and a configured schedule in the assistant or HA; this bridge does not currently fetch calendars or schedule work. A decision card points back to the original app. It does not authorize or execute the action.

Begin with **one verified local MCP client → bridge → browser preview → one physical TRMNL model**. Use the user's available device for the first proof, and record its exact model and firmware. Keep the cloud-dot tunnel path as an advanced option until tested with a real account. Avoid making cloud-account eligibility a prerequisite for every newcomer.

Recruit ten testers around the first job. Watch them set it up; then ask on day seven what they actually kept on the screen, whether they noticed it, and whether they would keep it running. Add the other jobs only when they answer a real need.

## Where it can stand out

There are already substantial adjacent projects:

| Project | What its current documentation offers | Strategic consequence |
| --- | --- | --- |
| [AgentDeck](https://github.com/puritysb/AgentDeck) | Agent-session dashboards, physical controls, multiple display types, and event/hook integrations. | A broad coding-agent control center would face an established alternative. Focus on a short, retained result and a much smaller setup. |
| [Tesserae](https://github.com/dmellok/tesserae) | Browser-composed e-ink dashboards, first-run setup, multiple transports, and MCP-assisted composition. | A general dashboard editor is a costly direction. Make opinionated result cards exceptionally easy instead. |
| [TRMNL Home Assistant](https://github.com/usetrmnl/trmnl-home-assistant) and [E-Ink Dashboard for HA](https://github.com/cryptomilk/hass-eink-dashboard) | Existing ways to turn dashboards or HA entity state into e-ink images. | Reuse those ecosystems. Another weather-and-calendar dashboard alone offers little differentiation. |

The opportunity is a **friendly paper inbox for useful results**, with a local core, readable defaults, reliable delivery, and small adapters. This is a positioning hypothesis, not a claim that the category is empty. Integration with existing display infrastructure may be more valuable than replacing it.

## Product changes, in order

### 1. Get to a first result in minutes

Build one guided path with four steps:

1. **Start:** launch the bridge and open its local setup screen. Check prerequisites with an actionable failure message. Node should be requested only for paths that need the current stdio adapter.
2. **Try:** enter a short note and show it immediately in the real renderer. Clearly identify this as a local test, independent of an assistant connection.
3. **Connect a source:** generate configuration for one tested MCP client, then prove it with an actual tool-published reply. Show whether publishing succeeded.
4. **Choose where it appears:** keep the browser preview, or connect the one supported hardware route and send a test card.

Give the user a visible progress checklist. Keep source and display choices separate: “ChatGPT dot” and “TRMNL” are different parts of the same setup. Move character and conversation customization after the first successful result, while preserving those controls for returning users.

Retain separate publishing and image credentials. Replace routine JSON-file handling with an explicit local pairing flow or a launcher-assisted connection. Do not put publishing keys in shareable URLs or make the bridge public to simplify setup.

Extend the existing doctor and launcher rather than adding another unrelated setup tool. Report the effective installed build/path, bridge reachability, source test, and display-fetch/upload status. An HTTP success means the image was accepted or fetched; only a device acknowledgement or observed panel can prove it was displayed.

**Acceptance:** at least 8 of 10 target users reach their first real assistant result in the browser within ten minutes, without maintainer intervention. Measure hardware setup separately; target thirty minutes after the device is already online. Record failures rather than excluding unsuccessful attempts.

### 2. Make stock TRMNL an easier hardware route

Run a short feasibility test for the official [Webhook Image plugin](https://help.trmnl.com/en/articles/13213669-webhook-image). It accepts image uploads and currently documents a **1 MB image limit and 12 uploads per hour**. The physical device still updates according to its refresh settings.

Add a bridge adapter that uploads **completed result cards** to a configured webhook. Coalesce repeated updates, persist pending delivery, respect rate limits, retry temporary errors, and report the last accepted upload. Validate actual image compatibility and account access on the chosen model before making it the recommended route.

This route could avoid BYOS server changes and device-to-local-network setup for stock owners. It is a cloud-dependent option and should be labelled accordingly. Keep BYOS for local delivery and advanced refresh control. Webhook uploads are unsuitable for a sequence of thinking frames.

**Acceptance:** a real assistant result reaches a stock device, survives a bridge restart, and recovers from a temporary upload failure. Publish measured latency with the actual device settings. If the feasibility test fails, ship the verified BYOS route and state its prerequisites prominently.

### 3. Make retained information trustworthy

For the first usable release:

- Add a configurable thinking timeout, with a truthful “No recent update” state and a recovery action. Retain the last completed result separately so a failed task does not erase it.
- Show source and a compact update time when useful. Freeze that timestamp into the card; do not repaint the panel every minute just to change a relative-age label.
- Provide “Send test card,” “Clear display,” and an explicit way to clear stored conversation/history.
- Add a display-length budget and a way to open the full result in the local browser. A short useful summary should remain readable on small screens.
- Offer a settled-image preset for battery devices. Make thinking animation an opt-in capability with tested refresh limits.
- Test restart, disconnect, expired run, duplicate event, and reconnect behavior using temporary state. Continue using the existing `event_id`/`run_id` protections.

For the following release, if testers use multiple sources, introduce a bounded inbox keyed by source and task. Add “needs input,” “done,” and “error” card types with an explicit priority policy, expiry, pin/dismiss, and deduplication. Keep approval cards until dismissed; let low-priority summaries expire. Preserve existing API callers through a versioned extension or adapter.

Do not promise multi-agent monitoring while there is one superseding active run. Do not make a caller's voluntary MCP tool use sound like automatic observation. Use documented client events/hooks where available, and keep explicit publishing as a supported fallback.

### 4. Package it like something people can install

- Publish a tagged beta with a tested runtime artifact, checksums, release notes, and an exact compatibility table.
- Build a prebuilt, versioned Docker image and verify persistent startup and upgrade. Test ARM64 before claiming Raspberry Pi support; a Dockerfile alone is not that proof.
- Give desktop users one maintained installation path with clear update/restart instructions. Avoid a native-app rewrite until installation evidence warrants it.
- Add build/capability checks so a stale installed package is caught even if both old and new source report `0.1.0`.
- Keep one small preview in the source tree and distribute large film exports separately. The tracked `demo`, `campaign`, and `brand` trees currently total about 34.2 MiB. Removing future binaries does not shrink old Git history; prefer small runtime downloads without rewriting history.
- Validate HA in an actual HA runtime before promoting that path. Then test installation as a HACS custom repository and consider default-directory submission. HACS distribution of the integration does not itself install the separate bridge. [Current HACS requirements](https://www.hacs.xyz/docs/publish/integration/)

### 5. Make the website help people succeed

Keep the existing visual identity. Lead with a useful result and one sentence explaining who it helps. Suggested hierarchy:

1. Short real-device clip and the result it delivered.
2. **Try in your browser** and **Install** as distinct actions.
3. Three practical examples, with their actual source and prerequisites.
4. One recommended installation route, with advanced alternatives below it.
5. Tested compatibility, known limits, troubleshooting, and contribution paths.

Bring the existing editable reply experience to the public demo so someone can type their own brief, choose a character, and download a sample image. Label browser examples as simulations. Keep personal demo text in the browser and leave it out of analytics and share URLs.

Fix two observed mobile problems in the same pass: hiding the demo heading's line break joins “a” and “thought” into “athought”; the native screen text becomes very small on a phone. Preserve the heading space and offer a readable transcript or expanded preview. Enlarge compact touch controls where practical. The checked desktop and phone layouts contained horizontal scrolling correctly and produced no browser warnings/errors; a wholesale visual redesign is unnecessary.

Separate “publishing works,” “image uploaded/fetched,” and “panel observed.” The current documentation already treats those honestly; the setup screen should make the distinction easier to understand.

## GitHub growth strategy

Virality is an uncertain outcome. Build the conditions for a strong launch: a distinctive object, an immediately understandable benefit, evidence it works, and a path visitors can reproduce.

### Prepare the repository before promotion

The repo already has an MIT license, CI, contribution guidance, a bug template, topics, and extensive docs. Improve the missing conversion steps:

- Set the About homepage to the existing public website. Use a concrete description, such as “A tiny e-ink companion for useful AI replies. Local bridge, MCP, and Home Assistant.”
- Add a working latest-release link and a CI badge. Keep the first README screen focused on outcome, demonstration, and getting started.
- Add a short “Works today” matrix with **verified / experimental / example only** labels, model and firmware versions, and dates.
- Open Discussions with “Show your desk,” “Setup help,” and “Recipes.” Add a hardware-verification issue form and a short public roadmap.
- Prepare five genuinely bounded contributor tasks: document one verified device, translate setup text, improve a small-screen layout, supply a tested recipe, or validate a client configuration. Each needs reproduction steps and a definition of done.
- Keep relevant existing topics. Add audience-specific topics only when the corresponding integration actually works. Topics aid discovery; they do not guarantee ranking. [GitHub topic documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics)

### Make a demonstration people can repeat

Record one 20–30 second real-desk demonstration:

1. Show a normal task request in the connected assistant.
2. Show the useful result on the actual panel, including enough detail to understand it.
3. Show the user returning to that retained result later.
4. End with the project name, a short setup claim backed by measured tests, and the repository URL.

Preserve real refresh behavior. Label any time compression. Use synthetic or deliberately selected demonstration content, not private transcripts. Keep the existing jokes as optional secondary material; the launch should make the daily benefit clear before asking viewers to enjoy the character.

Candidate launch headline, once demonstrated: **“I gave my AI's finished work a place on my desk.”**

Candidate Show HN title: **“Show HN: Dots on Paper — useful AI replies on an e-ink display.”** Publish that only when readers can try it; Show HN explicitly favors something people can use over a landing page alone. [Show HN guidelines](https://news.ycombinator.com/showhn.html)

### Launch in stages

| Stage | Audience and material | What to learn |
| --- | --- | --- |
| Private/small beta | 10 target users; one exact setup guide; observed first use. | Where installation fails and whether the result remains useful after a week. |
| Maker release | TRMNL and e-paper communities; exact hardware, normal-speed footage, verified configuration. | Whether another person can reproduce the desk setup. Follow each community's current posting rules. |
| Developer release | Show HN and relevant MCP/agent communities; working browser trial, repository, installation and architecture details. | Whether the benefit resonates beyond hardware enthusiasts. |
| Follow-up | X/Mastodon clips, a build article, and user-contributed desk photos with permission. | Which genuine use case generates installations and contributions. |

Space stages by several days so fixes from one audience improve the next. Be available to answer technical questions on launch day. Approach maintainers or creators with a working, relevant example when ready; outreach and posting are future actions, not performed by this strategy.

### Build a reason for users to share

The repeatable sharing path should be:

**Useful result → personal desk photo or safe sample card → recipe/configuration → another person's successful setup.**

Offer an explicit “Share a sample” export that starts with safe example text, lets the user review it, and links to the matching installation guide. Never automatically publish real answers. A gallery contribution should include the display model, source, template, setup time, and known limitations; credit the contributor.

Measure whether shared recipes lead to working installations. Keep stars optional. Avoid star exchanges, mass unsolicited messages, or repeated launch posts with no new value. They do not establish usefulness and create support noise.

## Delivery plan and gates

Assume one maintainer with roughly 20–30 focused engineering days across six weeks, plus tester/hardware waiting time. These are planning estimates, not delivery commitments. At five hours a week, extend the calendar rather than compressing the verification.

| Phase | Work | Exit condition |
| --- | --- | --- |
| First 2 days | Capture one real assistant-to-device run; test stock TRMNL webhook feasibility; diagnose current install drift; write the first-use checklist. | One observed physical result, exact environment recorded, and a chosen primary route. If hardware is unavailable, mark the physical gate blocked and continue browser work. |
| Week 1–2 | Guided first-run/test card; installed-build diagnostics; stale-thinking recovery; retained last result; clear/history controls; one client configuration. | Fresh setup and upgrade work on the supported OS; crash/reconnect cases behave truthfully; 5 observed testers attempt setup. |
| Week 3 | Finish the chosen hardware adapter and beta packaging; provide one practical recipe; run ten-user activation and seven-day follow-up. | At least 8/10 reach a real browser result unaided; physical path reproduced by at least 3 independent owners. |
| Week 4 | Fix measured friction; improve README/site entry path; publish safe editable browser trial; document user setups. | At least 5/10 activated beta users still use a real recipe on day seven; 3 useful use cases/photos documented with permission. |
| Week 5–6 | Tag the verified release; prepare the real-device film; launch to makers, then developers; respond and patch. | Downloads, guide, trial, and compatibility claims all work for the same release. If earlier gates fail, use this time on the failed gate. |
| Following 30–60 days | Add the next adapter or inbox behavior that retained users request; improve the main recipe. | Expansion follows repeated demand, not a speculative support matrix. |

An initial implementation backlog, in dependency order:

| Priority | Proposed issue | Existing starting point | Rough effort | Done when |
| --- | --- | --- | --- | --- |
| P0 | Verify one assistant → physical panel path | `docs/real-dot.md`, `docs/platforms.md` | 1–2 days plus access | Real result, device/firmware, refresh measurements, and reproduction documented. |
| P0 | First-run checklist and test card | `src/dots_on_paper/web.html`, `tools/setup.py` | 3–4 days | A new user can prove rendering and publishing from the UI without manual API requests. |
| P0 | Diagnose installed-build drift and document upgrades | `tools/doctor.py`, launchers, package metadata | 1–2 days | An old package is detected; reinstall/restart restores expected capabilities without losing state. |
| P0 | Recover interrupted work and retain the last useful answer | `state.py`, `server.py`, `render.py` | 2–3 days | Timeout and restart cannot leave endless thinking or silently discard the prior result. |
| P0 | Versioned beta artifacts and startup verification | `.github/workflows/ci.yml`, `Dockerfile`, `tools/package.py` | 2–3 days | Fresh runtime install and upgrade are exercised from the exact shipped artifact. |
| P1 | Finished-card TRMNL webhook adapter | New output adapter beside `server.py` | 3–4 days after feasibility | Quotas, pending delivery, retry, restart, and actual panel output verified. |
| P1 | Safe clear, full-result view, and display length guidance | `web.html`, `state.py`, renderer | 2–3 days | The user can read omitted text and deliberately clear both screen and stored history. |
| P1 | Editable public trial and outcome-focused README | `demo/`, `site/`, `README.md` | 2–3 days | A visitor tries their own text and reaches the correct install guide. |
| P1 | First repeatable daily-use recipe | Existing MCP tools and `examples/` | 1–2 days plus study | A tester repeats it without re-entering setup or reconfiguring keys. |
| Later | Bounded inbox, HA packaging, another client/device | Existing state/API and HA integration | Scope after evidence | Retained users demonstrate a recurring need and the added path is verified. |

## Measure usefulness before celebrating reach

Use beta interviews and local diagnostics first. If adding aggregate product telemetry later, make it opt-in and content-free. Never collect answer text, keys, private URLs, or conversation history for growth measurement.

| Metric | Definition / collection | Initial decision threshold |
| --- | --- | --- |
| Activation | A recruited tester publishes their own real assistant result and sees it in the browser. Record time and need for help. | 8/10 complete unaided in ≤10 minutes. |
| Physical success | Independent owner sees the same result on the named panel. Record firmware and delay. | 3 independent reproductions before a hardware-led launch. |
| Seven-day retention | Of activated testers, count those using a real recipe during days 5–7 and intending to keep it. Collect consented follow-up. | At least 50% of the activated cohort; expand recruitment until there are 10 activated users, then require at least 5. A small-sample gate, not a statistically precise market estimate. |
| Weekly useful use | Users receiving personally useful updates on at least 3 days/week. Self-report or opt-in aggregate, not API event volume. | Rising across two cohorts. |
| Support burden | Minutes of maintainer help per activated install; repeat failure categories. | Falls with each cohort; recurring failures become P0 onboarding work. |
| Reach | GitHub visitors, referrals, releases downloaded, stars, and external mentions. | Track separately from activation; downloads/clones are noisy proxies. |

Save a dated GitHub traffic snapshot at least weekly while actively launching; GitHub exposes a rolling **14-day** traffic window. Record anonymous website actions such as demo use, guide selection, and outbound GitHub clicks only if suitable analytics are installed. These metrics currently do not establish a joined person-level funnel. [GitHub traffic documentation](https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository/viewing-traffic-to-a-repository)

An aspirational first 30 days after launch: **20 confirmed working installations, 10 weekly users, 3 outside contributors, and 100 stars**. A thousand stars is a possible breakout outcome, not a forecast or the gate for a useful product.

If visits grow but activation stays low, fix setup. If installs grow but week-one use is weak, improve the recipe and retained information. If use is strong but visits are low, improve the demonstration and distribution. If stars grow without use, treat that as attention to the concept rather than product validation.

## Scope to protect

For this cycle, defer a dashboard editor, a native mobile app, paid cloud hosting, additional characters, broad automatic chat capture, and a long hardware-support list. Keep the existing API and characters; spend the effort on reliable operation, a shorter setup, and evidence from people using it.

The first concrete milestone is **one verified daily-use loop another person can install and repeat**. That is the strongest foundation for both a useful project and a credible GitHub launch.
