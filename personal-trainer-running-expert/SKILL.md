---
name: personal-trainer-running-expert
description: >-
  Running coaching expertise for designing and explaining run training. Use when
  programming or adjusting running sessions, setting training paces or heart-rate zones,
  choosing workout types (easy, long, tempo/threshold, intervals/VO2max, fartlek, hills,
  strides, race-pace), structuring a running week, or planning a build toward a goal
  (5k, 10k, half-marathon, marathon, general fitness, or the running portion of Hyrox).
  Supplies the running knowledge the personal-trainer skill uses to turn a weekly intent
  into concrete sessions. Triggers even without the word "running" when the activity is
  clearly run-based — e.g. "what should today's intervals be", "set my threshold pace",
  "design an easy run", "how hard should the long run be".
license: Proprietary
compatibility: >-
  Companion to the personal-trainer skill. Provides running training content and session
  sequencing only; data access, journaling, plan validation, and scheduling are handled by
  personal-trainer.
metadata:
  author: HyperHealth
  version: "0.2"
---

# Running Coaching Expert

You supply the *running content*: what to run, how fast, how hard, and why. The
**personal-trainer** skill owns the data, journal, plan schema, and scheduling — hand
finished session designs back to it. Always adapt to the athlete's level, goal, and
current recovery from their profile and the latest weekly review.

## Setting zones and paces

- **Anchor on a real benchmark** — a recent race, a time-trial, or a measured threshold
  effort. Prefer measured data over generic formulas; refine as new benchmarks arrive.
- **Paces** derive from that benchmark (VDOT-style relationships):
  - *Easy* — conversational; roughly 1:30–2:00/km slower than threshold. Most running lives here.
  - *Marathon* — sustainable for ~3+ hours.
  - *Threshold* — comfortably hard, ~1-hour race effort.
  - *Interval (VO2max)* — ~3–5k race effort.
  - *Repetition* — faster than VO2, short reps for speed/economy.
- **Heart-rate zones (5-zone)** from threshold HR (LTHR) or HRmax. Wrist HR is approximate
  and lags on short, sharp efforts — **use pace to control quality work and HR to enforce
  easy-day discipline.**
- **CoachBridge alerts:** pace as `"m:ss"` per km (`min`/`max`); easy effort as an HR `zone` (1–5).

## Workout toolbox

| Type | Purpose | Typical shape | Alert |
|------|---------|---------------|-------|
| Easy / recovery | Aerobic base, recovery | Steady conversational run | HR zone 1–2 |
| Long run | Aerobic endurance, durability | 1–2.5 h easy; optional finish at MP | HR zone 2 (pace late) |
| Tempo / threshold | Raise lactate threshold | 20–40 min continuous, or cruise intervals (e.g. 4×8 min) | threshold pace |
| VO2max intervals | Aerobic power | 5×1000 m / 6×800 m / 8×400 m, work:recovery ≈ 1:1 | interval pace |
| Fartlek | Unstructured speed play | e.g. 8×(1 min hard / 1 min easy) | pace or open |
| Hills | Power, economy, low-impact intensity | short (10–12×30 s) or long (6×2 min) | open / HR |
| Strides | Neuromuscular, form | 4–8×20 s relaxed fast after easy run | open |
| Race-pace / specific | Goal-pace economy & confidence | reps or blocks at goal pace | goal pace |

Scale by level: beginners get fewer/shorter reps and more recovery; advanced athletes get
more volume at quality. When recovery is poor, downgrade quality to easy — see
`references/load-and-injury.md`.

## Structuring the running week

- **Polarized lean (~80/20):** the large majority of running easy, a small fraction hard.
  Easy days run too fast is the single most common mistake — cap by HR/pace.
- Separate hard days with easy or rest; don't stack quality back-to-back for most athletes.
- One long run per week; place quality where the athlete is freshest.
- Session count and volume scale with level and time available (from the profile).
- Count *all* the loading, not just the running. Two strength sessions plus four runs is a
  six-session week, and the legs don't care which label a session had.

## Sequencing — what a session costs, and what can follow it

Most bad weeks aren't bad sessions. They're good sessions in an impossible order. Every
session you hand over carries a **recovery cost**, and that cost is what decides the next
day — so design the week as a sequence, not as seven independent days.

| Session | Recovery cost | The next day can be | Not the next day |
|---------|---------------|---------------------|------------------|
| Easy / recovery | none | anything | — |
| Easy + strides | very low | anything | — |
| Long run < 75 min | low–moderate | easy, strength | quality |
| Long run 75–120 min | **high** | easy, or rest | quality, **strides**, lower-body strength |
| Long run > 120 min | very high | rest or very easy | anything with intensity |
| Tempo / threshold | moderate–high | easy, or rest | quality |
| VO2max intervals | high | easy, or rest | quality, strides |
| Hills | high, strongly eccentric | easy, or rest | quality — expect DOMS at 48h |
| Race / time-trial | very high | rest | quality for 2–3 days |
| Lower-body strength | high and **delayed** | easy | long run, quality |

Two things this table exists to stop:

- **Strides are not recovery.** They're short, they feel harmless, and they are still a
  neuromuscular effort on legs that have to push off hard. The day after a 90-minute long
  run, an athlete cannot execute accelerations — they'll either run them badly or hurt
  themselves. An easy run the day after a long run is *flat*: no strides, no pickups, no
  "just a few accelerations at the end."
- **DOMS peaks at 24–48h, not immediately.** The evening after a heavy lower-body session
  the athlete feels fine, which is exactly why the next-day run gets scheduled. It's the
  morning *after that* which is wrecked. Leave two clear days between lower-body strength
  and any key run — and for an athlete who reports lasting DOMS, treat it as a hard rule.

**Read the week backwards before you hand it over.** Walk it day by day, carrying fatigue
forward: what are this athlete's legs actually like on the morning of each session, given
everything before it? A session that's right in isolation can be impossible in sequence,
and writing the week forward is exactly how that gets missed.

## Progression & deload

- Add volume **or** intensity in a given block, not both at once.
- Nudge weekly volume modestly (~5–10%, individualized); consistency beats heroic weeks.
- A ~3 weeks build / 1 week deload rhythm works for many — individualize from recovery data.

## Translating a session for scheduling

Example — threshold `5×1k`: warmup 10 min easy (HR z2) → 5 × [1000 m @ 4:45–5:00/km, 2 min
recovery] → cooldown 8 min easy. Hand this structure + targets to
`personal-trainer/references/programming.md`, which builds, validates, and schedules the
CoachBridge plan JSON. Do not build/schedule the JSON here.

Hand over the **recovery cost** with the session, not just its content — that's what the
plan gate (`personal-trainer/references/plan-critique.md`) needs to judge the order. If the
gate comes back objecting to a placement, the fix is usually the *week*, not the session:
move it, or downgrade it, rather than defending a session that's right on the wrong day.

## Gotchas

- Easy too fast — the #1 error. Enforce by HR/pace.
- A session that's right in isolation, on the wrong day — the #2 error, and the one that
  makes a week unrunnable. Check what precedes it before you finalize it.
- Don't chase paces when readiness is low; adjust the session, not the athlete.
- Wrist HR lags on short reps — control those by pace, not HR.
- Treadmill ≠ outdoor effort; set `location` and expect pace/effort differences.
- New stimulus (hills, speed, big long runs) → ramp gradually; expect some DOMS.
- GPS pace is noisy on short reps and trails — prefer distance goals + RPE there.

## Going deeper

- Phased plan toward a goal/event → `references/periodization.md`
- Load management, backing off, and injury red flags → `references/load-and-injury.md`
