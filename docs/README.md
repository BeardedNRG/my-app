---
description: >-
  A local-first, model-agnostic control plane that governs agents, models,
  memory, permissions, validation, and recovery — the OS is the asset, models
  are disposable engines.
icon: shield-halved
layout:
  title:
    visible: true
  description:
    visible: true
  tableOfContents:
    visible: true
---

# NRG Agent OS

**NRG Agent OS** is a structured, model-agnostic, local-first operating layer that governs and isolates distributed AI execution loops. The goal is that every agent action is **repeatable, inspectable, and recoverable** — no agent may self-authorize system mutations, change policy, or perform freelance filesystem operations.

{% hint style="info" %}
**The OS is the asset. Models are disposable engines.** The permanent lawbook of the system lives in its contracts, interfaces, and transaction-isolation structures — not in any single model. Fable 5, Hermes, Codex, Gemini, and local fallbacks are all replaceable.
{% endhint %}

## The corrected core truth

NRG Agent OS is **not** a model, a dashboard, Hermes, Fable, JARVIS, or a folder of agents freelancing. It is a **control plane** that governs agents, models, memory, permissions, validation, automation, recovery, skills, hooks, crons, logs, and operator visibility.

Safety, inspectability, recoverability, evidence, reversibility, and human control **beat** intelligence, autonomy, speed, convenience, and impressive output.

## Start here

<table data-view="cards">
  <thead>
    <tr><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>What is NRG Agent OS</strong></td>
      <td>The paradigm, the corrected intent, and what the system is not.</td>
      <td><a href="overview/what-is-nrg-agent-os.md">what-is-nrg-agent-os.md</a></td>
    </tr>
    <tr>
      <td><strong>Core doctrine</strong></td>
      <td>Master Build Law, the non-negotiables, and safe-state defaults.</td>
      <td><a href="overview/core-doctrine.md">core-doctrine.md</a></td>
    </tr>
    <tr>
      <td><strong>Roles &#x26; the Barbell</strong></td>
      <td>Fable, Workers, Hermes, and Ornith — who is allowed to do what.</td>
      <td><a href="overview/roles.md">roles.md</a></td>
    </tr>
    <tr>
      <td><strong>Architecture</strong></td>
      <td>The eight system layers, memory trust zones, and the phased build sequence.</td>
      <td><a href="architecture/system-layers.md">system-layers.md</a></td>
    </tr>
    <tr>
      <td><strong>Phase 0 — Source Lock</strong></td>
      <td>The first and only authorized phase: index, classify, preserve contradictions, report.</td>
      <td><a href="phase-0-source-lock/overview.md">overview.md</a></td>
    </tr>
    <tr>
      <td><strong>The Console</strong></td>
      <td>The full-stack app that runs Phase 0 Source Lock and produces the artifacts.</td>
      <td><a href="console/overview.md">overview.md</a></td>
    </tr>
  </tbody>
</table>

## Current system state

| Field | Value |
|---|---|
| Version | <code class="expression">space.vars.version</code> |
| Systemic mode | <code class="expression">space.vars.mode</code> |
| Risk baseline | <code class="expression">space.vars.risk_baseline</code> |
| Active phase | Phase 0 — Source Lock |

{% hint style="warning" %}
The system is in **Phase 0 Source Lock** and awaits operator acceptance. No Kernel, Memory, Router, Validation, Audit, Workers, Skills, Recovery, or live-operation components are authorized until Phase 0 is accepted. See [Scope lock](phase-0-source-lock/scope-lock.md).
{% endhint %}
