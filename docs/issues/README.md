# OTTO — PDD Issue Pack

Under PDD, **issues ARE prompts**: each file below is (a) a GitHub issue pasted verbatim
Saturday morning and (b) the prompt handed to a coding agent (or `pdd change ISSUE_URL`).
The DONE issues are the retroactive audit trail for work already verified in this repo —
every evidence line in them is checkable by opening the cited file or running the cited command.

| # | Issue | Phase | Status | Owner |
|---|---|---|---|---|
| 01 | [UI shell + mock engine + golden replay](issue-01-ui-shell-mock-run.md) | 1 | **DONE** | Person 1 + Person 2 |
| 02 | [Text spine end-to-end over the real WebSocket](issue-02-text-spine-e2e.md) | 2 | **DONE** | Person 2 (+ P1, P3) |
| 03 | [Select the planner model by measured benchmark](issue-03-planner-model-selection.md) | 2 | **DONE** | Person 3 |
| 04 | [Fan out all plan subtasks to parallel agents](issue-04-fanout-three-agents.md) | 3-A | OPEN | Person 2 |
| 05 | [Wire the ElevenLabs voice loop](issue-05-voice-loop-elevenlabs.md) | 3-B | OPEN | Person 1 + Person 2 |
| 06 | [Flip the Retriever live + score the allowlist](issue-06-retriever-live-allowlist.md) | 2-B | OPEN | Person 3 |
| 07 | [mem0 memory loop + "otto knows" pills](issue-07-memory-mem0.md) | 4-A | OPEN | Person 4 |
| 08 | [Standing Watch with simulate-trigger](issue-08-standing-watch.md) | 4-D | OPEN | Person 3 |

## Saturday flow (repo goes public in the morning)

1. After `git init` + push, paste each file above verbatim as a GitHub issue; DONE issues are filed and immediately closed — they are the back-propagated record the PRs link to.
2. Label OPEN issues `pdd-change` (or `pdd-generate` for greenfield) so the PDD GitHub App routes them; or run `pdd change <ISSUE_URL>` directly.
3. Bugs found live go through `pdd bug` → `pdd fix --protect-tests` — never weaken a test to make a fix pass, and never paste a key into an issue, prompt, or commit.
