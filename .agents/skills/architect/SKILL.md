---
name: architect
description: Plan complex, cross-cutting, or architecturally meaningful Guilty Gear Coach changes before implementation, resolving decisions and producing an approval-ready blueprint.
---

# Architect

Use this skill before implementation when a change crosses important boundaries, introduces a durable workflow, changes architecture, or carries meaningful privacy, ownership, data, or analysis risk. This is a planning session: do not modify application or documentation files while using it.

## Establish the Current State

Read `AGENTS.md`, `README.md`, and the relevant context files in the order defined by `AGENTS.md`. Inspect the smallest useful set of existing code and tests.

Confirm:

- what is implemented versus planned;
- the current roadmap position in `context/progress-tracker.md`;
- the relevant acceptance criteria in `context/build-plan.md`;
- the files and boundaries that already own the behavior.

Treat code and verification evidence as the source of truth for implementation status. Report stale or conflicting documentation rather than silently choosing a convenient version.

## Resolve Only Decisions That Change the Build

Do not force a fixed number of vocabulary questions. Define or confirm terms only when an ambiguity would change behavior, persistence, API contracts, evidence labels, or user expectations.

Surface unresolved decisions in impact order. For each one:

1. explain the decision and why it matters;
2. recommend an approach with its main tradeoff;
3. ask for input only when the answer cannot be safely inferred from approved context.

Do not ask the developer to repeat information already documented.

When relevant, explicitly reason about:

- ownership through `Replay -> Match -> User` and inaccessible-resource behavior;
- frontend, route, schema, model, and service responsibilities;
- PostgreSQL and R2 as separate resources, including partial failure and recovery;
- private replay media, consent, retention, and external-provider access;
- measured observations, inferred boundaries, deterministic findings, and AI coaching hypotheses as distinct claims;
- `unknown` visual evidence versus `failed` technical processing;
- background-work idempotency, retries, leases, and durable status;
- subprocess timeouts, temporary-file cleanup, and safe public errors;
- UI loading, empty, success, failure, focus, and accessibility behavior;
- installed dependency versions and approved library guidance;
- isolated disposable databases for mutating integration tests.

Use only the items that genuinely affect the proposed feature.

## Produce the Blueprint

When the meaningful decisions are resolved, say:

```text
Blueprint ready.
```

Then provide:

```markdown
## Implementation Plan — [Feature Name]

### Outcome
[What will exist and what remains out of scope.]

### Current-state evidence
[What already exists, the roadmap stage, and any relevant discrepancy.]

### Terms and decisions
[Only terms that needed clarification and decisions that affect implementation.]

### Files and responsibilities
[Expected files or modules and what each owns.]

### Data and execution flow
[How data enters, is authorized, transformed, persisted, returned, or displayed.]

### Failure, privacy, and evidence handling
[Relevant partial failures, uncertainty, provenance, consent, and recovery behavior.]

### Implementation sequence
[Small, ordered, verifiable steps.]

### Verification
[Focused tests, broader checks, environment limits, and manual validation.]

### Documentation
[Only context or progress files that the completed change would actually alter.]

### Assumptions and open decisions
[Anything not confirmed that could still affect the result.]
```

Keep the plan proportional to the feature. Do not introduce speculative layers, dependencies, or future schema that the approved slice does not require.

## Approval Boundary

Present the blueprint and wait for explicit approval before implementation. Approval of the plan authorizes only the described scope; it does not authorize destructive infrastructure operations, production changes, external media disclosure, or unrelated cleanup.
