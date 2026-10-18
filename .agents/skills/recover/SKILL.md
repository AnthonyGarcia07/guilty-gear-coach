---
name: recover
description: Diagnose a failed or repeatedly unsuccessful Guilty Gear Coach implementation before further changes, then choose a targeted correction, clean-context recovery, or architectural rethink without discarding work.
---

# Recover

Use this skill when the developer invokes `/recover` or when the same problem remains after one evidence-based corrective attempt. Its purpose is to stop speculative patching, identify the failure mode, and preserve the developer's work.

A clean-context recovery never means `git reset`, deleting files, reverting changes, or overwriting user work. No recovery mode authorizes destructive action.

## Gather Evidence

Before proposing another change:

1. read `AGENTS.md` and the relevant context;
2. inspect the exact error, logs, failing test, diff, and smallest relevant code path;
3. confirm expected behavior versus observed behavior;
4. identify what was already attempted and what evidence changed afterward;
5. verify environment-sensitive facts such as installed versions, configuration shape, service availability, and test isolation when relevant.

Ask only for evidence that cannot be inspected. Redact credentials, private object URLs, and user replay data.

For replay analysis, distinguish product uncertainty from technical failure:

- `unknown` means processing succeeded but visual evidence was inconclusive;
- `failed` means extraction or detection failed technically.

An `unknown` result is not a defect merely because it lacks a definitive classification.

## Classify the Failure

Choose the best-supported mode and explain the evidence.

### 1. Targeted defect

Use when one code path or configuration has a specific, testable root cause and the surrounding approach remains valid.

State:

- the observed symptom;
- the root cause and supporting evidence;
- why the earlier attempt did not resolve it;
- one focused correction;
- the test or observation that would prove the correction.

Stay within the already approved task. If the correction requires new scope, dependency changes, database mutation, external media disclosure, or destructive action, obtain explicit approval first.

If the focused correction fails, stop and re-diagnose from the new evidence. Do not chain speculative fixes.

### 2. Contaminated implementation or session

Use when repeated patches have obscured the original problem, introduced interacting changes, or made the current reasoning unreliable.

Do not revert automatically. Instead:

- inventory the exact changed files and current diff;
- identify verified-good work, uncertain work, and known failures;
- restate the original intended outcome;
- record approaches that failed and evidence learned;
- recommend pausing implementation and continuing from a clean conversational context.

Provide a concise handoff note. Suggest `/remember save` only when the work is incomplete, spans sessions, or contains hard-won diagnostic context. The developer decides whether any code should later be reverted or replaced.

### 3. Wrong approach or architecture

Use when the implementation follows an incorrect requirement, library contract, ownership model, evidence model, or system boundary, so local fixes cannot make it correct.

State:

- the incorrect assumption;
- the repository or documentation evidence that contradicts it;
- what can be retained;
- what would need replacement;
- the corrected approach and its tradeoffs.

Do not rebuild during the diagnosis. For a complex or cross-cutting replacement, recommend a new `/architect` planning pass and wait for approval.

## Project-Specific Checks

Apply only those relevant to the failure:

- ownership must be enforced through `Replay -> Match -> User`;
- routes own HTTP concerns while services own reusable processing and storage logic;
- PostgreSQL rows and R2 objects can fail independently;
- temporary media must be cleaned up and FFmpeg/`ffprobe` calls must retain timeouts and safe public errors;
- measured observations, deterministic findings, and AI coaching hypotheses must not be conflated;
- provider failure must not invalidate deterministic results;
- frontend requests must leave loading state on rejection;
- database-mutating tests require a verified disposable database.

## Recovery Report

Return:

```markdown
## Recovery diagnosis — [problem]

**Mode:** Targeted defect | Contaminated implementation/session | Wrong approach/architecture

**Evidence**
- [Observed facts, files, logs, or tests]

**Root cause or wrong assumption**
[What the evidence supports, including uncertainty.]

**Recommended next action**
[One bounded action and how it will be verified.]

**Work preservation**
[What remains untouched, reusable, or needs a handoff.]

**Approval needed**
[Only permissions or decisions not already granted.]
```

Separate confirmed facts from hypotheses. Do not modify files during the diagnosis unless the developer has explicitly asked for a bounded recovery change and the root cause is supported by evidence.
