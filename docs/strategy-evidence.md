# Strategy evidence — 5 October 2026

This record supports the [product and GitHub strategy](strategy.md). It distinguishes observations from recommendations. Source inspected: `a36a2c4bbf86858817a1059e73b02d8dce5110db` on `main`. The checkout was clean before adding the strategy documents.

## Engineering checks

| Check in this review | Result | Interpretation |
| --- | --- | --- |
| Existing `.venv` package against current Python tests | 47 tests attempted; 2 failures and 4 errors | Imports resolved to `.venv/Lib/site-packages/dots_on_paper`, whose state schema lacked current `mode`/`messages` support and whose renderer lacked `_conversation_messages`. |
| Current source with explicit `PYTHONPATH=src` | **69 tests passed**, approximately 9 seconds | Current source behavior passes the existing suite. The first result is installation drift, not proof of a source regression. |
| `node --test tests/test_mcp.mjs` | **15 tests passed** | Covers the current stdio adapter, protocol behavior, forwarding, configuration, and error redaction using local fixtures. |
| Latest GitHub workflow run via authenticated GitHub API | `success`, same source SHA | [Hosted CI run](https://github.com/heinrihs-s/dots-on-paper/actions/runs/37207817959), created 4 October 2026. |

Current-source reproduction in PowerShell, from the repository root:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location).Path 'src')
& .\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py'
node --test tests/test_mcp.mjs
```

The `PYTHONPATH` setting was confined to the audit command process. The existing installed package was not replaced, and no production state was published or cleared. A fresh artifact install, current installed-package smoke test, Docker runtime, live assistant-account connection, HA runtime, and physical panel were **not** verified in this review. The next release should test the shipped artifact rather than substituting the source-path run for installation validation.

Relevant source evidence:

- [State store](../src/dots_on_paper/state.py): `STATUSES` includes idle, thinking, answer, error; one `state` row with `id = 1`; a newer run supersedes a current thinking run. No source-specific inbox, expiry, or user dismissal exists in that state model.
- [HTTP server](../src/dots_on_paper/server.py): authenticated publication, settings, image and TRMNL display endpoints; no implemented cloud-image webhook output adapter or device render acknowledgement.
- [Preview](../src/dots_on_paper/web.html): credentials-file/key connection, selectors and image preview; no first-run test-publish form, assistant setup wizard, or history-clear control.
- [Setup](../tools/setup.py) and [CLI](../src/dots_on_paper/__main__.py): package installation and key initialization are separate from server startup and account/device connection.
- [Doctor](../tools/doctor.py): checks runtime, renderer assets, configuration and interfaces, but does not establish that the installed build matches the checkout.
- [Verification record](verification.md), [setup guide](setup.md), and [platform guide](platforms.md): explicitly describe the remaining live-account/hardware limits, no thinking expiry, device refresh behavior, and manual HA installation.
- [Packaging](../tools/package.py): source archive includes the demo/campaign trees; wheel copies depend on locally available builds. [CI](../.github/workflows/ci.yml) runs source and installed-package checks; it does not publish a tagged release or prebuilt Docker image.

Tracked-file sizes were measured from `git ls-files`, not by counting ignored local environments: `demo` 25.21 MiB, `campaign` 5.43 MiB, `brand` 3.58 MiB, `src` 6.70 MiB. GitHub's repository-size field was 84,343 KB. These are different measurements; neither is a measured download time.

## GitHub baseline

Repository: [heinrihs-s/dots-on-paper](https://github.com/heinrihs-s/dots-on-paper). Snapshot taken 5 October 2026. Public repository metadata and authenticated owner-access traffic endpoints were read; repository settings were not changed.

| Field | Observed value |
| --- | --- |
| Created | 3 October 2026, 20:46:47 UTC |
| Last push in snapshot | 4 October 2026, 14:02:51 UTC |
| Stars / forks / subscribers | 0 / 0 / 0 |
| Open issues / published releases | 0 / 0 |
| Homepage | Unset |
| Discussions | Disabled |
| License | MIT |
| Topics | chatgpt, e-ink, e-paper, esphome, home-assistant, mcp, openepaperlink, python, trmnl |
| Rolling views / unique visitors | 4 / 1 |
| Rolling clones / unique cloners | 119 / 58 |
| Reported referring sites | github.com: 1 view; heinrihs.org: 1 view |

Commands used included `gh api repos/heinrihs-s/dots-on-paper/traffic/views`, `/traffic/clones`, `/traffic/popular/referrers`, `/releases`, and `/actions/runs?per_page=1`, with output restricted to aggregate metadata. No tokens or personal visitor records were read out.

Unique counts across endpoints or referrers are not an additive funnel. Clones can include automation, and these aggregates cannot identify active installations. No reliable activation, retention, release-download, or user-satisfaction baseline exists yet. The strategy's targets are proposed thresholds, not inferred current performance.

## Independent website assessment

Method: dual-agent review. Assessment A: `/root/ux_review`; Assessment B: `/root/ux_evidence`. The assessments were isolated; A completed before B's findings were read in the parent review. The Impeccable skill supplied the review method. These scores describe the website and its installation guidance, not market demand or production reliability.

### Assessment A: design and user journey

The paper identity, four characters, display frame, restrained palette, and typography are distinctive and appropriate. The demo has useful controls for replay, skipping thinking, display mode, manual conversation turns, and reduced motion. Existing disclosures meaningfully qualify simulation and hardware behavior.

| Priority | Finding | Location | Strategy response |
| --- | --- | --- | --- |
| P1 | Connection choices mix answer sources with display destinations. A user connecting a dot to TRMNL needs multiple stages. LAN configuration is introduced after the general start command. | [Setup panels](../site/index.html) | Separate run → publish → display steps and choose one complete recommended path. |
| P1 | Setup lacks an explicit first successful reply checkpoint; opening the preview and importing credentials is not activation. | [Site setup](../site/index.html), [README](../README.md) | Add a test card, real-source publishing check, and expected result. |
| P1 | The README states outstanding live verification more clearly than the landing page. | [README](../README.md), [verification](verification.md) | Put short readiness labels beside setup and prove one physical path. |
| P2 | The prepared jokes explain personality more clearly than an everyday job. | [Demo scenarios](../site/site.js) | Lead with a useful task result and keep the joke as an optional sample. |
| P2 | “Your dot” assumes familiarity before explaining audience and prerequisites. | [Hero](../site/index.html) | Add a plain mechanism and audience description while retaining the brand. |

The emotional journey is appealing discovery → understandable simulation → a setup valley across several documents → no explicit real-reply payoff. Moderate cognitive load comes from assembling the route and remembering prerequisites; no single picker exceeds four choices.

| Nielsen heuristic | Score, 0–4 | Main observation |
| --- | --- | --- |
| Visibility of system status | 3 | Good demo feedback; weak installation milestones. |
| Match to the real world | 2 | Dot/MCP terms and mixed categories need explanation. |
| User control and freedom | 4 | Replay, skip, mode and character controls, reduced motion. |
| Consistency and standards | 3 | Familiar controls; platform/OS scope needs clarity. |
| Error prevention | 2 | Useful warnings; prerequisite ordering can still mislead. |
| Recognition rather than recall | 2 | Copy controls help; users assemble several guides. |
| Flexibility and efficiency | 3 | OS choice, copying, keyboard tabs, documentation links. |
| Aesthetic and minimalist design | 3 | Strong visual direction; usefulness needs more emphasis. |
| Error recognition and recovery | 3 | Frame retry, clipboard fallback, troubleshooting links. |
| Help and documentation | 3 | Extensive material without one complete visitor journey. |
| **Total** | **28/40** | Subjective heuristic assessment; all ten applied. |

Persona observations: a first-time visitor needs “dot” explained and a success checkpoint; a skeptical maker needs tested-device evidence; a mobile visitor needs a clear handoff to desktop setup. These are review hypotheses, not observed abandonment. The useful question for the beta is whether a person can reach and repeat a real useful result without assembling instructions themselves.

Assessment A used source review, a fresh public desktop browser tab, visual inspection and demo interaction, plus a mobile accessibility snapshot at 390 × 844. Its mobile screenshot request stalled, so it did not claim visually verified phone layout. No detector output was shown to A.

### Assessment B: mechanical and browser evidence

The detector ran once against `site/index.html`: exit 0, JSON `[]`, **zero reported findings**. However, its HTML parser dependencies (`htmlparser2`, `css-select`, `css-tree`, `domutils`) were unavailable. It fell back to regex and explicitly warned that CSS custom properties, selector matching, and computed contrast were not evaluated. This is an undercount, not a clean accessibility/design certification. No dependencies were installed or scan repeated; no detector findings needed false-positive classification.

Fresh native-browser inspection covered desktop 1440 × 1000 and phone viewport 390 × 844. The second assessment visually inspected both sizes and measured the live DOM. This was a viewport check, not a real phone or touch-input test.

| Finding | Evidence | Consequence |
| --- | --- | --- |
| Confirmed P2 mobile heading defect | `site/index.html:52` contains `Watch a<br>thought land.`; the narrow-screen rule at `site/styles.css:10` hides the break. Live text becomes `Watch athought land.` | Preserve a real space when changing the line break. |
| Phone preview is difficult to read | A 960-pixel source frame is displayed about 315 CSS pixels wide. Native screenshots show small reply text and conversation labels; no expand/transcript control is present. | Add an expanded view or readable transcript without changing the actual renderer output. |
| Actual result follows the brand artwork | On the desktop pass, demo begins around y=1108; on the phone pass the device begins around y=1238. Hero links do reach the demo. | Give the useful result greater early prominence; this is hierarchy advice, not a broken navigation finding. |
| Several controls are compact | Measured phone heights: replay 30px, mode buttons about 38px, OS options about 26px, copy buttons 24px, platform tabs about 36px. | Improve touch comfort. Measurements alone do not prove a WCAG target-size violation. |

Positive checks: demo anchor navigation, retained reply, Full conversation selection, Artist selection, final conversation turn, Windows start command, TRMNL/HA tabs, ArrowRight tab focus/selection, and an expanded FAQ worked. Warning/error logs returned `[]` after each viewport pass. No page-level horizontal overflow was observed; long code blocks scrolled inside their containers. All eight DOM images had loaded by the later pass. A below-fold lazy image eventually loaded and was not a broken asset. Descriptive image alternatives, pressed states, tab semantics, status announcements, a skip link, and focus styling were present.

Limits: no complete network audit, performance benchmark, screen-reader session, forced reduced-motion check, clipboard action, source installation, hardware run, or all-character/mode permutation test. One FAQ role locator failed; a refreshed exact-text locator succeeded, so this was not reported as a product defect. Production and source content aligned on inspected controls, but asset hashes were not compared.

The browser evaluate API was read-only, so no detector overlay was injected or presented. No local server was started. Assessment B reset its viewport and closed its temporary tab. Assessment A closed its desktop tab; its final mobile-tab close was refused because that browser tool requires one remaining tab. The ignore list did not exist. Target slug: `site-index-html`. Source and public-site observations informed the strategy; there were no UI fixes or deployment changes.

## External sources checked

These are primary sources accessed on 5 October 2026. Capability, availability, and quota details should be checked again during implementation.

- [TRMNL Webhook Image](https://help.trmnl.com/en/articles/13213669-webhook-image): raw image upload, private webhook, 1 MB maximum and 12 uploads/hour in the current help article. Device refresh timing remains separate. The proposed adapter does not exist in this project yet.
- [TRMNL refresh behavior](https://help.trmnl.com/en/articles/10113695-how-refresh-rates-work) and [BYOS](https://docs.trmnl.com/go/diy/byos): distinguish server image availability from device fetch/refresh.
- [AgentDeck](https://github.com/puritysb/AgentDeck): adjacent agent-session dashboard and physical-surface ecosystem. Its own support claims were not independently reproduced here.
- [Tesserae](https://github.com/dmellok/tesserae): adjacent dashboard composer, onboarding, transports, and MCP path. Its own support claims were not independently reproduced here.
- [TRMNL Home Assistant](https://github.com/usetrmnl/trmnl-home-assistant) and [E-Ink Dashboard for HA](https://github.com/cryptomilk/hass-eink-dashboard): alternatives for dashboard/image delivery. These informed the recommendation to avoid a generic dashboard-editor expansion.
- [HACS integration requirements](https://www.hacs.xyz/docs/publish/integration/): packaging requirements; releases are preferred, not mandatory. HACS listing and operational verification are different milestones.
- [GitHub traffic](https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository/viewing-traffic-to-a-repository) and [topics](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics): measurement window and discovery mechanisms, not a formula for virality.
- [Show HN guidelines](https://news.ycombinator.com/showhn.html): favor a project readers can try. No post or outreach was made during this review.

The broader product recommendation, six-week sequence, effort estimates, sample size, and numerical goals are reasoned proposals. They are not competitor-derived benchmarks, promises of virality, or results of a user study.
