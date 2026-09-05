#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""Validate a CoachBridge schedule_plan payload BEFORE it reaches the athlete's Watch.

Why this exists: the coach re-derives the same feasibility rules every week from prose in
the journal ("no key run within 48h of a big lower-body session", "protect the long run"),
and re-deriving them is exactly where it slips — a 90-minute long run followed the next
morning by a run with accelerations is a plan no athlete can execute, and no amount of
written guidance reliably catches it. These checks are mechanical, so a script enforces
them: same verdict every week, no judgment involved.

This checks *feasibility and load mechanics*, not coaching quality. Whether the week is the
right week for this athlete's goal is the critique phase's job (references/plan-critique.md);
this is the gate that runs first, and BLOCK findings must be fixed or explicitly overruled
with a logged reason before schedule_plan is called.

Usage:
    check_plan.py plan.json [--context ctx.json] [--week-start YYYY-MM-DD] [--json]
    check_plan.py --list-rules

Exit codes: 0 = clean (WARN/INFO only), 1 = at least one BLOCK, 2 = bad input.
"""
import json
import sys
import re
import argparse
import datetime as dt

EXIT_OK = 0
EXIT_BLOCKED = 1
EXIT_INPUT = 2  # bad path / not JSON / malformed payload (argparse also uses 2)

BLOCK, WARN, INFO = "BLOCK", "WARN", "INFO"
SEV_ORDER = {BLOCK: 0, WARN: 1, INFO: 2}

DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

STRENGTH_ACTIVITIES = {
    "functionalStrengthTraining", "traditionalStrengthTraining", "coreTraining",
    "crossTraining", "highIntensityIntervalTraining",
}
# Loosening / mobility work: real sessions, but they don't consume recovery, so they
# neither break a rest day nor extend a consecutive-training-day streak.
RECOVERY_ACTIVITIES = {
    "yoga", "flexibility", "preparationAndRecovery", "cooldown", "mindAndBody", "walking",
}
RUN_ACTIVITIES = {"running", "trailRunning", "treadmillRunning"}

# Keywords that mark a strength session as loading the legs — the ones that collide with
# running. Matched against title + note when the caller gives no explicit tag.
LOWER_BODY_HINTS = [
    "lower", "leg", "jambe", "squat", "lunge", "fente", "sled", "deadlift", "souleve",
    "soulevé", "hamstring", "ischio", "glute", "fessier", "quad", "calf", "mollet",
    "bas du corps", "posterior chain", "chaine post", "chaîne post", "step-up", "hip thrust",
]

DEFAULT_RULES = {
    # Sequencing — expressed as minimum gaps in calendar days. A gap of 1 means
    # "the next day", which is what most of these are designed to forbid.
    "min_days_between_hard": 2,            # quality -> quality
    "long_run_minutes": 75,                # at/over this, a run counts as a long run
    "long_run_heavy_minutes": 90,          # at/over this, even strides the next day are a BLOCK
    "min_days_after_long_run": 2,          # long run -> quality or strides
    "min_days_after_lower_body": 2,        # lower-body strength -> long run or quality
    "max_consecutive_training_days": 3,
    # Load
    "max_session_increase": 1,             # vs the trailing session count
    "max_volume_increase_pct": 10.0,       # vs the trailing weekly minutes
    "easy_share_min_pct": 75.0,            # share of running minutes that must be easy
    "require_rest_day": True,
    # Feasibility
    "max_session_minutes": None,           # number, or {"mon": 60, ..., "default": 60}
    "default_easy_pace_sec_per_km": 360,   # only used to turn distance goals into minutes
}

RULE_DOC = [
    ("SCHEMA", BLOCK, "Payload is structurally valid: ids present and unique, dates parseable "
                      "with an offset, goals carry the field their type requires, repeat >= 1, "
                      "pace strings are m:ss, HR zones are 1-5."),
    ("SEQ-HARD", BLOCK, "No two quality sessions closer than min_days_between_hard."),
    ("SEQ-LONG", BLOCK, "No quality within min_days_after_long_run of a long run. Strides too — "
                        "BLOCK when the long run was >= long_run_heavy_minutes, else WARN."),
    ("SEQ-STRENGTH", WARN, "No long run or quality within min_days_after_lower_body of a "
                           "lower-body strength session."),
    ("SEQ-STREAK", BLOCK, "No more than max_consecutive_training_days without a rest day."),
    ("SEQ-DOUBLE", WARN, "Two loading sessions on the same calendar day."),
    ("SEQ-PRELONG", WARN, "The long run is not preceded by an easy or rest day."),
    ("LOAD-COUNT", WARN, "Session count exceeds the trailing count by more than max_session_increase."),
    ("LOAD-VOLUME", WARN, "Weekly minutes exceed the trailing average by more than max_volume_increase_pct."),
    ("LOAD-EASY", WARN, "Easy share of running minutes is below easy_share_min_pct."),
    ("LOAD-REST", BLOCK, "The week contains no rest day at all."),
    ("FEAS-DAY", BLOCK, "A session falls on a day the athlete is not available."),
    ("FEAS-LENGTH", BLOCK, "A session is longer than the athlete's session-length limit."),
    ("FEAS-WINDOW", WARN, "A session starts outside the athlete's window for that day."),
    ("FEAS-BUSY", WARN, "A session clashes with a known commitment from the calendar."),
    ("FEAS-WEEK", BLOCK, "A session falls outside the target week, or in the past."),
]

PACE_RE = re.compile(r"^\d{1,2}:[0-5]\d$")
GOAL_FIELD = {"time": "minutes", "distance": "meters", "energy": "kilocalories", "open": None}


def die(msg):
    """Clean input-error exit: message to stderr, documented exit code (2)."""
    print(msg, file=sys.stderr)
    sys.exit(EXIT_INPUT)


def load_json(path, what):
    try:
        with open(path) as fh:
            return json.load(fh)
    except FileNotFoundError:
        die("%s not found: %s" % (what, path))
    except json.JSONDecodeError as e:
        die("%s is not valid JSON (%s): %s" % (what, e, path))
    except OSError as e:
        die("could not read %s: %s" % (what, e))


def parse_dt(value):
    """Parse an ISO-8601 timestamp. Returns (datetime|None, error|None)."""
    if not isinstance(value, str):
        return None, "date is missing or not a string"
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")), None
    except ValueError:
        return None, "date is not ISO-8601 (%r)" % value


def hhmm(value):
    try:
        h, m = value.split(":")
        return int(h) * 60 + int(m)
    except (ValueError, AttributeError):
        return None


# ---------------------------------------------------------------- findings

def finding(sev, rule, sid, msg, fix=None):
    return {"severity": sev, "rule": rule, "session": sid, "message": msg, "fix": fix}


# ---------------------------------------------------------------- structure walk

def blocks_of(struct):
    b = struct.get("blocks")
    return b if isinstance(b, list) else []


def work_steps(struct):
    """Yield (repeat, work_step) for every repeat block that has a work step."""
    for block in blocks_of(struct):
        if not isinstance(block, dict):
            continue
        work = block.get("work")
        if isinstance(work, dict):
            yield int(block.get("repeat") or 1), work


def pace_seconds(step, rules):
    """Seconds per km implied by a step's pace alert, or the easy default."""
    alert = step.get("alert") or {}
    if alert.get("type") == "pace":
        vals = []
        for key in ("min", "max"):
            v = alert.get(key)
            if isinstance(v, str) and PACE_RE.match(v):
                vals.append(hhmm(v))
        if vals:
            return sum(vals) / len(vals)
    return rules["default_easy_pace_sec_per_km"]


