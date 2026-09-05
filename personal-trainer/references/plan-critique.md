# Plan critique — the gate before the Watch

A week that reads well in a chat window is not the same as a week a tired human can
execute. The failure mode is specific and it repeats: the coach writes the week forward,
day by day, and never reads it *backwards* as a whole — so a 90-minute long run gets
followed the next morning by a run with accelerations, and nobody notices until the
athlete tries to run it.

Nothing reaches `schedule_plan` until it has been through both layers below.

## Layer 1 — the mechanical gate (always)

Write the plan JSON to a file and run the checker:

```bash
python3 scripts/check_plan.py plan.json --context ctx.json --week-start 2026-07-06
```

`ctx.json` is built once per athlete from `client-profile.md` and the recent weekly logs,
and refreshed as they change:

```jsonc
{
  "week_start": "2026-07-06",                    // Monday of the target week
  "availability": {
    "days": ["mon","tue","thu","sat","sun"],
    "windows": { "mon": ["06:30","08:15"] },     // per-day; omit where it's open
    "max_session_minutes": { "default": 60, "sat": 150, "sun": 150 }
  },
  "recent": { "weeks": [ { "iso": "2026-W27", "sessions": 5, "minutes": 195 } ] },
  "session_tags": { "2026-07-06-force-a": ["lower-body"] },  // what the title can't say
  "busy": [ { "start": "…", "end": "…", "label": "déplacement" } ],
  "rules": { "min_days_after_lower_body": 2 }    // athlete-specific overrides
}
```

The default thresholds encode ordinary coaching practice; **the athlete's own rules belong
in `rules`**. When you establish a sequencing rule in the journal ("no key run within 48h of
a big lower-body session"), put it here too — a rule that lives only in prose is a rule that
gets forgotten. `--list-rules` prints the full set and the current thresholds.

Then:

- **BLOCK** → fix it. Exit code 1 means the plan does not go to the Watch. You may overrule a
  BLOCK, but only deliberately: change the threshold in `ctx.json` if the rule is wrong for
  this athlete, or record the override and its reason in `decision-log.md` if it's a one-off.
  Never overrule silently.
- **WARN** → a judgment call, not a veto. Every warning must be *answered* in layer 2 — fixed,
  or consciously accepted with a reason.
- **Any material edit → re-run the checker.** Moving a session to fix one rule routinely
  breaks another.

The checker validates mechanics only: schema, spacing, load steps, feasibility. It cannot
tell you whether this is the right week for this athlete. That's layer 2.

## Layer 2 — the critique panel

Run **independent critics in parallel**, each given one lens, then reconcile. Independence is
the whole point: a critic who has read your reasoning will confirm it.

**What each critic gets:** the rendered week (day, session, structure, targets), the checker's
output, and the facts they need — profile constraints and open niggles, the current phase and
its intent, the last two weekly logs, and this week's check-in answers.

**What each critic must NOT get:** your rationale for the week. They judge the plan cold.

**The brief, for every critic:** *"Your job is to find the reason this week fails. Assume it
does. If you can't break it, say so explicitly."*

### The four lenses

| Lens | The question it owns |
|------|---------------------|
| **Execution reality** | Can a tired human actually run this, in this order, in these slots? Read the week backwards, day by day, carrying fatigue forward from the session before. What is the athlete's body like on the morning of each session? |
| **Progression & goal fit** | Does this week move the athlete toward the goal, at the right point in the phase? Flag under-cooking as readily as over-cooking — a wasted week is also a failure. |
| **Injury & health flags** | Does anything here load the known niggle, injury history, or a red flag from the check-in? Would a cautious coach schedule this given what's in the profile? |
| **Athlete fit** | Does it respect the constraints, preferences and stated capacity in the profile and this week's check-in — session-length limits, available mornings, how much detail this athlete wants, what they said they had left in the tank? |

**Each critic returns:** a verdict (`ship` / `fix` / `rethink`) and a list of objections, each
with what's wrong, why it matters, and a concrete fix.

### Reconciling

- **Two or more critics raising the same objection independently → treat it as a BLOCK.**
  Convergence from separate lenses is the strongest signal you get.
- **A single critic's objection** → fix it, or write one line on why you're not.
- **Critics object; they don't rewrite.** You own the week. Don't hand it to a committee — take
  the objection, decide the fix.
- **After any material change, re-run layer 1**, then re-check whether the fix created a new
  objection.
- **Cap it at two rounds.** If the week still won't converge, the problem isn't the schedule —
  it's the intent behind it. Go back to the decision, not the calendar.

### How heavy to go

Always run layer 1. For layer 2, scale to the week:

- **Full panel (all four lenses)** — a new phase or block, a volume or intensity step, a new
  session type, the week after a red flag or a deload decision, or **any week the checker
  returned a WARN**.
- **Single critic (execution reality)** — a routine week that repeats a validated shape with a
  clean checker run.

**No subagents available in the host?** Then do the critique yourself, but do it properly: take
the lenses one at a time, in separate passes, and argue each one against the plan before moving
on. It is weaker than independent critics — you're auditing your own work — so lean harder on
the checker and be slower to dismiss its warnings.

## Then, and only then

Schedule (`references/programming.md` §5). Record in `decision-log.md` anything the critique
changed, and any BLOCK you overrode with the reason. The next coach should be able to see not
just the week you shipped, but the week you rejected.
