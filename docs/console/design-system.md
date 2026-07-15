---
description: >-
  The operational, mission-control design language of the Console — Swiss-grid
  discipline, dense dark surfaces, and status codification over spectacle.
icon: palette
---

# Design system

The Console's visual language is **operational, not cinematic**. Dashboard beauty is secondary; the primary question of any screen is whether the operator can *dispatch, observe, intervene, and review*. The aesthetic fuses Swiss typographic discipline with a mission-control console.

## Brand attributes

`forensic` · `disciplined` · `mission-control` · `operator-first` · `high-signal / low-noise` · `non-cinematic (explicitly NOT JARVIS)` · `ADHD-friendly (clear, direct, structured)`

## What to avoid

{% hint style="danger" %}
- No neon cyberpunk.
- No cinematic HUD glow overload.
- No purple gradients.
- No flashy animated backgrounds.
- No centered reading layouts.
{% endhint %}

Instead: Swiss/International grid discipline, mission-control status codification with dense tables, modern enterprise dark mode (soft blacks, layered surfaces), and subtle industrial grain.

## Typography

| Role | Family | Usage |
|---|---|---|
| **Heading** | Space Grotesk (600–700) | Geometric but serious; reads like modern ops tooling. |
| **Body / UI** | IBM Plex Sans (400–600) | Neutral, legible for dense tables and long metadata. |
| **Monospace** | IBM Plex Mono (400–600) | SHA-256 hashes, filenames, ranks, IDs, code-like claims. |

{% hint style="info" %}
Avoid ALL-CAPS paragraphs. Reserve caps for short status chips only — `WAIT`, `LOCKED`, `PRESERVED`.
{% endhint %}

## Density strategy

The default layout is **dense**, with deliberate escape hatches so density never becomes noise:

- Collapsible sections
- Resizable panels
- A drawer for source detail
- Sticky table headers with column-visibility toggles

## Status codification

Because the system's whole purpose is inspectability, **failures and blockers must be the most visible thing on screen.** Status is codified consistently across the surface — parse status, authority tier, contradiction severity, and operating mode each read as a distinct, scannable chip rather than buried prose.

{% hint style="success" %}
The design system exists to communicate **status, risk, and recovery** — the same three things the OS itself is built to guarantee. Form follows the doctrine.
{% endhint %}