def step_minutes(step, rules):
    """Duration of one step in minutes, or None when it can't be derived (open/energy)."""
    goal = step.get("goal") or {}
    kind = goal.get("type")
    if kind == "time":
        v = goal.get("minutes")
        return float(v) if isinstance(v, (int, float)) else None
    if kind == "distance":
        m = goal.get("meters")
        if isinstance(m, (int, float)):
            return (m / 1000.0) * pace_seconds(step, rules) / 60.0
    return None


def step_meters(step, rules):
    goal = step.get("goal") or {}
    if goal.get("type") == "distance" and isinstance(goal.get("meters"), (int, float)):
        return float(goal["meters"])
    if goal.get("type") == "time" and isinstance(goal.get("minutes"), (int, float)):
        return goal["minutes"] * 60.0 / pace_seconds(step, rules) * 1000.0
    return 0.0


def session_totals(struct, rules):
    """(minutes, meters, open_steps) across warmup + blocks + cooldown."""
    minutes, meters, open_steps = 0.0, 0.0, 0
    if not isinstance(struct, dict):
        return minutes, meters, open_steps
    for key in ("warmup", "cooldown"):
        step = struct.get(key)
        if isinstance(step, dict):
            m = step_minutes(step, rules)
            if m is None:
                open_steps += 1
            else:
                minutes += m
                meters += step_meters(step, rules)
    for block in blocks_of(struct):
        if not isinstance(block, dict):
            continue
        repeat = block.get("repeat")
        repeat = int(repeat) if isinstance(repeat, (int, float)) and repeat >= 1 else 1
        for key in ("work", "recovery"):
            step = block.get(key)
            if isinstance(step, dict):
                m = step_minutes(step, rules)
                if m is None:
                    open_steps += 1
                else:
                    minutes += m * repeat
                    meters += step_meters(step, rules) * repeat
    return minutes, meters, open_steps


