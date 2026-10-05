# Website deployment

Public route: https://heinrihs.org/dotsonpaper/.

The website is static. It runs inside the existing `heinrihs-s/heinrihs.org` Coolify application on Server A; no bridge, account connection, or device credentials are deployed with it.

| Setting | Value |
| --- | --- |
| Portfolio checkout | `C:/Users/Heinrihs_f0rjsns/Documents/claude/heinrihs.org` |
| Source checkout | `C:/Users/Heinrihs_f0rjsns/Documents/claude/TRMNL/dots-plugin` |
| Coolify application | ID `10`, UUID `uoo8w8ksc4w0o8g4cw8wsgcc` |
| Git source | `heinrihs-s/heinrihs.org`, branch `main` |
| Build | Root `Dockerfile`, nginx listening on port `3000` |
| Public files | Portfolio `dotsonpaper/` → `/usr/share/nginx/html/dotsonpaper/` |
| Server access | Infrastructure skill, saved `server-a` SSH record |

Build with `python tools/build_site.py`, copy the generated folder into the portfolio, and review its diff. Remove only retired files identified by the builder when synchronizing an older checkout. Preserve unrelated portfolio work.

Push both repositories. Queue a deployment of the existing application using the full 40-character portfolio commit SHA. Coolify fetches that revision remotely, so a shortened SHA is insufficient. Inspect the deployment status before reporting success.

The nginx configuration redirects `/dotsonpaper` to `/dotsonpaper/` with a relative redirect, serves project HTML without caching, and returns a real 404 for missing assets. The retired `assets/dot-noo.mp4` URL has an exact HTTP 410 route. After removing a previously served file, purge that exact URL from Cloudflare using the saved account token; assets otherwise have a seven-day cache.

The builder gives landing-page and trial scripts/styles content-hash query versions. Verify the URLs actually referenced by HTML against the manifest; this prevents a visitor's cached script from outliving its matching page. On 5 October the saved Cloudflare account token reported `expired`, so no purge was performed. New versioned URLs provide the updated assets; old unversioned cache entries remain until normal expiry. Refresh saved authentication before a future deletion that requires a purge.

Verify the canonical route, scroll-triggered thinking, both display modes, conversation turn selection, retained result, missing asset status, and retired URL status. The main portfolio references Dots on Paper and Cloakspan. Record the confirmed full commit SHA and deployment UUID in the infrastructure inventory; keep tokens and credentials outside both repositories.

## Beta website verified, 5 October 2026

Portfolio commit `f97f188c86942dd3c60e409d044a039a753752bf` finished in deployment `456850ec-6168-4571-9fe0-f3bacb6a2713` at `2026-10-05T08:39:49Z`. All 109 public files matched the generated manifest when fetched through their referenced URLs, including the four content-versioned scripts/styles. The canonical route and editable trial returned 200, a missing asset returned 404, and the retired film returned 410. A safe note was rendered and appeared in the readable transcript in the live browser trial. No Cloudflare purge or credential changes were performed.
