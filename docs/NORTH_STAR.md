# North Star

Status: Current
Owner: Krish Raja
Last verified: 2026-10-18

> By 18 November 2026, any raw recording (a keynote, a podcast, a room) goes in and comes out compressed with its best clips already cut, ready for the content engine, without leaving the machine.

Set by Krish on 18 October 2026. It is not reached yet. It is what every session in this repository works toward.

## The number

**Share of the week's raw recordings compressed with their best clips cut, with no manual step**: 100% by 16 November 2026, on a linear weekly ladder. Checkpoints: 16 Nov 2026: 100%.

```yaml north-star-metric
metric: "Share of the week's raw recordings compressed with their best clips cut, with no manual step"
unit: %
direction: up
target: 100
deadline: 2026-11-16
ladder_shape: linear
source: "The engine's run log against the week's recordings"
status: active
ladder:
  - [2026-10-26, 25.0]
  - [2026-11-02, 50.0]
  - [2026-11-09, 75.0]
  - [2026-11-16, 100.0]
```

Urgency (U1 to U5) is worked out every week from where the number stands against that week's target, by [the harness contract](https://github.com/krishanraja/ai-harness/blob/main/contract/north-star-metric.md). Set by Krish on 23 October 2026.

## How to use it

- Read it before any work, every session.
- Before you start, say which part of it the task moves. If the task moves nothing toward it, say so first and let Krish decide.
- Prefer the work that moves it furthest, and close each session by noting what moved.
- Only Krish changes this file. Record his ruling in the commit body as `Ruling (Krish, YYYY-MM-DD): ...`.
- When it is reached, say so and ask Krish for the next one.
