---
description: >-
  The fixed phase order for building NRG Agent OS — armor before automation,
  kernel before dashboard.
icon: list-ol
---

# Build sequence

Fable 5 must plan and execute the build in this exact sequence. The governing rule is simple: **armor is built before automation, and the kernel is built before the dashboard.**

{% hint style="danger" %}
Phases may only be **planned** during Phase 0 — never implemented early. No secondary modules, dashboard interfaces, or background cron runners may be initialized until the kernel specifications are coded and frozen.
{% endhint %}

## The phases

{% stepper %}
{% step %}
### Phase 0 — Source Lock

Initialize the foundation: index and classify every source, preserve contradictions, and produce the completion report. Then **stop** and await operator acceptance. This is the only currently authorized phase — see [Phase 0](../phase-0-source-lock/overview.md).
{% endstep %}

{% step %}
### Phase 1 — Kernel

Define the boot sequence, task lifecycles, operating modes, agent contracts, and evidence schemas. Target files: `boot.sequence.md`, `task.lifecycle.md`, `definition-of-done.md`, `operating-modes.md`.
{% endstep %}

{% step %}
### Phase 2 — Memory

Establish trust levels and the Persistent / Scratch / Quarantine layout, with explicit promotion rules. See [Memory & trust](memory-and-trust.md).
{% endstep %}

{% step %}
### Phase 3 — Router & Permissions

Map intent, risk levels, model routing, skill assignment, and fallback schemas. Verify local ports and container gateway parameters before configuring the model gateway.
{% endstep %}

{% step %}
### Phase 4 — Validation

Build path/diff/claim verification, drift and hallucination detection, and OS self-tests.
{% endstep %}

{% step %}
### Phase 5 — Worker Task System

Design the task-card templates and the Fable Review Queue. See [Worker task cards](worker-task-cards.md).
{% endstep %}

{% step %}
### Phase 6 — Hermes Integration

Define the runtime contracts and lesson-proposal formatting for the daily operator.
{% endstep %}

{% step %}
### Phase 7 — Skills & Automations

Build the first safe, read-only skills (e.g. `filesystem.readonly-inventory`) and cron policies.
{% endstep %}

{% step %}
### Phase 8 — Control Surface

Design the operational UI dashboard — **only after** backend truth is established.
{% endstep %}
{% endstepper %}

## Current position

| Phase | Status |
|---|---|
| Phase 0 — Source Lock | **In progress — awaiting operator acceptance** |
| Phase 1 — Kernel | Next target (blocked until Phase 0 accepted) |
| Phases 2–8 | Planned only |

{% hint style="warning" %}
On operator acceptance of the Phase 0 Completion Report, the system freezes Phase 0 outputs and enters **WAIT mode**. Phase 1 may not begin until explicitly commanded.
{% endhint %}
