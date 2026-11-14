# North Star

Status: Current
Owner: Krish Raja
Last verified: 2026-11-14

> Anything Krish points at, a link or a file, becomes a full text reading on his own machine and a card that asks why he likes it, with no model watching it.

Set by Krish on 14 November 2026, his yes to D3 in `docs/DECISIONS.md`. It replaces the compression-only North Star set on 18 October 2026, before the rename. It is not reached yet. It is what every session in this repository works toward.

## The number

**Share of links he pastes that become a card with a full reading within 15 minutes, with no manual step**: target 100%. Baseline 16 of 23 (70%), all time to 14 November 2026. Krish set no deadline; the target holds every week from the week of his yes.

```yaml north-star-metric
metric: "Share of links he pastes that become a card with a full reading within 15 minutes, with no manual step"
unit: %
direction: up
target: 100
ladder_shape: linear
source: "Control Center content_watch_requests joined to content_reads on read_id: links pasted this ISO week, at least 15 minutes old, read within 15 minutes of the paste (a reused reading counts as on time)"
status: active
ladder:
  - [2026-11-09, 100.0]
```

Measured every morning by Control Center (`READERS['content-watcher']` in its `api/_northStarRefresh.ts`), which writes the state line in `NOW.md`. A week with no link pasted is unknown, never zero. Urgency (U1 to U5) is worked out from where the number stands against that week's target, by [the harness contract](https://github.com/krishanraja/ai-harness/blob/main/contract/north-star-metric.md).

## How to use it

- Read it before any work, every session.
- Before you start, say which part of it the task moves. If the task moves nothing toward it, say so first and let Krish decide.
- Prefer the work that moves it furthest, and close each session by noting what moved.
- Only Krish changes this file. Record his ruling in the commit body as `Ruling (Krish, YYYY-MM-DD): ...`.
- When it is reached, say so and ask Krish for the next one.
