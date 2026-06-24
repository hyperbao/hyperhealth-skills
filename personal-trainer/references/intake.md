# Intake — first-run onboarding

Goal: understand the client well enough to build a first plan, then scaffold the journal.
Run this only when `./journal/` does not yet exist. Keep it a conversation, not an
interrogation — ask in batches, react to answers.

## 1. Interview

Cover these; skip what the client volunteers, follow up on what matters.

- **Goal** — primary goal and *why*; target event and date if any; what success looks like;
  any secondary goals.
- **Training background** — years of running/training; recent training (volume, frequency);
  injury history and surgeries; current niggles or limitations.
- **Current level** — most recent race or time-trial; a typical easy-run pace; current
  weekly volume; longest recent run.
- **Constraints** — which days/times they can train; session-length limits; equipment and
  access (treadmill, track, gym); usual terrain and climate; regular travel or fixed
  commitments.
- **Health & lifestyle** — relevant conditions or medications (only if they choose to
  share); typical sleep; current stress/life load.
- **Preferences** — units (default metric), coaching tone, how often to check in; whether
  they want you to check weather ad hoc when planning outdoor sessions.

## 2. Establish baselines from data (derived only)

1. `get_status` — confirm the bridge is reachable and HealthKit is authorized. If not,
   tell the client what to fix and proceed with self-reported numbers for now.
2. `get_metrics` with `interval=day` over the last 14–30 days for: HRV (SDNN), resting HR,
   respiratory rate, sleep analysis, VO2max, body mass. 
3. `get_workouts` over the last 30 days to see recent volume, frequency, and paces.

From these, **compute and keep derived baselines only** (never raw samples):
- resting HR baseline (typical value)
- HRV (SDNN) baseline *range* over 7–14 days (it's sampled sporadically — read the band, not a point)
- typical sleep (total, rough pattern)
- current weekly volume and session count
- recent benchmark pace/effort

Mood (Apple State of Mind) and menstrual cycle are available from CoachBridge when the
client logs them (both optional; mood needs iOS 18+). If present, baseline them like any
other signal and note in the profile that they're tracked; if absent, record "not logged."
Nutrition / hydration is not read by CoachBridge — record it as "not tracked" and do not
gather it another way.

## 3. Scaffold the journal

Create `./journal/` and these files (copy from `assets/`, fill from the conversation +
derived baselines). See `references/journal.md` for the full contract.

- `journal/client-profile.md` — from `assets/client-profile.template.md`
- `journal/training-plan.md` — from `assets/training-plan.template.md`. For a running goal,
  use the **personal-trainer-running-expert** skill (`references/periodization.md`) to lay
  out the phase map toward the target date.
- `journal/decision-log.md` — from `assets/decision-log.template.md`; seed it with the
  intake decisions (goal chosen, starting volume, plan approach + why).
- `journal/weekly/` — empty directory; the first weekly log is written at the first review.

## 4. Confirm direction

Summarize back to the client: the goal, the starting point, and the plan's shape and first
phase. Get their agreement before programming the first week (`references/programming.md`).
