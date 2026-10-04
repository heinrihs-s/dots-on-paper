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

Verify the canonical route, scroll-triggered thinking, both display modes, conversation turn selection, retained result, missing asset status, and retired URL status. The main portfolio references Dots on Paper and Cloakspan. Record the confirmed full commit SHA and deployment UUID in the infrastructure inventory; keep tokens and credentials outside both repositories.