def is_lower_body(sess, tags):
    """Does this strength session load the legs? Explicit tag wins; else keyword sniff."""
    explicit = tags.get(sess["id"])
    if explicit is not None:
        return any(str(t).lower() in ("lower", "lower-body", "legs") for t in explicit)
    haystack = " ".join(str(sess.get(k) or "") for k in ("title", "note", "id")).lower()
    return any(hint in haystack for hint in LOWER_BODY_HINTS)


def classify(sess, rules, tags):
    """Tag a session with load classes: quality / strides / long / easy / strength / recovery."""
    classes = set()
    activity = sess["activity"]
    struct = sess["structure"] if isinstance(sess["structure"], dict) else {}

    if activity in STRENGTH_ACTIVITIES:
        classes.add("strength")
        if is_lower_body(sess, tags):
            classes.add("lower-body")
        return classes
    if activity in RECOVERY_ACTIVITIES:
        classes.add("recovery")
        return classes

    for repeat, work in work_steps(struct):
        alert = work.get("alert") or {}
        goal = work.get("goal") or {}
        fast_alert = alert.get("type") in ("pace", "power")
        hard_hr = alert.get("type") == "hr" and isinstance(alert.get("zone"), (int, float)) \
            and alert["zone"] >= 4
        secs = (goal.get("minutes") or 0) * 60 if goal.get("type") == "time" else None
        meters = goal.get("meters") if goal.get("type") == "distance" else None
        short = (secs is not None and secs <= 60) or (meters is not None and meters <= 250)
        if fast_alert or hard_hr:
            classes.add("quality")
        elif short and repeat >= 3:
            # A handful of short reps tacked onto an otherwise easy run: neuromuscular
            # load, not a workout — but it is NOT recovery, which is the whole point.
            classes.add("strides")
        elif repeat >= 2:
            classes.add("quality")

    if not classes:
        classes.add("easy")
    if sess["minutes"] and sess["minutes"] >= rules["long_run_minutes"] and activity in RUN_ACTIVITIES:
        classes.add("long")
    return classes


# ---------------------------------------------------------------- schema

