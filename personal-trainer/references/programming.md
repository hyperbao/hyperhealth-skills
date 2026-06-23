# Programming — turn intent into scheduled sessions

Translate the week's intent into the CoachBridge plan schema, validate it, then schedule.
Session *content* (paces, structures, zones) comes from the sport expert
(**personal-trainer-running-expert** for running); this file owns the schema, validation,
and scheduling mechanics.

## Plan schema (CoachBridge `schedule_plan`, PRD §9)

```jsonc
{
  "sessions": [
    {
      "id": "2026-06-22-intervals",          // stable, unique; reuse for reconciliation
      "date": "2026-06-22T07:00:00+02:00",    // ISO-8601 with offset
      "activity": "running",                   // HKWorkoutActivityType name
      "location": "outdoor",                   // "indoor" | "outdoor" (optional)
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
- `raceSim` (`"separate"`|`"continuous"`) exists for Hyrox-style mixed sessions but is deferred — omit unless asked.

## Process — plan, validate, execute

1. **Get content** from the sport expert: each session's structure, paces, and zones.
2. **Build the plan JSON** for the week. Set each `date` from the client's availability
   (`client-profile.md`) and check the **Calendar MCP** (`list_events`) to avoid clashes.
   Map paces to `"m:ss"` per km; map easy-day effort to HR zones.
3. **Validate before scheduling.** Confirm: every session has `id`, `activity`, `structure`;
   `blocks` is non-empty; each `goal` has the field its `type` requires; `repeat` ≥ 1; pace
   strings look like `"m:ss"`; HR `zone` is 1–5. Fix problems before sending.
4. **Reconcile existing.** `list_scheduled` to see what's already on the device;
   `remove_scheduled` anything you're replacing. (Both live-only — the phone must be reachable.)
5. **Schedule.** `schedule_plan` (live-only). On error, read the message precisely
   (unsupported activity/goal combo, malformed step, scheduling limit) and correct.
6. **Confirm.** Report the returned scheduled sessions to the client. Optionally mirror them
   to the Calendar MCP (`create_event`) so they show on the agenda.

## Discipline
Schedule one week at a time — only what you'll actually review. Don't get ahead of the
feedback loop.
