# Coordination protocol

How Tree and the Mac session coordinate on this repo. The board in COORDINATION.md is the public summary; this folder is the working kit.

## Files

- COORDINATION.md (repo root): the board. Shared. End-of-file appends only.
- coordination/tree-status.md: Tree's status. Only Tree writes it.
- coordination/mac-status.md: the Mac session's status. Only the Mac session writes it.
- coordination/handoffs.md: the handoff log. Append-only, either agent may append its own entries.

## Claim format

Claim before you build. A claim is one block, on the board or in your status file:

```
Task: <short id, e.g. mcp-wiring-test>
Owner: Tree | Mac session
Branch: tree/<slug> | rene/<slug> | main (coordination files and Rene-approved fixes only)
Areas: <files or folders>
Status: CLAIMED
Started: 2026-10-24 ~11:24 AM PT
```

One owner per file area at a time. If you are not sure an area is free, it is not free.

## Status vocabulary

- CLAIMED: claimed, not started yet.
- WIP: actively working.
- BLOCKED: cannot proceed; say what is missing and whose move it is.
- READY: a setup or verification job is finished and the other agent can build on it. Always with a timestamp and evidence.
- DONE: finished and merged (or not code). Always with evidence.

## Handoff format

When work passes between agents, append one entry to coordination/handoffs.md:

```
## 2026-10-24 ~12:05 PM PT, Tree -> Mac session: <task id>
Done: <what was done, plainly>
Evidence: <verbatim test result, PR link, or commit sha>
Next: <what happens now>
Owner now: Tree | Mac session | Rene
```

## Rules

1. Each agent writes only its own status file. Never edit the other agent's status file; if their status looks stale, say so in a handoff entry instead.
2. Shared files (COORDINATION.md, this file, handoffs.md) get end-of-file appends only. Never rewrite, reorder, or delete earlier content.
3. Test evidence rule: no READY and no DONE without the verbatim test result or a link to it. "Tests pass" without the output or a link does not count.
4. Small PRs, branch names tree/<slug> or rene/<slug>, never force-push. Main is for coordination files and Rene-approved fixes only.
5. Every commit carries the trailer: Signed-off-by: Rene Turcios <95189389+CloudCorpRecords@users.noreply.github.com>
6. No em dashes or en dashes anywhere.

## Ready protocol

When an agent finishes a setup or verification job: write READY plus the timestamp in your own status file, append a handoffs.md entry with the evidence, and Rene relays the word to the other agent. The other agent confirms by reading the status file and the handoff entry, not by asking.