def check_step(step, where, sid, out):
    if not isinstance(step, dict):
        out.append(finding(BLOCK, "SCHEMA", sid, "%s is not an object" % where))
        return
    goal = step.get("goal")
    if not isinstance(goal, dict):
        out.append(finding(BLOCK, "SCHEMA", sid, "%s has no goal object" % where))
    else:
        kind = goal.get("type")
        if kind not in GOAL_FIELD:
            out.append(finding(BLOCK, "SCHEMA", sid,
                               "%s goal.type %r is not time/distance/energy/open" % (where, kind)))
        else:
            field = GOAL_FIELD[kind]
            if field and not isinstance(goal.get(field), (int, float)):
                out.append(finding(BLOCK, "SCHEMA", sid,
                                   "%s goal.type=%s requires a numeric %s" % (where, kind, field),
                                   "add %s to the goal" % field))
    alert = step.get("alert")
    if alert is None:
        return
    if not isinstance(alert, dict):
        out.append(finding(BLOCK, "SCHEMA", sid, "%s alert is not an object" % where))
        return
    kind = alert.get("type")
    if kind == "hr":
        zone = alert.get("zone")
        if not isinstance(zone, (int, float)) or not 1 <= zone <= 5:
            out.append(finding(BLOCK, "SCHEMA", sid,
                               "%s HR zone %r is outside 1-5" % (where, zone)))
    elif kind in ("pace", "power"):
        for key in ("min", "max"):
            v = alert.get(key)
            if v is None:
                continue
            if kind == "pace" and not (isinstance(v, str) and PACE_RE.match(v)):
                out.append(finding(BLOCK, "SCHEMA", sid,
                                   "%s pace.%s %r is not \"m:ss\"" % (where, key, v)))
        if alert.get("min") is None and alert.get("max") is None:
            out.append(finding(BLOCK, "SCHEMA", sid, "%s %s alert has neither min nor max" % (where, kind)))
    elif kind != "cadence":
        out.append(finding(BLOCK, "SCHEMA", sid,
                           "%s alert.type %r is not hr/pace/cadence/power" % (where, kind)))


def check_schema(raw, sid, out):
    """Structural checks on one raw session. Returns the parsed start datetime or None."""
    for field in ("id", "date", "activity"):
        if not raw.get(field):
            out.append(finding(BLOCK, "SCHEMA", sid or "(no id)", "missing required field %r" % field))

    when, err = parse_dt(raw.get("date"))
    if err:
        out.append(finding(BLOCK, "SCHEMA", sid, err))
    elif when.tzinfo is None:
        out.append(finding(BLOCK, "SCHEMA", sid, "date has no UTC offset — the Watch needs one",
                           "write it as 2026-07-06T07:00:00+02:00"))

    struct = raw.get("structure")
    if struct is None:
        out.append(finding(INFO, "SCHEMA", sid,
                           "no structure — treated as an unstructured placeholder"))
        return when
    if not isinstance(struct, dict):
        out.append(finding(BLOCK, "SCHEMA", sid, "structure is not an object"))
        return when

    for key in ("warmup", "cooldown"):
        if key in struct and struct[key] is not None:
            check_step(struct[key], key, sid, out)

    blocks = struct.get("blocks")
    if blocks is None:
        out.append(finding(INFO, "SCHEMA", sid, "structure has no blocks — warmup/cooldown only"))
        return when
    if not isinstance(blocks, list) or not blocks:
        out.append(finding(BLOCK, "SCHEMA", sid, "structure.blocks must be a non-empty array"))
        return when

    for i, block in enumerate(blocks):
        label = "blocks[%d]" % i
        if not isinstance(block, dict):
            out.append(finding(BLOCK, "SCHEMA", sid, "%s is not an object" % label))
            continue
        repeat = block.get("repeat", 1)
        if not isinstance(repeat, (int, float)) or repeat < 1:
            out.append(finding(BLOCK, "SCHEMA", sid, "%s repeat %r must be >= 1" % (label, repeat)))
        if not isinstance(block.get("work"), dict):
            out.append(finding(BLOCK, "SCHEMA", sid, "%s has no work step" % label))
        else:
            check_step(block["work"], label + ".work", sid, out)
        if block.get("recovery") is not None:
            check_step(block["recovery"], label + ".recovery", sid, out)
    return when


