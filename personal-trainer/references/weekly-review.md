# Weekly review — the coaching loop

The core cycle: read state → interpret → decide → program next week → log. Work the
checklist; don't skip the logging.

## 1. Load context
Read `journal/client-profile.md`, `journal/training-plan.md`, the latest `journal/weekly/`
file, and `journal/decision-log.md`. Know the current phase, this week's intent, and what
you were watching.

## 2. Pull the week's data
Use `interval=day` and explicit `types`; window = the training week under review.

- `get_status` — reachable? authorized? is data stale?
- `get_metrics` for: HRV (SDNN), resting HR, respiratory rate, SpO2, sleep analysis,
  sleeping wrist temperature, active energy, steps/exercise time, VO2max, body mass (and
  running dynamics if relevant).
- `get_workouts` for the week.
- `get_reconciliation` for the week → planned-vs-actual. If unavailable, build it from
  `list_scheduled` + `get_workouts` by matching date and activity.
- `get_feedback` for the week → the athlete's own notes. If unavailable, ask the client
  how the key sessions felt (RPE, energy, anything off).

## 3. Interpret

- **Readiness / recovery.** HRV vs the 7–14 day baseline *range* (trend, not a single
  value). Resting HR vs baseline — sustained elevation suggests fatigue, stress, or illness.
  Sleep: read the per-night summaries in `sleep[]` (total asleep, deep/REM/core minutes,
  awakenings, efficiency) — already rolled up, no need to sum stage intervals yourself.
  Respiratory rate / SpO2 anomalies.
- **Stress read.** Combine HRV (vs baseline band), resting HR (vs baseline), sleep quality,
  and sleeping wrist temperature into one call — **low / moderate / high** physiological
  stress vs the client's baseline — and record it in the weekly log. This is an *inferred*
  read (Apple has no stress metric), so weight it alongside the athlete's feedback rather
  than treating it as a measured score. Subjective mood (Apple State of Mind) **is**
  available when the client logs it (iOS 18+) — if present, fold its valence/labels into
  the stress read; if absent, note it as not logged and rely on the physiological read.
- **Menstrual cycle.** If the client tracks their cycle, use the phase (from logged
  menstrual-flow / cycle-start dates, plus basal body temperature when present) to
  contextualize readiness, energy, and injury risk — track the athlete's *own* patterns
  rather than applying rigid rules. Available from CoachBridge when logged (optional).
- **Training load.** Weekly volume and session count; intensity distribution (easy vs hard);
  notable sessions vs the prescribed paces/HR. Compare to plan and to recent weeks — watch
  for sharp jumps.
- **Adherence.** Completed / modified / missed, read together with the feedback.
- **Life context.** For the coming week — travel, deadlines, holidays — to shape next week's
  load and placement. Use the agenda path the client chose at intake (profile **Data sources**):
  if the **Calendar MCP** is connected, pull `list_events`; if they opted to **share weekly**,
  ask them for the coming week's constraints here.

## 4. Decide and adjust
Distinguish adaptation (handling load, ready for more) from accumulating fatigue from red
flags. Adjust next week's volume/intensity accordingly. On under-recovery or pain signals,
back off — see the running expert's `references/load-and-injury.md`. Record the decision
and its rationale.

## 5. Program next week
Hand the week's intent to `references/programming.md`, drawing session content (paces,
structures) from the **personal-trainer-running-expert** skill.

## 6. Write the outputs (derived only)
- Create `journal/weekly/<ISO-week>.md` from `assets/weekly-log.template.md`.
- Update `journal/training-plan.md` if the plan changed.
- Append `journal/decision-log.md` with any non-trivial decisions.

## Red-flag guidance
Advise rest or a professional evaluation when you see: sharp or localized pain, or pain
that alters gait; a sustained combination of low HRV + elevated resting HR + poor sleep;
illness; or unusual, persistent fatigue. When in doubt, be cautious and refer out.
