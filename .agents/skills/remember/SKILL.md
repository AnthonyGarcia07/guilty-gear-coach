---
name: remember
description: Save or restore non-sensitive Guilty Gear Coach handoff context for incomplete multi-session work, unresolved decisions, or hard-won diagnostics; skip trivial or fully documented tasks.
---

# Remember

Use this skill only when work is incomplete across sessions, an unresolved decision materially affects the next step, or diagnostic context would be costly to reconstruct. Do not create memory for trivial tasks or completed work already represented by the repository and `context/progress-tracker.md`.

Invocation:

```text
/remember save
/remember restore
```

If the mode is omitted, ask which mode the developer wants.

## Security Boundary

Never persist or repeat secrets, credentials, tokens, passwords, cookies, authorization headers, connection strings, private object URLs, private keys, real user replay data, or identifying media details. Replace a necessary reference with a descriptive placeholder such as `[REDACTED_R2_CREDENTIAL]`. If uncertain, omit it.

Memory is an ephemeral handoff, not a second source of truth. Do not copy decisions already maintained in the context files or implementation details that are obvious from code.

## Save Mode

Before writing:

1. read `AGENTS.md` and `context/progress-tracker.md`;
2. confirm the work warrants a handoff;
3. verify that root-level `memory.md` is ignored by Git;
4. inspect any existing `memory.md`.

If `memory.md` is not ignored, do not create or overwrite it. Tell the developer and ask for explicit approval to add the exact ignore rule before saving. Never place secrets in the file even if it is ignored.

If an existing memory would be overwritten, summarize it in one line and wait for confirmation.

Capture only:

- the approved in-flight objective and its scope;
- files changed or partially changed;
- verified results and commands already run;
- unresolved failures or blockers with evidence;
- temporary decisions not yet promoted to canonical context;
- the precise next action and any approval still required.

Do not claim tests passed unless they were run in the recorded environment. Do not store planned product capabilities as implemented.

Use this compact format:

```markdown
# Memory — [Work item]

Last updated: [date and time]

## In-flight objective
[Approved outcome and boundaries.]

## Current working state
[Changed files, completed portions, partial work, and known failures.]

## Verification already performed
[Commands and results, including anything not verified.]

## Temporary decisions and diagnostic evidence
[Only information not already canonical elsewhere.]

## Next action
[One concrete starting action.]

## Open decisions or required approval
[Only unresolved items.]
```

Run a final secret and privacy review before writing. After saving, state that `memory.md` was updated and summarize the next action.

## Restore Mode

1. Read `memory.md` first. If it does not exist, say so and stop.
2. Read `AGENTS.md`.
3. Read `context/progress-tracker.md`.
4. Read only the additional context, plan, code, and tests needed to validate the handoff, following the order in `AGENTS.md`.
5. Check the current diff or repository state when the memory refers to uncommitted work.

Do not broadly scan instruction files from other tools unless the developer identifies one as part of the handoff. Never surface a secret found while restoring; redact it and warn that it should be removed from the source.

Compare memory with the repository and canonical context. Call out stale or contradictory handoff details rather than treating memory as authoritative.

Summarize:

```markdown
Memory restored.

**In-flight objective:** [scope]
**Current repository state:** [what is actually present]
**Verified so far:** [evidence]
**Next action:** [specific action]
**Gaps or conflicts:** [anything stale, unclear, or missing]
```

Do not resume implementation automatically. Wait for the developer to confirm or correct the restored state.

## Maintenance Rule

After the handoff is no longer needed, ask before deleting `memory.md`. Never remove it automatically. Durable product decisions belong in the appropriate context file, and completed implementation status belongs in `context/progress-tracker.md`.