def normalize(plan, rules, tags, out):
    """Schema-check every session and return the ones we can reason about, date-sorted."""
    sessions = plan.get("sessions")
    if not isinstance(sessions, list):
        die("plan has no \"sessions\" array — expected the schedule_plan payload")
    if not sessions:
        die("plan contains no sessions")

    seen, normed = {}, []
    for i, raw in enumerate(sessions):
        if not isinstance(raw, dict):
            out.append(finding(BLOCK, "SCHEMA", "sessions[%d]" % i, "session is not an object"))
            continue
        sid = raw.get("id") or "sessions[%d]" % i
        if sid in seen:
            out.append(finding(BLOCK, "SCHEMA", sid, "duplicate id (also at sessions[%d])" % seen[sid],
                               "ids must be unique — reconciliation matches on them"))
        seen[sid] = i

        when = check_schema(raw, sid, out)
        if when is None:
            continue
        if when.tzinfo is None:
            # Already flagged as a BLOCK above. Pin it to UTC so the rest of the checks
            # still run — one malformed date shouldn't hide the week's real problems.
            when = when.replace(tzinfo=dt.timezone.utc)
        minutes, meters, open_steps = session_totals(raw.get("structure"), rules)
        sess = {
            "id": sid, "title": raw.get("title"), "note": raw.get("note"),
            "activity": raw.get("activity"), "structure": raw.get("structure"),
            "when": when, "date": when.date(), "minutes": round(minutes, 1) or None,
            "km": round(meters / 1000.0, 2) or None, "open_steps": open_steps,
        }
        sess["classes"] = classify(sess, rules, tags)
        normed.append(sess)

    normed.sort(key=lambda s: s["when"])
    return normed


# ---------------------------------------------------------------- sequencing

def label(sess):
    return sess["title"] or sess["id"]


def loading(sess):
    """Does this session consume recovery? Mobility and walks don't."""
    return "recovery" not in sess["classes"]


def check_sequencing(sessions, rules, out):
    hard = [s for s in sessions if "quality" in s["classes"]]
    for a, b in zip(hard, hard[1:]):
        gap = (b["date"] - a["date"]).days
        if gap < rules["min_days_between_hard"]:
            out.append(finding(
                BLOCK, "SEQ-HARD", b["id"],
                "quality %s is %s quality %s — hard days need %d clear day(s) between them"
                % (label(b), "on the same day as" if gap == 0 else "%d day(s) after" % gap,
                   label(a), rules["min_days_between_hard"] - 1),
                "move %s later, or downgrade it to easy" % label(b)))

    longs = [s for s in sessions if "long" in s["classes"]]
    for lr in longs:
        for s in sessions:
            gap = (s["date"] - lr["date"]).days
            if gap <= 0 or gap >= rules["min_days_after_long_run"]:
                continue
            after = "quality" in s["classes"], "strides" in s["classes"]
            if not any(after):
                continue
            heavy = lr["minutes"] and lr["minutes"] >= rules["long_run_heavy_minutes"]
            kind = "quality" if after[0] else "strides"
            sev = BLOCK if (after[0] or heavy) else WARN
            out.append(finding(
                sev, "SEQ-LONG", s["id"],
                "%s carries %s %d day(s) after the %s long run %s — legs are not there yet"
                % (label(s), kind, gap, "%d min" % lr["minutes"] if lr["minutes"] else "",
                   label(lr)),
                "make %s a flat easy run (no accelerations), or move it to +%d days"
                % (label(s), rules["min_days_after_long_run"])))

    lower = [s for s in sessions if "lower-body" in s["classes"]]
    for st in lower:
        for s in sessions:
            gap = (s["date"] - st["date"]).days
            if gap <= 0 or gap >= rules["min_days_after_lower_body"]:
                continue
            if not ({"quality", "long"} & s["classes"]):
                continue
            out.append(finding(
                WARN, "SEQ-STRENGTH", s["id"],
                "key run %s is %d day(s) after lower-body strength %s — expect DOMS "
                "through it" % (label(s), gap, label(st)),
                "separate them by %d day(s), or keep the run easy"
                % rules["min_days_after_lower_body"]))

    by_day = {}
    for s in sessions:
        by_day.setdefault(s["date"], []).append(s)
    for day, group in sorted(by_day.items()):
        loaders = [s for s in group if loading(s)]
        if len(loaders) > 1:
            out.append(finding(
                WARN, "SEQ-DOUBLE", loaders[1]["id"],
                "%s on %s: %s" % ("double session", day.isoformat(),
                                  " + ".join(label(s) for s in loaders)),
                "confirm the athlete wants a double, or split them across two days"))

    for lr in longs:
        prev = lr["date"] - dt.timedelta(days=1)
        before = [s for s in by_day.get(prev, []) if loading(s)]
        if any({"quality", "long", "lower-body"} & s["classes"] for s in before):
            out.append(finding(
                WARN, "SEQ-PRELONG", lr["id"],
                "the long run %s is preceded by %s — it should be run on fresh legs"
                % (label(lr), ", ".join(label(s) for s in before)),
                "put an easy or rest day in front of the long run"))

    train_days = sorted({s["date"] for s in sessions if loading(s)})
    streak, start = 0, None
    for i, day in enumerate(train_days):
        if i and (day - train_days[i - 1]).days == 1:
            streak += 1
        else:
            streak, start = 1, day
        if streak > rules["max_consecutive_training_days"]:
            out.append(finding(
                BLOCK, "SEQ-STREAK", None,
                "%d consecutive training days (%s to %s) — the limit is %d"
                % (streak, start.isoformat(), day.isoformat(),
                   rules["max_consecutive_training_days"]),
                "insert a rest day"))
            break


