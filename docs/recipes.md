# Three small recipes

Use the [first-result setup](first-result.md) once. Keep the same bridge and source configuration for subsequent runs. The bridge retains published text; each recipe's assistant, monitor or automation supplies its actual data and schedule.

## Keep a completed task visible

Source: a local assistant with the three MCP tools enabled. Ask it to perform a real task, then call `publish_dot_reply` with a short summary, `source: "Desk assistant"`, and an optional title. Example instruction:

> After reviewing the site, publish the useful result to Dots on Paper in three short lines. Keep the full report in this chat. Use a fresh run ID if you report thinking first.

Success: the same summary appears in the browser, remains after restart, and can be read later without reopening the chat. A tool-published summary is deliberate publishing; it is not an automatic chat feed.

## Keep one daily brief

Source: an assistant or Home Assistant automation already connected to the required calendar/task data. Configure its daily schedule there. Ask it to publish only the confirmed items useful for a desk glance, with `source: "Daily brief"`. Keep locations, private notes and extra detail in the original app unless deliberately selected for display.

The bridge neither fetches calendars nor creates schedules. A browser sample such as “Call at 11. Check the invoice. Bring the parcel.” is illustrative. For a non-MCP automation, write the actual generated brief to a local text file and use `examples/publish.py --text-file brief.txt`; its publishing key is read from the configured private file.

Success: the configured source publishes on at least three days in a week without re-entering bridge setup. Record source/scheduler versions and failures in the beta study; do not call this a verified recurring recipe until that observation exists.

## Surface an exception that needs attention

Source: your existing backup monitor or an assistant checking its result. Publish a concise confirmed exception, such as “Backup failed. Check the storage connection,” with `source: "Backup monitor"`. Use a stable event ID for a retry of identical content. Open the original app to investigate or authorize any action.

This beta has one superseding active run and one retained result. It cannot promise an inbox, pin/dismiss policy or multi-agent monitoring. A later ordinary result can replace an exception; do not rely on this display as the sole alarm channel.

Success: a real failure can be reproduced, the published summary points back to its source, and reconnect/retry creates one result rather than duplicate history. [API and event ordering](api.md)

## Share a reviewed sample

The [browser trial](https://heinrihs.org/dotsonpaper/try/) starts with safe example text. **Prepare a safe sample** replaces the editor's personal text with a reviewed example before export. **Save screen** downloads only on your explicit click. Text stays in browser memory; it is not put into query strings, local storage or analytics.

A contributed photo/recipe should name source, panel model, firmware, refresh interval, setup time, known limits and permission to publish. Use the hardware form or the Recipes discussion category. No transcript is published automatically.
