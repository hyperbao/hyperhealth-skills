#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""Post-process a CoachBridge get_workout() payload into a compact DERIVED analysis.

Why this exists: get_workout() with time-series almost always overflows the tool-result
context limit and gets spilled to a .txt file. This script reads that file and emits only
derived values (splits, dynamics, decoupling, HR distribution) — never raw samples — so the
analysis can go straight into the journal (which stores derived values only). Output is
small and bounded regardless of session length, by design.

Recommended call: get_workout(id, series=[...], splits="km", resolution=10|30).
Passing splits="km" gives clean even-km splits that this script's decoupling relies on.

Zone/pace *derivation* from a benchmark is deliberately NOT here — that's a once-per-
benchmark decision that belongs in training-plan.md.
"""
import json
import sys
import argparse
import datetime as dt

EXIT_OK = 0
EXIT_INPUT = 2  # bad path / not JSON / malformed payload (argparse also uses 2)


def T(z):
    return dt.datetime.fromisoformat(z.replace("Z", "+00:00"))


def mmss(sec):
    if sec is None:
        return "—"
    sec = round(sec)
    sign = "-" if sec < 0 else ""
    sec = abs(sec)
    return f"{sign}{sec // 60}:{sec % 60:02d}"


def rnd(x, n=0):
    if x is None:
        return None
    return int(round(x)) if n == 0 else round(x, n)


def die(msg):
    """Clean input-error exit: message to stderr, documented exit code (2)."""
    print(msg, file=sys.stderr)
    sys.exit(EXIT_INPUT)


def warn(model, msg):
    model["warnings"].append(msg)
    print(msg, file=sys.stderr)


def load(path):
    """Read + parse the payload, with clean errors (never a raw traceback)."""
    try:
        raw = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
    except FileNotFoundError:
        die(f"Error: file not found: {path}\n"
            f"       Pass the .txt file that get_workout() spilled to, or '-' for stdin.")
    except OSError as e:
        die(f"Error: cannot read {path}: {e}")
    try:
        d = json.loads(raw)
    except json.JSONDecodeError as e:
        die(f"Error: {path} is not valid JSON ({e}). Expected a get_workout() payload.")
    d = d if "summary" in d else {"summary": d, "series": d.get("series", [])}
    if not isinstance(d.get("summary"), dict) or "start" not in d["summary"]:
        die("Error: payload has no usable 'summary' (missing 'start'). "
            "Is this a get_workout() response?")
    return d


class Series:
    """Lazy accessors over series[]. Cadence is already steps/min (both feet) in
    HealthKit — never double it."""

    def __init__(self, arr):
        self.by = {x["key"]: [(T(p["date"]), p["value"]) for p in x.get("points", [])]
                   for x in (arr or [])}

    def avg(self, key, a, b):
        v = [val for (t, val) in self.by.get(key, []) if a <= t < b]
        return sum(v) / len(v) if v else None

    def mx(self, key, a, b):
        v = [val for (t, val) in self.by.get(key, []) if a <= t < b]
        return max(v) if v else None


def split_pace(sp):
    if sp.get("averagePaceSecondsPerKm"):
        return sp["averagePaceSecondsPerKm"]
    dm = sp.get("distanceMeters") or 0
    return sp["durationSeconds"] / (dm / 1000) if dm else None


# ---- compute: each returns plain data (the model), no printing ----------------

def build_overview(s, ser):
    t0, te = T(s["start"]), T(s["end"])
    dist = s.get("totalDistanceMeters", 0)
    dur = s["duration"]
    return {
        "start_local": (t0 + dt.timedelta(hours=2)).strftime("%a %Y-%m-%d %H:%M"),
        "activity_type": s.get("activityType"),
        "distance_km": rnd(dist / 1000, 2),
        "duration_s": rnd(dur),
        "avg_pace_s_per_km": rnd(dur / (dist / 1000)) if dist else None,
        "hr_avg": rnd(s.get("averageHeartRate")),
        "hr_max": rnd(s.get("maxHeartRate")),
        "energy_kcal": rnd(s.get("totalEnergyKilocalories")),
        "power_w": rnd(s.get("averageRunningPowerWatts")),
        "stride_m": rnd(s.get("averageRunningStrideLengthMeters"), 2),
        "cadence_spm": rnd(ser.avg("cadence", t0, te)),
        "elevation_m": rnd(s.get("elevationAscendedMeters")),
        "hr_recovery_1min": s.get("heartRateRecovery"),
    }


def build_splits(s, ser, model):
    sp = s.get("splits") or []
    if not sp:
        warn(model, "note: no splits in payload — pass splits=\"km\" to get_workout for per-km detail.")
        return []
    out = []
    for x in sp:
        a, b = T(x["start"]), T(x["end"])
        out.append({
            "label": x.get("label", "?"),
            "distance_m": rnd(x.get("distanceMeters")),
            "pace_s_per_km": rnd(split_pace(x)),
            "hr": rnd(x.get("averageHeartRate")),
            "cadence": rnd(ser.avg("cadence", a, b)),
            "stride": rnd(ser.avg("stride", a, b), 2),
            "power": rnd(ser.avg("power", a, b)),
            "gct_ms": rnd(ser.avg("groundContact", a, b)),
            "vo_cm": rnd(ser.avg("verticalOscillation", a, b), 1),
        })
    return out


def build_decoupling(s, model):
    sp = [x for x in (s.get("splits") or [])
          if x.get("distanceMeters") and x.get("averageHeartRate")]
    if len(sp) < 2:
        return None
    sp = sorted(sp, key=lambda x: T(x["start"]))
    total = sum(x["distanceMeters"] for x in sp)
    cut, best_err, cum = 1, float("inf"), 0.0
    for i, x in enumerate(sp[:-1]):
        cum += x["distanceMeters"]
        err = abs(cum - total / 2)
        if err < best_err:
            best_err, cut = err, i + 1
    h1, h2 = sp[:cut], sp[cut:]
    if not h1 or not h2:
        return None

    def stat(g):
        d = sum(x["distanceMeters"] for x in g)
        t = sum(x["durationSeconds"] for x in g)
        hr = sum(x["averageHeartRate"] * x["durationSeconds"] for x in g) / t
        return {"distance_km": rnd(d / 1000, 2), "pace_s_per_km": rnd(t / (d / 1000)),
                "hr": rnd(hr, 1), "_spd": d / t, "_hr": hr}

    a, b = stat(h1), stat(h2)
    pct = (a["_spd"] / a["_hr"] - b["_spd"] / b["_hr"]) / (a["_spd"] / a["_hr"]) * 100
    return {"h1": {k: v for k, v in a.items() if not k.startswith("_")},
            "h2": {k: v for k, v in b.items() if not k.startswith("_")},
            "decoupling_pct": rnd(pct, 1)}


def build_hr_distribution(ser, te, fcmax, rhr, model):
    pts = sorted(ser.by.get("hr", []))
    if not pts:
        return None
    durs = []
    for i, (t, v) in enumerate(pts):
        nxt = pts[i + 1][0] if i + 1 < len(pts) else te
        durs.append(min((nxt - t).total_seconds(), 60))
    tot = sum(durs) or 1
    Z = [("Z1", .50, .60), ("Z2", .60, .70), ("Z3", .70, .80), ("Z4", .80, .90), ("Z5", .90, 1.01)]
    if fcmax and rhr:
        res = fcmax - rhr
        mode = "karvonen_hrr"
        bands = [(n, rhr + lo * res, rhr + hi * res) for n, lo, hi in Z]
    elif fcmax:
        mode = "pct_hrmax"
        bands = [(n, lo * fcmax, hi * fcmax) for n, lo, hi in Z]
    else:
        mode = "buckets_10bpm"
        lo = int(min(v for _, v in pts) // 10 * 10)
        hi = int(max(v for _, v in pts) // 10 * 10 + 10)
        bands = [(f"{b}-{b + 10}", b, b + 10) for b in range(lo, hi, 10)]
    rows = []
    for name, blo, bhi in bands:
        z = sum(dr for (t, v), dr in zip(pts, durs) if blo <= v < bhi)
        rows.append({"name": name, "lo": rnd(blo), "hi": rnd(bhi),
                     "seconds": rnd(z), "pct": rnd(100 * z / tot)})
    return {"mode": mode, "bands": rows}


def build_thirds(s, ser):
    sp = [x for x in (s.get("splits") or [])
          if x.get("distanceMeters") and x.get("averageHeartRate")]
    if len(sp) < 3:
        return []
    sp = sorted(sp, key=lambda x: T(x["start"]))
    n = len(sp)
    groups = [("early", sp[:n // 3]), ("mid", sp[n // 3:2 * n // 3]), ("late", sp[2 * n // 3:])]
    out = []
    for label, g in groups:
        if not g:
            continue
        d = sum(x["distanceMeters"] for x in g)
        t = sum(x["durationSeconds"] for x in g)
        hr = sum(x["averageHeartRate"] * x["durationSeconds"] for x in g) / t
        a, b = T(g[0]["start"]), T(g[-1]["end"])
        out.append({"name": label, "pace_s_per_km": rnd(t / (d / 1000)), "hr": rnd(hr),
                    "cadence": rnd(ser.avg("cadence", a, b)), "gct_ms": rnd(ser.avg("groundContact", a, b))})
    return out


def build_best(s, ser, meters, model):
    dpts = sorted(ser.by.get("distance", []))
    if not dpts:
        warn(model, f"note: --best needs the 'distance' series — re-run get_workout with "
                    f"series including \"distance\".")
        return None
    cum, tot = [], 0.0
    for t, v in dpts:
        tot += v
        cum.append((t, tot))

    def t_at(target):
        for i in range(1, len(cum)):
            if cum[i][1] >= target:
                (ta, da), (tb, db) = cum[i - 1], cum[i]
                f = (target - da) / (db - da) if db > da else 0
                return ta + dt.timedelta(seconds=(tb - ta).total_seconds() * f)
        return None

    best = None
    for i in range(len(cum)):
        target = cum[i][1] + meters
        if target > cum[-1][1]:
            break
        te = t_at(target)
        el = (te - cum[i][0]).total_seconds()
        if best is None or el < best[0]:
            best = (el, cum[i][0], te, cum[i][1])
    if not best:
        warn(model, f"note: session shorter than {meters:.0f} m — no continuous block found.")
        return None
    el, ts, te, dstart = best
    splits = []
    prev, k = ts, 1
    while 1000 * k <= meters:
        tk = t_at(dstart + 1000 * k) or te
        splits.append({"km": k, "seconds": rnd((tk - prev).total_seconds()),
                       "hr_avg": rnd(ser.avg("hr", prev, tk)), "hr_max": rnd(ser.mx("hr", prev, tk)),
                       "cadence": rnd(ser.avg("cadence", prev, tk)),
                       "stride": rnd(ser.avg("stride", prev, tk), 2), "power": rnd(ser.avg("power", prev, tk))})
        prev = tk
        k += 1
    mid = ts + dt.timedelta(seconds=el / 2)
    l20 = max(te - dt.timedelta(minutes=20), ts)
    return {
        "meters": meters, "seconds": rnd(el), "pace_s_per_km": rnd(el / (meters / 1000)),
        "starts_at_km": rnd(dstart / 1000, 2), "splits": splits,
        "hr": {"avg": rnd(ser.avg("hr", ts, te)), "max": rnd(ser.mx("hr", ts, te)),
               "first_half": rnd(ser.avg("hr", ts, mid)), "second_half": rnd(ser.avg("hr", mid, te))},
        "lthr_proxy": rnd(ser.avg("hr", l20, te)),
        "cadence_spm": rnd(ser.avg("cadence", ts, te)), "stride_m": rnd(ser.avg("stride", ts, te), 2),
    }


def analyze(d, best_m, fcmax, rhr):
    s, ser = d["summary"], Series(d.get("series"))
    te = T(s["end"])
    model = {"warnings": []}
    model["overview"] = build_overview(s, ser)
    model["splits"] = build_splits(s, ser, model)
    model["decoupling"] = build_decoupling(s, model)
    model["hr_distribution"] = build_hr_distribution(ser, te, fcmax, rhr, model)
    model["thirds"] = build_thirds(s, ser)
    model["best"] = build_best(s, ser, best_m, model) if best_m else None
    return model


# ---- render: text (diagnostics already went to stderr) ------------------------

def render_text(m):
    o = m["overview"]
    out = ["=" * 64, "OVERVIEW", "=" * 64,
           f"  start {o['start_local']} (local+02)   activityType {o['activity_type']}",
           f"  {o['distance_km']} km   {mmss(o['duration_s'])}"
           + (f"   avg {mmss(o['avg_pace_s_per_km'])}/km" if o['avg_pace_s_per_km'] else ""),
           f"  HR avg {o['hr_avg'] or '—'}  max {o['hr_max'] or '—'}   energy {o['energy_kcal'] or '—'} kcal"]
    if o["power_w"] is not None:
        out.append(f"  power {o['power_w']} W   stride {o['stride_m']} m   cadence {o['cadence_spm']} spm")
    if o["elevation_m"] is not None:
        out.append(f"  elevation +{o['elevation_m']} m")
    out.append(f"  HR recovery (1 min): {o['hr_recovery_1min']}")

    if m["splits"]:
        out += ["", "=" * 64, "SPLITS  (pace, HR + aligned running dynamics)", "=" * 64,
                f"{'#':>3} {'pace':>6} {'HR':>4} {'cad':>4} {'strd':>5} {'pwr':>4} {'GCT':>4} {'VO':>4}"]
        for x in m["splits"]:
            dash = lambda v, s="{}": ("  —" if v is None else s.format(v))
            tag = "" if (x["distance_m"] or 0) >= 990 else f"  ({x['distance_m']:.0f}m)"
            out.append(f"{x['label']:>3} {mmss(x['pace_s_per_km']):>6} {dash(x['hr']):>4} "
                       f"{dash(x['cadence']):>4} {dash(x['stride'],'{:.2f}'):>5} {dash(x['power']):>4} "
                       f"{dash(x['gct_ms']):>4} {dash(x['vo_cm'],'{:.1f}'):>4}{tag}")

    if m["decoupling"]:
        dc = m["decoupling"]
        out += ["", "=" * 64, "AEROBIC DECOUPLING (Pa:HR)", "=" * 64,
                f"  H1 {dc['h1']['distance_km']} km  pace {mmss(dc['h1']['pace_s_per_km'])}  HR {dc['h1']['hr']}",
                f"  H2 {dc['h2']['distance_km']} km  pace {mmss(dc['h2']['pace_s_per_km'])}  HR {dc['h2']['hr']}",
                f"  decoupling {dc['decoupling_pct']:+.1f}%   (<5% = well-aerobic; contaminated by any warm-up/cool-down in the splits)"]

    if m["hr_distribution"]:
        hd = m["hr_distribution"]
        title = {"karvonen_hrr": "HR TIME-IN-ZONE (Karvonen %HRR)",
                 "pct_hrmax": "HR TIME-IN-ZONE (%HRmax)",
                 "buckets_10bpm": "HR DISTRIBUTION (10-bpm buckets)"}[hd["mode"]]
        out += ["", "=" * 64, title, "=" * 64]
        for b in hd["bands"]:
            out.append(f"  {b['name']:>7} {b['lo']:>4.0f}-{b['hi']:<4.0f} {mmss(b['seconds']):>6} "
                       f"{b['pct']:4.0f}%  {'#' * round(30 * b['pct'] / 100)}")

    if m["thirds"]:
        out += ["", "=" * 64, "DRIFT BY THIRDS", "=" * 64]
        for t in m["thirds"]:
            out.append(f"  {t['name']:>5}: pace {mmss(t['pace_s_per_km'])}  HR {t['hr']}  "
                       f"cad {t['cadence'] or '—'}  GCT {t['gct_ms'] or '—'}")

    if m["best"]:
        bt = m["best"]
        out += ["", "=" * 64,
                f"BEST CONTINUOUS {bt['meters']:.0f} m  =  {mmss(bt['seconds'])}   ({mmss(bt['pace_s_per_km'])}/km)",
                "=" * 64, f"  starts at {bt['starts_at_km']} km into the session",
                f"  {'km':>3} {'time':>6} {'HRavg':>6} {'HRmax':>6} {'cad':>4} {'strd':>5} {'pwr':>4}"]
        for x in bt["splits"]:
            out.append(f"  {x['km']:>3} {mmss(x['seconds']):>6} {x['hr_avg'] or '—':>6} {x['hr_max'] or '—':>6} "
                       f"{x['cadence'] or '—':>4} {('%.2f' % x['stride']) if x['stride'] else '—':>5} "
                       f"{x['power'] or '—':>4}")
        h = bt["hr"]
        out.append(f"  HR: avg {h['avg']}  max {h['max']}  1st half {h['first_half']}  2nd half {h['second_half']}")
        out.append(f"  LTHR proxy (avg HR last 20 min of effort): {bt['lthr_proxy']} bpm")
        out.append(f"  cadence {bt['cadence_spm']} spm  stride {bt['stride_m']} m")
    return "\n".join(out)


EPILOG = """\
Examples:
  analyze_workout.py workout.txt
  analyze_workout.py workout.txt --best 5000                 # isolate a 5 km time-trial
  analyze_workout.py workout.txt --fcmax 179 --rhr 48        # HR time-in-zone (Karvonen)
  analyze_workout.py workout.txt --json | jq .best.pace_s_per_km
  get_workout spilled to a file? pass that file (or '-' to pipe the JSON via stdin).