# ---------------------------------------------------------------- load

def check_load(sessions, rules, ctx, week_start, out):
    loaders = [s for s in sessions if loading(s)]
    total_minutes = sum(s["minutes"] or 0 for s in loaders)

    if rules["require_rest_day"] and week_start:
        week_days = {week_start + dt.timedelta(days=i) for i in range(7)}
        rest = week_days - {s["date"] for s in loaders}
        if not rest:
            out.append(finding(BLOCK, "LOAD-REST", None,
                               "no rest day anywhere in the week — every day carries a session",
                               "make at least one day genuinely off"))

    recent = ((ctx.get("recent") or {}).get("weeks")) or []
    prior = [w for w in recent if isinstance(w, dict)]
    if prior:
        counts = [w.get("sessions") for w in prior if isinstance(w.get("sessions"), (int, float))]
        mins = [w.get("minutes") for w in prior if isinstance(w.get("minutes"), (int, float))]
        if counts:
            base = max(counts[-3:])
            if len(loaders) > base + rules["max_session_increase"]:
                out.append(finding(
                    WARN, "LOAD-COUNT", None,
                    "%d sessions this week vs %d recently — that is +%d, over the +%d step"
                    % (len(loaders), base, len(loaders) - base, rules["max_session_increase"]),
                    "drop a session, or hold the count and add duration instead"))
        if mins and total_minutes:
            avg = sum(mins[-4:]) / len(mins[-4:])
            if avg > 0:
                jump = (total_minutes - avg) / avg * 100.0
                if jump > rules["max_volume_increase_pct"]:
                    out.append(finding(
                        WARN, "LOAD-VOLUME", None,
                        "%d min planned vs %d min trailing average — +%.0f%%, over the +%.0f%% step"
                        % (round(total_minutes), round(avg), jump, rules["max_volume_increase_pct"]),
                        "trim ~%d min, most cheaply off the easy runs"
                        % round(total_minutes - avg * (1 + rules["max_volume_increase_pct"] / 100.0))))

    runs = [s for s in loaders if s["activity"] in RUN_ACTIVITIES and s["minutes"]]
    run_minutes = sum(s["minutes"] for s in runs)
    if run_minutes:
        easy_minutes = sum(s["minutes"] for s in runs
                           if not ({"quality", "long"} & s["classes"]))
        share = easy_minutes / run_minutes * 100.0
        if share < rules["easy_share_min_pct"]:
            out.append(finding(
                WARN, "LOAD-EASY", None,
                "only %.0f%% of running minutes are easy (target >= %.0f%%) — the week leans hard"
                % (share, rules["easy_share_min_pct"]),
                "lengthen an easy run or downgrade a quality session"))


# ---------------------------------------------------------------- feasibility

