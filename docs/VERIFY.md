# OTTO — Hour-Zero Verification Checklist (§13 · Phase 1 Task G)

**Window: Sat 9:00–9:45 · BLOCKING.** Person 3 + Person 4 split the lines
below; Person 2 + 3 do the RocketRide skim. All decisions announced to the
room at 9:45.

> **Rule: Nothing is guessed — anything unverifiable stays flagged.**
> Every line ends checked with an answer, or explicitly `unknown — fallback chosen`.

---

## Person 3

### Retriever

- [ ] API shape — submit/poll or webhook? · answer: ___
- [ ] Concurrency limit on hackathon credits (need 3 parallel sessions)? · answer: ___
- [ ] Is a live session view embeddable in our UI? · answer: ___

### TokenRouter  ($50 credit in hand — confirmed at the event)

- [x] Base URL? · answer: **https://api.tokenrouter.com/v1** — OpenAI-compatible; just switch base_url + one key. Operated by Artemis Tokenrouter Inc. **Verified live.**
- [x] Exact Kimi K3 model string? · answer: **`moonshotai/kimi-k3`** — works, but see the planner benchmark below; not the model we ship.
- [x] JSON-mode flag (name + how to set)? · answer: **`response_format={"type":"json_object"}`** — standard OpenAI shape, **confirmed working live** on both Kimi and Gemini.
- [ ] Context-caching flag (name + how to set)? · answer: ___ (not documented on the model page; "Cache Read" pricing implies it exists. `usage.prompt_tokens_details.cached_tokens` was non-zero on a MiniMax reply, so caching may be automatic. Set `TOKENROUTER_CACHE_FLAG` if a header turns up.)

### Planner model benchmark — measured live, same key + same prompt

| model | latency | plan |
|---|---|---|
| **google/gemini-3.5-flash-lite** | **2.8s** | 3 subtasks ✅ **shipping this** |
| openai/gpt-5.4-mini | 3.9s | ⚠️ 1 subtask — breaks the fan-out visual |
| x-ai/grok-4.1-fast | 7.6s | 3 subtasks |
| z-ai/glm-5-turbo | 10.4s | 3 subtasks |
| moonshotai/kimi-k3 | 28.0s | 3 subtasks (reasoning model) |

Kimi K3 plans correctly but spends reasoning tokens on a task that doesn't need
them; D2 budgets this stage at 5–10s. Gemini flash-lite verified **5/5 runs at
2.6–2.9s**, identical allowlist targets, and still returns a Clarification on an
ambiguous ask. Swap = one env var (`PLANNER_MODEL`), zero code change.

### Gotchas found live (cost us debugging time — don't re-learn these)

- **Kimi K3 rejects `temperature`** unless it is exactly `1` → HTTP 400 `"invalid temperature: only 1 is allowed for this model"`. We omit the param.
- **MiniMax M3 prepends an un-fenced `<think>…</think>` block** before its JSON. Strip it before parsing or every synthesis silently falls back.
- **Reasoning models need generous timeouts** — 30s produced intermittent `ReadTimeout` on ~40% of Kimi planner calls, surfacing as a bogus "could you rephrase that?".

### MiniMax  (routing through TokenRouter — same $50 key)

- [x] Endpoint (chat/completions URL)? · answer: **via TokenRouter** `https://api.tokenrouter.com/v1/chat/completions` (TokenRouter catalogs MiniMax). Native MiniMax only if using a separate MINIMAX_API_KEY.
- [ ] Exact MiniMax model string? · answer: ___ (TokenRouter models page, MiniMax row → set `MINIMAX_MODEL`)
- [ ] Image-input format (for screenshot recovery reads)? · answer: ___ (OpenAI-style `image_url` blocks assumed; confirm)

> **Decision:** TokenRouter is the LLM gateway for BOTH planner (Kimi K3) and
> synthesizer (MiniMax M3). One key, automatic multi-provider failover. To go
> live now: set `TOKENROUTER_API_KEY`, `KIMI_MODEL`, `MINIMAX_MODEL` in
> `backend/.env`, leave `OTTO_MOCK` empty. Retriever stays mock until Saturday.

---

## Person 4

### ElevenLabs

- [ ] Agent tool/webhook mechanism (how run_task() is wired)? · answer: ___
- [ ] **Timeout ceiling** on a tool call (our pipeline runs 60–90s → picks the D3 pattern)? · answer: ___
- [ ] Widget embed vs React SDK — which path? · answer: ___

### Respan

- [ ] Which providers route through it (Kimi? MiniMax?)? · answer: ___

### Band

- [ ] SDK language(s) available? · answer: ___
- [ ] Minimal post-message call (paste the one-liner)? · answer: ___

### mem0

- [ ] Hosted vs self-host decision? · answer: ___
- [ ] add call (paste the one-liner)? · answer: ___
- [ ] search call (paste the one-liner)? · answer: ___

---

## RocketRide GO/NO-GO — Person 2 + Person 3 (10 min skim)

**GO only if ALL THREE hold** (ambiguity = NO-GO; fallback = Standing Watch
as the RocketRide pipeline, Phase 4):

- [x] JSON schema is clean? · answer: **YES.** Export produces a plain
  `.pipe` / `application/json` file: `{project_id, components: [{id,
  provider, config, ui, input}, ...]}`. Verified on a real pipeline
  (`hello-inspect`, built off the "RocketRide Wave Agent" template) — e.g.
  `{"id":"llm_openai_1","provider":"llm_openai","config":{"profile":
  "openai-5-2",...}}` and the HTTP tool node's config (allowGET/POST/PUT/
  PATCH/DELETE, `urlWhitelist: []`, rate limits). Structured, readable, no
  proprietary opacity.
- [x] Steps can call an external tool / custom function? · answer: **YES,
  clearly.** The node palette's TOOL category includes **HTTP Request**
  (arbitrary external URL, all methods, `urlWhitelist: []` = unrestricted
  by default), **Python** (custom code), and **MCP Client** — three
  independent arbitrary-execution paths. Full TOOL list also has Mem0,
  GitHub, Slack, Google Sheets/Docs/Drive/Calendar, Gmail, Exa/Tavily
  search, Firecrawl, Git, File System, Apify, Chart.js, and more.
- [x] Custom model base URL is configurable? · answer: **YES, via one
  specific node type.** The branded `OpenAI` node is locked (Node Name /
  preset Model dropdown / API key only — no base URL). The
  **"OpenAI-Compatible API"** node exposes an explicit **"Base URL \*"**
  field + free-text Model + Tokens + API key — meaning any OpenAI-
  compatible gateway (TokenRouter included) can be pointed at from a
  RocketRide pipeline. Ollama likely implies a custom host too, untested.

**decision: GO — recorded Sat Jul 25, ~12:40.** All three verified with
concrete evidence (JSON snippet, node list, field name), not guessed.

**Scope decision (not a spec requirement, a judgment call):** the main
brain (planner → fan-out → synthesizer) is NOT being ported to RocketRide.
It is already live-verified twice on the deployed Render backend (38/38
tests, real 3-agent runs, e.g. `req_ffccc683` in 23s) — replacing working,
tested infrastructure this late for a sponsor integration is exactly the
kind of scope creep the master plan's cut order warns against. RocketRide's
GO instead unlocks **Standing Watch (Phase 4-D, currently unbuilt)**: an
HTTP Request tool step (fetch the watched page) → an OpenAI-Compatible LLM
step (base URL = TokenRouter, same key already live) that judges "condition
met?" — the exact shape of the watch-compare prompt already stubbed in
`backend/prompts/watch-compare.md`. Honest sponsor use: earned, not forced.
