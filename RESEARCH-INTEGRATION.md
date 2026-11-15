# FieldMind with integrated public-source research

Development branch: `codex/research-integration` in this local checkout. No deployment, main-branch merge, data migration or persistence replacement.

## Start

Requires Python 3.12, Git and a Linux/macOS shell. From the extracted folder:

```
./start-fieldmind.sh
```

The first run installs pinned Python dependencies, downloads Chromium and clones pinned SearXNG. Open **http://127.0.0.1:8765** in your browser. Keep the terminal running. Installing dependencies requires public network access. This prepared workspace can instead run:

```
FIELDMIND_SEARCH_SOURCE=/workspace/fieldmind-research-engine-eval/upstream/searxng \
  /workspace/fieldmind-research-engine-eval/.venv/bin/python research/server.py
```

Opening index.html directly preserves existing functionality but cannot start the Python worker. The research service is local to the computer running it, not a remote mobile backend. An HTML download alone cannot include or execute Crawl4AI. On a phone, the loopback URL points at the phone; remote/mobile service access requires a separately designed authenticated backend and deployment, neither included here. Browser storage at this local origin is separate from the hosted application's storage. Existing hosted records are not automatically imported or moved.

## Use

Open one business, tap **Research**, then **Start public research**. Review the six-question draft, qualified source excerpts, retrieval dates and source links. Tap **Save reviewed brief to this record** to attach it to the existing Overview and Sources views. Discarding saves nothing. No bulk research runs automatically after list import.

Only name, street address, city and an opaque per-request reference are sent to the service. Utility account numbers, MIMO historical fields, device information, notes and list membership are not sent. Suppressed records cannot start or receive a research attachment. Identity/suite or note changes during a job prevent stale attachment. Existing adjudicated profiles/decisions are preserved. Research cannot approve prospects, release suppression or create eligibility. It attaches publication-backed leads to the deliberately selected record; it does not accept an identity relationship.

This version uses deterministic extraction, with live SearXNG discovery and Crawl4AI retrieval. It does not claim Claude model reasoning. Current occupant, five distinct decision authorities and current HVAC remain unknown unless established separately. Undated source leads display as current-applicability unknown; dated owner context remains historical. The worker's name-matching primary-site heuristic is conservative and will miss differently named domains; other retrieved sources may still yield qualified leads. No data migration occurs.

## Controls and limits

Loopback binding, strict Host/Origin checks, a random HttpOnly SameSite session cookie, a custom same-origin API header, JSON-only allowlisted inputs, one active job, a 180-second job deadline and private-network browser request screening are included. These are a local companion boundary, not server-enforced multi-workspace permissions or cloud authentication. Do not expose the server on a public interface. Local browser Chrome runs with --no-sandbox in this prepared environment; it uses a separate per-job profile, not a personal logged-in profile. DNS screening does not provide a full network sandbox or a DNS-rebinding guarantee.

Raw public captures, request target, logs, and source hashes are stored under ignored `research/runs/<job-id>/` for audit. Complete API job entries expire after an hour; run directories do not auto-delete. Stop the service and delete run directories when no longer needed. Saved briefs continue using the application's existing storage and backup behavior. Local save errors are checked and leave the draft for retry; cloud failure cannot guarantee the remote write did not complete, so verify before retrying.

No paid research APIs or model inference are used. Existing compute and human review have costs. Search engines can rate-limit or CAPTCHA; failures are shown rather than replaced with pasted text. Semantic contradictions, source freshness, ambiguous suite identity and general decision-authority reasoning still need review. This integration is not evidence of broad benchmark accuracy.

## Validation

`npm ci` then `FIELDMIND_CHROMIUM=/usr/bin/chromium npm test` runs app/domain/security/integration tests. Python service boundary tests: `research/.venv/bin/python -m unittest discover -s research/tests -v`. `node tests/live-research-proof.cjs` deliberately performs a single live public-business proof and must be invoked explicitly; it is excluded from routine tests. It seeds only synthetic local app identity/history and uses independently selected public Videri business information. No Brian records are included.

## Licenses

This product includes software developed by UncleCode (https://x.com/unclecode) as part of the Crawl4AI project (https://github.com/unclecode/crawl4ai). Crawl4AI's exact attribution/license terms require review before redistribution. SearXNG is AGPL-3.0-or-later; use the pinned upstream source and comply with applicable source obligations. Python dependency pins are recorded in research/requirements.lock. No dependency binaries or third-party source packages are bundled in the application download.