def check_feasibility(sessions, rules, ctx, week_start, today, out):
    avail = ctx.get("availability") or {}
    days = [str(d).lower()[:3] for d in (avail.get("days") or [])]
    windows = {str(k).lower()[:3]: v for k, v in (avail.get("windows") or {}).items()}
    limits = rules["max_session_minutes"] or avail.get("max_session_minutes")

    def limit_for(dow):
        """A session-length cap, either flat or per-day. Most athletes have a tight
        weekday-morning cap and a loose weekend — a flat cap would flag every long run."""
        if isinstance(limits, dict):
            v = limits.get(dow, limits.get("default"))
            return v if isinstance(v, (int, float)) else None
        return limits if isinstance(limits, (int, float)) else None

    for s in sessions:
        dow = DAYS[s["date"].weekday()]
        limit = limit_for(dow)

        if week_start:
            offset = (s["date"] - week_start).days
            if not 0 <= offset < 7:
                out.append(finding(
                    BLOCK, "FEAS-WEEK", s["id"],
                    "%s is on %s, outside the target week starting %s"
                    % (label(s), s["date"].isoformat(), week_start.isoformat()),
                    "schedule one week at a time"))
        if today and s["date"] < today:
            out.append(finding(BLOCK, "FEAS-WEEK", s["id"],
                               "%s is dated %s, in the past" % (label(s), s["date"].isoformat())))

        if days and dow not in days and loading(s):
            out.append(finding(
                BLOCK, "FEAS-DAY", s["id"],
                "%s falls on %s, which is not in the athlete's available days (%s)"
                % (label(s), dow, ", ".join(days)),
                "move it to an available day"))

        if limit and s["minutes"] and s["minutes"] > limit:
            out.append(finding(
                BLOCK, "FEAS-LENGTH", s["id"],
                "%s runs %d min, over the %d min limit for a %s session"
                % (label(s), round(s["minutes"]), limit, dow),
                "shorten it, or move it to a day with more room (weekend)"))

        window = windows.get(dow)
        if window and len(window) == 2 and loading(s):
            start_min = s["when"].hour * 60 + s["when"].minute
            lo, hi = hhmm(window[0]), hhmm(window[1])
            end_min = start_min + (s["minutes"] or 0)
            if lo is not None and hi is not None and (start_min < lo or end_min > hi):
                out.append(finding(
                    WARN, "FEAS-WINDOW", s["id"],
                    "%s runs %s-%s, outside the %s window %s-%s"
                    % (label(s), "%02d:%02d" % divmod(start_min, 60),
                       "%02d:%02d" % divmod(int(end_min), 60), dow, window[0], window[1])))

    for busy in ctx.get("busy") or []:
        if not isinstance(busy, dict):
            continue
        bs, _ = parse_dt(busy.get("start"))
        be, _ = parse_dt(busy.get("end"))
        if not bs or not be:
            continue
        bs = bs if bs.tzinfo else bs.replace(tzinfo=dt.timezone.utc)
        be = be if be.tzinfo else be.replace(tzinfo=dt.timezone.utc)
        for s in sessions:
            if not s["minutes"]:
                continue
            se = s["when"] + dt.timedelta(minutes=s["minutes"])
            if s["when"] < be and se > bs:
                out.append(finding(
                    WARN, "FEAS-BUSY", s["id"],
                    "%s overlaps %s" % (label(s), busy.get("label") or "a calendar commitment")))


# ---------------------------------------------------------------- report

def summarize(sessions):
    rows = []
    for s in sessions:
        tags = ",".join(sorted(s["classes"]))
        dur = "%d min" % round(s["minutes"]) if s["minutes"] else "—"
        km = "%.1f km" % s["km"] if s["km"] else ""
        rows.append("  %s %s  %-26s %-22s %8s %8s"
                    % (DAYS[s["date"].weekday()], s["date"].isoformat(),
                       (label(s) or "")[:26], tags[:22], dur, km))
    return rows


