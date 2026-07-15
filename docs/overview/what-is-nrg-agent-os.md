---
description: >-
  The paradigm behind NRG Agent OS — a control plane for governing AI work
  safely across local and cloud models — and an explicit list of what it is not.
icon: circle-question
---

# What is NRG Agent OS

NRG Agent OS is a full-stack agent operating system for controlling AI work **safely** across local and cloud models. It lets capable models and agents enter a project, understand the source state, receive bounded tasks, operate under permissions, produce evidence, pass validation, record audit history, and expose truthful operational state to the operator.

## The system paradigm

{% hint style="success" %}
**The OS is the asset.** Large language models are treated as disposable computational engines. The permanent lawbook of the system resides entirely in its contracts, interfaces, and transaction-isolation structures.
{% endhint %}

- **Model-agnostic** — Fable 5, Hermes, Codex, GPT-5.5, Gemini, Ornith/local models, and future models are replaceable engines. The OS contracts are the stable machine bay.
- **Local-first** — the system is designed to run natively, without vendor lock-in, with a local fallback model always available behind the gateway.
- **In-session orchestration** — execution loops run within a single master session using cold-context subagents. External scripts and driver loops are deprecated from the core architecture.

## What it must include

The final product spans the full stack: a frontend/control surface, backend/API, kernel/control layer, agent runtime, model gateway, memory layer, router, validation system, audit/event log, worker task-card system, skill registry, automation/hook/cron policy, recovery rails, versioning/migration policy, and an operator-grade dashboard.

## What it is not

The entire source pack converges on one corrected truth — this matters because much of the early material drifted toward each of these:

| NRG Agent OS is **not**... | Because... |
|---|---|
| A model | Models are disposable engines behind the gateway. |
| A dashboard | The dashboard is the last layer, built only after backend truth exists. |
| Hermes | Hermes is the runtime operator *inside* the OS, not the OS itself. |
| Fable | Fable is the architect *of* the OS while available, not the OS. |
| JARVIS / a knowledge galaxy | JARVIS-style ideas are inspiration only, never architecture to copy. |
| A folder of agents freelancing | Agents operate under contracts, permissions, and validation. |

{% hint style="info" %}
The pack is **architecturally rich but operationally immature** — strong doctrines and repeated consensus, but many files are drafts, transcripts, and inspiration layers. The right move is not more ideation and not immediate dashboard construction. It is to convert the source material into a source-locked foundation with hard contracts, schemas, auditability, and phased proof gates. That is [Phase 0](../phase-0-source-lock/overview.md).
{% endhint %}
