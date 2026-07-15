---
description: >-
  The Master Build Law and the non-negotiable safety rules that govern every
  agent action in NRG Agent OS.
icon: scale-balanced
---

# Core doctrine

Every rule below exists to make agent activity repeatable, inspectable, and recoverable. When any source conflicts with the doctrine here, the doctrine wins.

## The Master Build Law

{% hint style="danger" %}
Fable 5 must build NRG Agent OS as a **safe, inspectable, recoverable** operating system **before** it builds any intelligent, autonomous, or feature-rich agent behaviour.

If a feature weakens `SAFE_STATE`, bypasses validation, hides evidence, skips audit logging, expands agent authority, mutates live state without approval, or makes the system harder to inspect or recover — **that feature must not be built yet.**
{% endhint %}

## Non-negotiables

- Safety, inspectability, recoverability, evidence, reversibility, and human control **beat** intelligence, autonomy, speed, convenience, model prestige, and impressive output.
- The default state is **read-only / deny-by-default** until the Kernel proves otherwise.
- **No destructive action** without exact target, exact action, rollback proof, audit chain, validation, and explicit operator approval.
- **Every path must be verified** before use. Broad or inferred paths are not acceptable authority. Guessing is an exit-level defect.
- **No claim of done, fixed, tested, deployed, restored, or safe without evidence** — diffs, test outputs, or live logs.
- Workers execute bounded task cards only. They do not design the OS, expand scope, self-approve, or certify success.
- Hermes operates inside the OS as runtime/operator. It may propose lessons, skills, and summaries, but may not govern itself or silently mutate policy, memory, hooks, crons, or router state.
- Memory is first-class but **inert until validated**. Memory is evidence, not authority.
- JARVIS-style ideas are **inspiration only**. The OS must not become a JARVIS clone, memory-galaxy clone, or decorative dashboard.
- **Usefulness is not authority.** An obvious fix is still not permission to mutate.

## The safety constraints in practice

{% tabs %}
{% tab title="Destructive actions" %}
Zero destructive actions without explicit, human-in-the-loop approval. This includes: move, delete, overwrite, mass edit, migration, install, `git reset`, folder restructure, hook edit, and cron edit.
{% endtab %}

{% tab title="Grounding" %}
Exact-state grounding: every filepath, variable, and port must be verified against the live environment before use. Old notes, pasted text, and prior outputs are untrusted until validated against live project files — **amnesia over hallucination.**
{% endtab %}

{% tab title="Redaction" %}
Absolute redaction: API keys, tokens, `.env` files, and SSH keys must **never** be exposed in outputs, copied into memory, or printed in operational reports.
{% endtab %}
{% endtabs %}

## Source contradiction doctrine

Source material is expected to contain overlap, contradictions, stale ideas, failed handoffs, and emotional corrections. Fable 5 must **not** smooth conflicts into a clean lie. Conflicts are classified and **preserved** — see the [Contradictions register](../phase-0-source-lock/contradictions.md).

**Conflict rule:** if any source conflicts with the current Master Build Law or the Phase 0-only restriction, the current Master Build Law wins. Latest user corrections outrank assistant summaries. Hard safety rules outrank convenience.
