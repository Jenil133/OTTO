<!-- PDD SOURCE ARTIFACT · runtime prompt — STAGED (Define/Constrain done, Generate pending)
Consumed by:  Phase 4-D watch loop (Standing Watch, architecture D10) — one
              small-model call per check cycle: interval loop / Render cron →
              ONE Retriever fetch of the watched url → this prompt judges
              "condition met?". Not yet loaded by backend code.
Generates:    a strict-JSON verdict that flips the watch card and triggers
              Otto's proactive spoken alert — or silently sleeps.
Verified:     Saturday, Phase 4 (simulate-button test per phase-4.md exit
              criteria: watch triggers via simulate button if built).
Authored:     Sat 15:00-18:00 (phase-4.md Task D, stretch — droppable). The
              constraints below are frozen now so authoring is fill-in.
-->

# Watch-Compare — Standing Watch Condition Check (Phase 4 · Task D)

**Status: PDD Define/Constrain staged Friday; prompt body authored Saturday.**
A deliberate staged artifact — the contract below is binding on whatever text
lands in the TODO.

## Define

Given one fetched snapshot of the watched page and the user's stored
condition (`{url, condition, contact_mode}` from `POST /watch`), return a
single machine-parseable verdict: is the condition met right now?

## Constrain (frozen — the authored prompt MUST enforce all of these)

- **Strict JSON only** — exactly `{"met": <bool>, "reason": "<str>"}`, no
  prose, no fences, no extra keys (same strict-JSON discipline as planner.md
  and synthesizer.md).
- **Never guess** — `reason` must quote the exact observed value/text that
  justifies the verdict (e.g. `"price shown: $198"`), so the watch card and
  the spoken trigger can cite real evidence. No observable evidence → not met.
- **Ambiguity resolves to `met: false`** — the loop sleeps and re-checks; a
  false trigger interrupts the user, a missed check just waits N minutes.
  Asymmetric cost, asymmetric default.
- **Condition-only judgment** — evaluate ONLY the stored condition against
  ONLY the fetched content. No inference about trends, no "probably soon",
  no knowledge outside the snapshot.

## TODO — Saturday authoring (Ph4-D, ~15:00, stretch)

- [ ] TODO: final prompt text satisfying every constraint above.
- [ ] TODO: model choice (small/fast — this runs every N minutes on credit).
- [ ] TODO: input framing — how the page snapshot + condition are packed
      into the user message.
- [ ] TODO: wire into the `POST /watch` interval loop (or as a RocketRide
      fetch → compare → notify pipeline if Task C was NO-GO — phase-4.md).
- [ ] TODO: negative-path check — ambiguous page must return
      `{"met": false, ...}`, never a trigger.

## Validation (Phase 4 gate)

Simulate button flips the watch card watching → triggered and Otto speaks the
trigger with the quoted evidence. If time runs out, Standing Watch is cleanly
dropped — this file stays as the committed Define/Constrain record.
