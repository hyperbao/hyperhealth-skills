# Journal — structure and contract

The journal is the coaching record. Write it so another coach could pick it up cold and
continue without you.

**Where it lives.** The journal's home is the **CoachBridge iCloud Drive folder**, so the
record syncs to the athlete's devices and they can read it in Finder / the Files app (it
shows up as "CoachBridge"). Never hard-code its path — resolve it with

```bash
python3 scripts/journal_root.py          # --json for structured output
```

On disk the folder is an iCloud *container* under `~/Library/Mobile Documents/`, named
after the app's container identifier (`iCloud~<reverse-dns>~CoachBridge`). The script
discovers it by that pattern for whichever user is running the skill and returns
`<container>/Documents/journal` as the root. The CoachBridge **iPhone app** creates the
container; iCloud syncs it down to the Mac.

Fallback rule — `./journal/` in the working directory is used **only when iCloud Drive is
not available on this machine** (`source: local`), or when the athlete opted out of iCloud
in the iPhone app's setup — `get_status` then reports `journal.mode: "local"` and you run
the resolver with `--local`. If iCloud Drive is on but the
CoachBridge folder hasn't arrived yet (`source: icloud-pending`, exit 3), do **not** fall
back: ask the athlete to open the CoachBridge iPhone app and confirm CoachBridge is enabled
under iCloud Drive on both devices, then re-run. Sandbox runs (e.g. `coach-test/`) opt into
a local journal explicitly with `--local` (or `--root PATH`), never by accident.

Resolve this once at the start of a session and use the same root throughout. Create the
`journal/` folder (and `weekly/`) by writing into it. The structure below is identical
whichever root you end up with.

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
