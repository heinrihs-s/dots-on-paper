# Works today

Beta bridge: `0.2.0b1` / Git tag `v0.2.0-beta.1`. Evidence date: 5 October 2026, Europe/Riga. [Exact checks and versions](verification.md)

| Path | Label | Verified scope | Model / firmware |
| --- | --- | --- | --- |
| Local bridge and browser | Verified | Windows Python 3.12.14 / Pillow 12.3.0 installed runtime, native PNG/BMP, paired/manual browser, retained state and restart | Software; no device firmware |
| Node stdio → bridge MCP | Verified | Real stdio initialization/discovery/publication test client; generated configuration refers to installed adapter | Node 24.11.0 locally; interactive assistant client reproduction remains a beta gate |
| Source and download checks on Linux/Windows | Automated | Python 3.11/3.12 matrix and exact-artifact jobs; use linked run results for the released commit | Software |
| Docker AMD64 / ARM64 | Automated | Native architecture cold start, restart and replacement in CI; published image only after both checks | Container runtime, not a Raspberry Pi or physical-device claim |
| TRMNL BYOS | Experimental | Enrolled-device HTTP contract, image cache and opt-in frame policy | `trmnl` 800×480 or `trmnl_x` 1872×1404; no observed model/firmware run yet |
| Stock TRMNL Webhook Image | Experimental | PNG serialization, persisted queue, coalescing, retry, hourly quota and redacted receipts | Same profiles; no authenticated stock account/panel verification yet |
| Home Assistant integration | Experimental | Source tests and syntax; component version remains 0.1.0 | No live HA version recorded |
| ESPHome / OpenEPaperLink | Example only | Existing configuration fragments and documentation checks | Actual board, driver, pins and tag need verification |
| Inkplate / Kindle / custom sizes | Example only | Native renderer dimensions and grayscale | No bundled firmware/client verification |

Hardware claims require the exact panel and firmware, a real assistant result, normal refresh settings, observed output, restart and failure recovery. No physical latency is claimed by HTTP, CI or browser success. Animation defaults off; opt-in limits must be tested on the chosen panel. HACS installation and live cloud-dot eligibility remain unverified.
