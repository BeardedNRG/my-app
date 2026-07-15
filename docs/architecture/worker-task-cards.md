---
description: >-
  The minimal-verification-gate task card that bounds every worker action —
  exact file, exact action, mandatory proof.
icon: id-card
---

# Worker task cards

Workers (Codex, GPT-5.5, Gemini, local models) never design; they execute. The **task card** is the contract that bounds each worker action: it names the exact file, the exact allowed action, the forbidden actions, and the verification the worker must produce before claiming success.

## The template

```markdown
# TASK CARD ID: [Generated]
**Target Model:** [Codex/Gemini/Local]
**Objective:** [Strict single-sentence goal]

### ALLOWED SCOPE
- **Target File:** /path/to/exact/file.js
- **Allowed Action:** [e.g., READ / APPEND / EDIT-FUNCTION]
- **Forbidden Actions:** Restructuring, deleting dependencies.

### VERIFICATION REQUIREMENT
You must output the exact terminal command used to verify this change
(e.g., `npm run test:target`) and capture the output.
Do not output "Done" without the stack trace.
```

## Why each field exists

| Field | What it prevents |
|---|---|
| **Target File** (exact path) | Broad or inferred paths being treated as authority. |
| **Allowed Action** | Scope creep beyond the single assigned operation. |
| **Forbidden Actions** | Restructuring and dependency deletion sneaking in under a small task. |
| **Verification Requirement** | Unverified "done" claims — proof must accompany the result. |

{% hint style="danger" %}
A worker **cannot** invent architecture, alter permissions, expand scope, or touch forbidden files. If a task appears to require any of these, the worker stops and returns to Fable rather than improvising.
{% endhint %}

## The review queue

Completed task cards do not merge themselves. They flow into the **Fable Review Queue**, where the architect checks the evidence against the acceptance criteria before anything is accepted into the project. This is the Final Review Gate in practice — see [Roles & the Barbell](../overview/roles.md).

{% hint style="info" %}
The task-card system is formally built in **Phase 5** of the [build sequence](build-sequence.md), but the template above is the doctrine that governs it from the start.
{% endhint %}
