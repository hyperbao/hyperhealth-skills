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
- **Calendar / agenda** — ask how they want their personal agenda used to place sessions
  around real life (travel, work, commitments). Offer two paths and let them choose:
  - **Connect via MCP** — read the calendar directly with the **Calendar MCP** (e.g. Google
    Calendar `list_events`) so you can see their agenda whenever you plan a week. Confirm the
    MCP is connected with a quick `list_events` test; if it isn't, tell them what to enable.
  - **Share weekly** — they tell you the coming week's constraints during each weekly review,
    and you plan from that instead of reading the calendar.
  Record their choice (and which calendar, if connected) in the profile's **Data sources**.

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

## 5. Offer a recurring weekly routine

Before you finish onboarding, **ask the client whether they want a recurring weekly routine**
that automatically runs the weekly check-in — pull the week's data, interpret it, adjust the
plan, and log the week (`references/weekly-review.md`) — so the loop keeps running without
them having to remember to ask.

- Frame it as a choice, not a default: "Want me to set up a weekly routine that reviews your
  data and updates your plan automatically, or would you rather kick off each review yourself?"
- If yes, agree on **day and time** (anchor it to the check-in cadence from the interview, and
  to when the week's training is done — e.g. Sunday evening or Monday morning), then create the
  recurring task using the **host's scheduled-task / recurring-task capability** (if the host
  exposes one). The scheduled task should invoke this skill's weekly review. Confirm back the
  exact schedule you set.
- If the host has no scheduling capability, say so plainly and fall back to a standing
  agreement: remind the client on the agreed day, and prompt them to start the review.
- Record the outcome in `journal/client-profile.md` (the **Weekly routine** field): whether a
  routine is set, its day/time, and the mechanism — so a future coach knows the loop is armed
  and how to change or cancel it. Log the decision in `journal/decision-log.md`.

The client can always change or cancel the routine later; treat "set up a weekly routine" and
"change/cancel my weekly routine" as triggers to revisit this step.