Exit codes:
  0  success
  2  bad input (file not found, not JSON, or not a get_workout payload) / bad arguments

Notes:
  Structured data goes to stdout; diagnostics (missing-series notes) go to stderr.
  Call get_workout with splits="km" so decoupling has clean 50/50 halves.
"""


def main():
    ap = argparse.ArgumentParser(
        prog="analyze_workout.py",
        description="Derived analysis of a CoachBridge get_workout() payload (no raw samples).",
        epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="path to the get_workout JSON, or '-' to read stdin")
    ap.add_argument("--best", type=float, metavar="METERS",
                    help="isolate & analyze the fastest continuous METERS (e.g. 5000 for a 5 km test)")
    ap.add_argument("--fcmax", type=float, metavar="BPM", help="render HR time-in-zone (5 zones)")
    ap.add_argument("--rhr", type=float, metavar="BPM", help="resting HR -> use Karvonen %%HRR zones (needs --fcmax)")
    ap.add_argument("--json", action="store_true", help="emit the full model as JSON on stdout (composable with jq)")
    a = ap.parse_args()
    if a.rhr and not a.fcmax:
        ap.error("--rhr requires --fcmax")

    model = analyze(load(a.path), a.best, a.fcmax, a.rhr)
    if a.json:
        print(json.dumps(model, ensure_ascii=False, indent=2))
    else:
        print(render_text(model))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
