# Client Profile — [Name]
_Last updated: [YYYY-MM-DD]_

## Snapshot
- Age / sex (if shared):
- Units: metric
- Coaching tone & check-in cadence:
- Knowledge level (how much to teach vs. talk shorthand): [beginner / intermediate / advanced — note specifics, e.g. "knows zones & RPE, new to periodization"]
- Weekly routine (auto weekly review): [none / set — day & time + mechanism, e.g. "Sun 18:00, host scheduled task"]

## Goals
- Primary goal (and why):
- Target event & date:
- Secondary goals:
- What success looks like:

## Training background
- Years running / experience:
- Recent training (volume, frequency):
- Injury history / surgeries:
- Current niggles / limitations:

## Current level (derived from recent data — no raw samples)
- Recent benchmark (race / time-trial):
- Typical easy pace:
- Current weekly volume:
- Longest recent run:
- VO2max (Apple estimate, trend):

## Baselines (derived; update as trends shift)
- Resting HR baseline:
- HRV (SDNN) baseline range (7–14 day band):
- Typical sleep (total / pattern):
- Subjective baseline (typical check-in scores — fatigue / motivation / soreness / life load): [e.g. 2 / 1 / 2 / 3 — refresh ~monthly so "normal for them" stays current]

## Constraints
- Weekly availability (days / times):
- Session-length limits: [note if it differs by day — e.g. 60 min weekday mornings, open at the weekend]
- Equipment & access (treadmill, track, gym):
- Environment (terrain, climate):
- Travel / fixed commitments:

## Health & lifestyle
- Conditions / medications (if shared):
- Stress / life load:
- Sleep context:

## Data sources
- CoachBridge MCP: [connected? from get_status]
- Calendar / agenda: [MCP-connected (which calendar, e.g. Google Calendar) / shared weekly at review / none]
- Mood (State of Mind) & menstrual cycle: tracked via CoachBridge when the client logs them (optional)
- Nutrition / hydration: not tracked (not read by CoachBridge)
- Ad-hoc weather checks when planning outdoor sessions: [yes/no]

## Sequencing rules (athlete-specific)
Rules you've established for this athlete about what can follow what. Mirror each one into
the `rules` block of the `ctx.json` used by `scripts/check_plan.py` — a rule that lives only
here is a rule that gets forgotten when the week is drafted.
- [e.g. no key run within 48h of a big lower-body session → `min_days_after_lower_body: 2`]

## Preferences & notes
-

## Update log
- [YYYY-MM-DD] — [what changed]
