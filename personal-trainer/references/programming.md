# Programming — turn intent into scheduled sessions

Translate the week's intent into the CoachBridge plan schema, put it through the gate, then
schedule. Session *content* (paces, structures, zones) comes from the sport expert
(**personal-trainer-running-expert** for running); this file owns the schema and the
scheduling mechanics, and `references/plan-critique.md` owns the gate.

## Plan schema (CoachBridge `schedule_plan`, PRD §9)

```jsonc
{
  "sessions": [
    {
      "id": "2026-06-22-intervals",          // stable, unique, date-based; reuse for reconciliation
      "title": "W3 T1 Intervals",             // display label (Watch + app); falls back to id
      "date": "2026-06-22T07:00:00+02:00",    // ISO-8601 with offset
      "activity": "running",                   // HKWorkoutActivityType name
      "location": "outdoor",                   // "indoor" | "outdoor" (optional)
      "note": "Threshold day — settle in, don't go out hot. 💪", // optional coach note shown in-app
      "structure": {
        "warmup":  { "goal": { "type": "time", "minutes": 10 }, "alert": { "type": "hr", "zone": 2 } },
        "blocks": [
          { "repeat": 5,
            "work":     { "goal": { "type": "distance", "meters": 1000 }, "alert": { "type": "pace", "min": "4:45", "max": "5:00" } },
            "recovery": { "goal": { "type": "time", "minutes": 2 } } }
        ],
        "cooldown": { "goal": { "type": "time", "minutes": 8 } }
      }
    }
  ]
}
```

- **goal.type:** `time` (`minutes`), `distance` (`meters`), `energy` (`kilocalories`), or `open`.
- **alert.type:** `hr` (with `zone` 1–5), `pace` (`min`/`max` as `"m:ss"` per km), `cadence`, or `power` (`min`/`max` numeric strings).
- `blocks[].repeat` ≥ 1; `warmup`/`cooldown`/`recovery` optional.
- `title` (optional, per session): the human-readable label the athlete sees on the Watch and in the app. Use **`W{week} T{n} {Type}`** — `week` is the training-block week number (the week index within the current plan/build), `n` is the session number within that week (1, 2, 3… in date order), and `Type` is the session type (Easy run, Intervals, Tempo, Long run, Strength…). E.g. `"W3 T2 Easy run"`. Don't put the date in the title — it's shown separately. Keep `id` date-based for reconciliation; the title is display-only and falls back to `id` when omitted.
- `note` (optional, per session): a coach note for the athlete — a short encouragement or an explanation of the session's purpose/intent. Shown in the app when they open the workout (not on the Watch); rides back to you on `list_scheduled`. Keep it personal and brief; omit when you have nothing to add.
- `raceSim` (`"separate"`|`"continuous"`) exists for Hyrox-style mixed sessions but is deferred — omit unless asked.

## Process — plan, gate, execute

1. **Get content** from the sport expert: each session's structure, paces, and zones.
2. **Build the plan JSON** for the week. Set each `date` from the client's availability
   (`client-profile.md`) and check the **Calendar MCP** (`list_events`) to avoid clashes.
   Map paces to `"m:ss"` per km; map easy-day effort to HR zones.
3. **Run the gate — `references/plan-critique.md`.** Non-negotiable, and it is the whole
   reason a week gets caught before the athlete does. Two layers:
   - **`scripts/check_plan.py`** — mechanical validation. Schema (ids, goals, repeats, pace
     format, HR zones) *and* the things a schema can't see: hard-day spacing, quality or
     strides too soon after a long run, lower-body strength colliding with a key run,
     consecutive training days, session-count and volume steps, easy/hard split, and whether
     each session fits a day and time the athlete actually has. Exit 1 means it does not
     ship.
   - **The critique panel** — independent critics, one per lens (execution reality,
     progression & goal fit, injury flags, athlete fit), reconciled before scheduling.

   ```bash
   python3 scripts/check_plan.py plan.json --context ctx.json --week-start 2026-07-06
   ```

   Fix, re-run, and only move on when it's clean. Building the week forward, day by day, is
   exactly how an impossible sequence gets written — the gate is what reads it back.
4. **Reconcile existing.** `list_scheduled` to see what's already on the device;
   `remove_scheduled` anything you're replacing. (Both live-only — the phone must be reachable.)
5. **Schedule.** `schedule_plan` (live-only). On error, read the message precisely
   (unsupported activity/goal combo, malformed step, scheduling limit) and correct.
6. **Confirm.** Report the returned scheduled sessions to the client. Optionally mirror them
   to the Calendar MCP (`create_event`) so they show on the agenda.

## Discipline
Schedule one week at a time — only what you'll actually review. Don't get ahead of the
feedback loop. And never schedule a week the gate hasn't cleared: "it looked fine while I
was writing it" is precisely the judgment the gate exists to replace.
