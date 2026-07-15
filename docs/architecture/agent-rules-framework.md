---
description: >-
  The XML-tagged microservices layout that every system prompt, subagent
  profile, and tool instruction sheet must follow.
icon: code
---

# Agent rules framework

Every system prompt, subagent profile, and tool instruction sheet must use the same **software-like, XML-tagged microservices architecture**. Treating prompts as structured modules — rather than prose — is what makes agent behaviour inspectable and repeatable.

## The required tag structure

```xml
<role>Define explicit operational character and unique system utility.</role>
<context>Map baseline project facts, environment constraints, and current goals.</context>
<priority_rules>Assign severity-ranked rules governing all execution paths.</priority_rules>
<decision_frameworks>If/then routing checklists and early-exit conditions.</decision_frameworks>
<tools_and_permissions>Allowed/forbidden utilities, filesystem locks, and approval gates.</tools_and_permissions>
<skills>List of pre-cleared, declarative workflows available to the thread.</skills>
<memory_policy>Data extraction, trust rules, and state promotion protocols.</memory_policy>
<validation>Mandatory methods to empirically verify claims before reporting success.</validation>
<anti_patterns>Explicit list of bad behavioral traits and structural violations.</anti_patterns>
<trust_boundaries>Firewalls against context poisoning and injection vectors.</trust_boundaries>
<final_response_rules>Standardized formatting constraints for final transaction logs.</final_response_rules>
```

## What each tag governs

| Tag | Purpose |
|---|---|
| `<role>` | Operational character and unique system utility of the agent. |
| `<context>` | Baseline project facts, environment constraints, current goals. |
| `<priority_rules>` | Severity-ranked rules governing all execution paths. |
| `<decision_frameworks>` | If/then routing checklists and early-exit conditions. |
| `<tools_and_permissions>` | Allowed/forbidden utilities, filesystem locks, approval gates. |
| `<skills>` | Pre-cleared, declarative workflows available to the thread. |
| `<memory_policy>` | Data-extraction, trust, and state-promotion protocols. |
| `<validation>` | Methods to empirically verify claims before reporting success. |
| `<anti_patterns>` | Bad behavioural traits and structural violations to avoid. |
| `<trust_boundaries>` | Firewalls against context poisoning and injection vectors. |
| `<final_response_rules>` | Formatting constraints for final transaction logs. |

## The Wager Loop

{% hint style="info" %}
**Enforce the "Wager" Loop.** Agents must log a prediction *before* action and a verification *after* action. Pairing an explicit hypothesis with an explicit post-action check is what patches the known verification blind spot — the tendency to declare success without proof.
{% endhint %}

Severity ranking is first-class: rules carry levels (for example, `LEVEL 4: SEVERE VIOLATION` down to `LEVEL 2: STRONG RULE`) so that when rules collide, the higher-severity rule wins deterministically. The forensic operator methodology that these prompts encode is documented in [Forensic methodology](forensic-methodology.md).