def report(findings, sessions, week_start):
    print("PLAN CHECK" + ("  ·  week of %s" % week_start.isoformat() if week_start else ""))
    print("=" * 78)
    if sessions:
        print("\nSessions (%d)" % len(sessions))
        print("  day date         label                      load                    dur      dist")
        for row in summarize(sessions):
            print(row)

    findings = sorted(findings, key=lambda f: (SEV_ORDER[f["severity"]], f["rule"]))
    counts = {BLOCK: 0, WARN: 0, INFO: 0}
    for f in findings:
        counts[f["severity"]] += 1

    print("\nFindings: %d BLOCK · %d WARN · %d INFO" % (counts[BLOCK], counts[WARN], counts[INFO]))
    if not findings:
        print("  none — the plan is mechanically sound.")
    for f in findings:
        who = " [%s]" % f["session"] if f["session"] else ""
        print("\n  %-5s %-13s%s\n    %s" % (f["severity"], f["rule"], who, f["message"]))
        if f["fix"]:
            print("    → %s" % f["fix"])

    print("\n" + "=" * 78)
    if counts[BLOCK]:
        print("BLOCKED — fix the %d BLOCK finding(s), or overrule one explicitly and record the"
              % counts[BLOCK])
        print("reason in decision-log.md. Do not call schedule_plan until this is clean.")
    else:
        print("PASS — no blocking issue. Warnings are judgment calls: answer them in the")
        print("critique phase (references/plan-critique.md) before scheduling.")


def main():
    ap = argparse.ArgumentParser(
        description="Validate a CoachBridge schedule_plan payload before scheduling it.")
    ap.add_argument("plan", nargs="?", help="path to the plan JSON ({\"sessions\": [...]})")
    ap.add_argument("--context", "-c", help="athlete context JSON (availability, recent load, rules)")
    ap.add_argument("--week-start", help="Monday of the target week, YYYY-MM-DD (overrides context)")
    ap.add_argument("--today", help="treat this date as today, YYYY-MM-DD (default: no past check)")
    ap.add_argument("--json", action="store_true", dest="as_json", help="emit findings as JSON")
    ap.add_argument("--list-rules", action="store_true", help="print the rule set and exit")
    args = ap.parse_args()

    if args.list_rules:
        print("%-14s %-6s %s" % ("RULE", "SEV", "CHECKS"))
        for rule, sev, doc in RULE_DOC:
            print("%-14s %-6s %s" % (rule, sev, doc))
        print("\nThresholds are overridable per athlete under \"rules\" in the context file:")
        for k, v in DEFAULT_RULES.items():
            print("  %-38s %s" % (k, v))
        return EXIT_OK

    if not args.plan:
        ap.error("a plan JSON path is required (or --list-rules)")

    plan = load_json(args.plan, "plan")
    ctx = load_json(args.context, "context") if args.context else {}
    if not isinstance(ctx, dict):
        die("context must be a JSON object")

    rules = dict(DEFAULT_RULES)
    for k, v in (ctx.get("rules") or {}).items():
        if k in rules:
            rules[k] = v
        else:
            print("warning: unknown rule %r in context — ignored" % k, file=sys.stderr)
    tags = ctx.get("session_tags") or {}

    week_start = None
    raw_week = args.week_start or ctx.get("week_start")
    if raw_week:
        try:
            week_start = dt.date.fromisoformat(raw_week)
        except ValueError:
            die("--week-start must be YYYY-MM-DD, got %r" % raw_week)
        if week_start.weekday() != 0:
            print("warning: week_start %s is a %s, not a Monday"
                  % (week_start, DAYS[week_start.weekday()]), file=sys.stderr)
    today = None
    if args.today:
        try:
            today = dt.date.fromisoformat(args.today)
        except ValueError:
            die("--today must be YYYY-MM-DD, got %r" % args.today)

    findings = []
    sessions = normalize(plan, rules, tags, findings)
    if sessions:
        check_sequencing(sessions, rules, findings)
        check_load(sessions, rules, ctx, week_start, findings)
        check_feasibility(sessions, rules, ctx, week_start, today, findings)

    blocked = any(f["severity"] == BLOCK for f in findings)
    if args.as_json:
        print(json.dumps({
            "blocked": blocked,
            "week_start": week_start.isoformat() if week_start else None,
            "sessions": [{"id": s["id"], "title": s["title"], "date": s["date"].isoformat(),
                          "activity": s["activity"], "classes": sorted(s["classes"]),
                          "minutes": s["minutes"], "km": s["km"]} for s in sessions],
            "findings": findings,
        }, indent=2, ensure_ascii=False))
    else:
        report(findings, sessions, week_start)
    return EXIT_BLOCKED if blocked else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
