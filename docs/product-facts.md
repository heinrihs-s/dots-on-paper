# Product facts for the demo and X copy

Checked against official OpenAI documentation on **3 October 2026, Europe/Riga**. Product details and availability can change. This page separates documented behavior, this package's implementation, and fictional dialogue.

## What a ChatGPT dot does

A dot is an ongoing agent in ChatGPT. It works between conversations, returns results, and brings decisions back to the user. Its cloud computer can continue working while the user's computer is off. The user can customize its name and appearance. These are documented product behaviors; the four characters in this demo are our own display artwork. [Meet dots](https://learn.chatgpt.com/docs/dots)

A dot can handle several responsibilities, delegate parallel work, and continue after a conversation ends. Recurring work needs a saved schedule; monitoring requires an instruction identifying supported events, sources, and notification conditions. Connecting a service alone does not create a monitoring task. Relevant conversation context, ChatGPT memory, and the dot's own notes support continuity. [Tasks and memory](https://learn.chatgpt.com/docs/dots/tasks-and-memory)

ChatGPT, voice, Slack, and Teams are documented ways to contact the same dot. Conversations remain separate rather than mirroring every message. The messaging documentation currently says **“Texting is coming soon.”** Do not advertise the fictional wife-texting joke as an existing native SMS capability. [Message your dot](https://learn.chatgpt.com/docs/dots/channels)

A dot can use supported installed and enabled plugins. Its access depends on the connected account, permissions, and execution environment. A messaging contact method does not also connect the user's apps or computer. Local skills require a connected computer. Reading an inbox can be permitted separately from sending email. [Computers and apps](https://learn.chatgpt.com/docs/dots/computers-and-apps)

## What approval means

Before an action affects accounts or shares information, automatic review considers instructions, permissions, custom rules, and safeguards. An action may proceed, require approval, or need a user-operated step. Drafting permission does not authorize sending. A sufficiently scoped instruction can cover future actions; custom rules cannot grant an unavailable connection or bypass built-in requirements. Proactive research itself cannot send messages or change apps. Stopping work does not undo completed actions. Do not describe dots as either always requiring a send confirmation or universally sending without asking. [Control your dot](https://learn.chatgpt.com/docs/dots/controls)

## What this package actually implements

The current bridge's MCP interface exposes exactly these tools:

| Tool | Implemented result | Boundary |
| --- | --- | --- |
| `publish_dot_reply` | Stores the supplied answer, updates the display state, and makes a rendered image available. | Accepts text deliberately supplied by the caller; it does not independently read ChatGPT replies or calendars. |
| `set_dot_status` | Stores `thinking`, `idle`, or `error`, with optional safe display text. | This is a caller-reported status, not telemetry from the dot's internal activity. |
| `get_dot_state` | Returns the latest stored status, character, name, and reply. | Reading the bridge does not verify that physical hardware refreshed. |

These statements come from `src/dots_on_paper/server.py` and `state.py`. The plugin contains no texting, email, contact lookup, calendar modification, or message-delivery tool. It renders what was published. A response displayed in the marketing demo is scripted example data; a connected live dot must invoke the publishing tool with its actual result. Hardware refresh remains platform dependent. See [the real-dot setup](real-dot.md) for the supported MCP connection path and remaining account setup.

## Stage the joke honestly

This is a **scripted concept**. The user requested a clean composition without an extra fictional-demo footer; captions, source documentation, and embedded provenance retain that context:

> Dot: Okay, understood. Texting your wife that you have a date with Paula tonight.
>
> You: NOO.
>
> Dot: Relax. Nothing sent. Your calendar needs a lawyer.

For a closer imitation of documented behavior, change the first line to “Okay, understood. Drafting a text to your wife about your date with Paula tonight.” The humor can remain in the dialogue, while `DRAFT ONLY · NOT SENT` keeps the depicted outcome clear. Do not add a delivered checkmark, send-success toast, SMS branding, or a claim that `NOO` recalled a sent message. No real recipient, messaging connector, or external send is needed for this scene.

## ChatGPT dot and Codex are distinct

A dot can coordinate separate Work or Codex tasks; those tasks have their own conversations and receive context for their assigned work. They do not automatically inherit every dot conversation. [Tasks and memory](https://learn.chatgpt.com/docs/dots/tasks-and-memory)

The desktop app exposes ChatGPT and Codex as separate choices, with Chat and Work modes under ChatGPT. A workspace coding assistant using this bridge can publish its answer too, but that does not make it the user's persistent cloud dot. Use **“ChatGPT dot”** for the ongoing companion and **“Codex reply”** for an answer from a coding task, identifying the actual connected source when demonstrating live output. [ChatGPT desktop app](https://learn.chatgpt.com/docs/app)

## Instinct is a separate product

The user identified **[Instinct](https://instinct.com/)**, a separate personal-assistant product operated by Spear Street Technology, Inc. Its site describes app and device context, phone and computer use, texting and calls, proactive follow-up, and tasks such as rides and home repairs. These are product claims, not behaviors independently tested by this demo. [Instinct homepage](https://instinct.com/), [Instinct privacy policy](https://instinct.com/privacy-policy)

Instinct's privacy policy describes access to connected content according to granted permissions. It explicitly names Google Calendar, Gmail, Drive, Docs, Sheets, Slides, and Tasks through Google Workspace connections. It also describes user-provided communications and optionally enabled audio and location context. Do not infer support for a particular third-party messaging app from the broad word “messaging.” [Instinct privacy policy](https://instinct.com/privacy-policy)

The homepage's start link leads to account onboarding. Instinct's terms document phone-code sign-ins and notifications when a place becomes available. Those materials do not establish the user's eligibility, immediate access, or support in a specific country. [Instinct homepage](https://instinct.com/), [Instinct terms, SMS section](https://instinct.com/terms)

## Instinct integration and publishing boundaries

**No Instinct connector is implemented in this package.** Reviewing the homepage, its linked product/legal materials, and official-domain searches did not locate public developer API, MCP, reply-webhook, e-ink, or Home Assistant integration documentation. That is a research limit, not proof that no private integration exists. The existing bridge API remains available to authorized callers, but it does not itself make Instinct a supported caller.

Instinct's terms restrict unauthorized scraping, reverse engineering, and modifications. They also contain separate restrictions on publishing confidential or closed-beta screenshots, videos, and generated output when those restrictions apply. Use our own artwork and scripted concept data for this campaign; this is not a reproduction of a private Instinct account or evidence of an approved connector. [Instinct terms, use and beta sections](https://instinct.com/terms)

The terms describe actions on connected services and possible safeguards or confirmations. They do not provide a public action-review protocol equivalent to the ChatGPT dot documentation above. Do not claim that Instinct always asks before sending, never asks, can retract a delivered message, or supports a particular send workflow on the strength of this website alone. [Instinct terms, actions section](https://instinct.com/terms)

## Truthful angles for separate posts

- **ChatGPT dots:** an ongoing companion's actual published reply on paper. The package supports deliberate MCP display publishing, while live account connection and physical refresh must be verified. For a scripted clip, identify it as a concept. The joke's calendar judgment fits a personal-assistant conversation; native SMS should not be implied. [Meet dots](https://learn.chatgpt.com/docs/dots), [Message your dot](https://learn.chatgpt.com/docs/dots/channels)
- **Instinct:** “What if Instinct lived on e-ink?” An independent display concept about an assistant that follows everyday context and can be contacted by text or call. Use the wife's-text dialogue as fiction, with `DEMO · NOTHING SENT` visible. Describe the prototype as inspired by Instinct's stated direction, with no claim of live integration or endorsement. [Instinct homepage](https://instinct.com/)

Keep the two post packages separate. The same display renderer can illustrate both ideas without asserting that their models, connections, permissions, or availability are interchangeable.
