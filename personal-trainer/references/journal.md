# Journal — structure and contract

The journal is the coaching record. Write it so another coach could pick it up cold and
continue without you. It lives in `./journal/` in the working directory.

```
journal/
├── client-profile.md      # who they are, goals, constraints, derived baselines
├── training-plan.md       # current macro plan: phases, current week, history
├── decision-log.md        # append-only log of coaching decisions + rationale
└── weekly/
    ├── 2026-W26.md         # one progress log per ISO week
    └── 2026-W27.md
```

## What each file holds

- **client-profile.md** — identity, goals, training background, constraints, health/lifestyle,
  and *derived* baselines. Update when these change and add a line to its update log.
- **training-plan.md** — the current macro plan: goal, phase map toward the target date,
  current phase/week, the current weekly template, benchmarks, and an update history.
- **decision-log.md** — append-only, most recent at top. Every non-trivial coaching decision:
  what you decided, why, and the derived data that drove it.
- **weekly/`YYYY-Www`.md** — one progress log per ISO week, from
  `assets/weekly-log.template.md`. The heart of progress tracking and handoff.

## File naming — ISO weeks

Weekly logs are named by ISO week: `YYYY-Www`, e.g. `2026-W26`. Get the current ISO week
deterministically rather than guessing:

```bash
date +%G-W%V        # e.g. 2026-W26 (GNU/BSD date)
```

## When to write

| File | Written at |
|------|-----------|
| client-profile.md | intake; and whenever profile facts or baselines change |
| training-plan.md | intake; and on every plan adjustment |
| weekly/`week`.md | every weekly review |
| decision-log.md | whenever you make a non-trivial coaching decision |
| sessions (optional) | per-session notes if a session is worth recording in detail (`assets/session-note.template.md`) |

## Privacy — restate before every write

Persist **derived data only**. Never paste a raw MCP payload or sample array into the
journal. Allowed: trends vs baseline, computed summaries (total sleep, % deep/REM, wake
count), weekly load totals, scores/ratios you compute, and decisions. The source samples
stay in the working turn and are not saved.

## Handoff principle

Every entry should help a future coach understand the *current state* and the *reasoning*:
where the client is, what you changed and why, what to watch, and what's next.
