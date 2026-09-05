# Weekly check-in — ask before you interpret

The data tells you what the body did. It does not tell you what the week *cost*. Sleep,
HRV and resting HR can all sit inside their normal band while an athlete is quietly
sliding into overreaching — the first signals are subjective (motivation, mood, heaviness,
dread) and arrive **before** the physiology moves.

The athlete does not reliably leave feedback in the app. So you ask. This is the coach's
half of the weekly loop, and it runs **before** you interpret the week, write the log, or
draft next week — those all depend on the answers.

## Where it sits

Data pull → **check-in (this file)** → interpret → decide → program → log. It is a **gate**:
if the answers aren't in, don't write the weekly log, don't draft next week, and don't
schedule anything. Post the questions and pick the review back up when they reply. (If a
recurring routine ran this unattended, that's exactly what it should do: ask, then stop.)

## Ask like a coach, not like a form

- **One message, a handful of questions, in their language and tone** (`client-profile.md`).
  Never a numbered questionnaire of ten items.
- **Ask what you don't already know.** Pull `get_feedback` for the week first. Any session
  they've already commented on is answered — don't re-ask it. Name the ones they skipped.
- **Be specific — reference the actual week.** "Jeudi tu as couru 20 s/km plus lentement à
  la même FC — c'était quoi ?" lands as coaching. "How was your week?" gets "fine."
- **Let them talk.** Invite a number (`sur 5`) as a shortcut for the core items, but accept
  prose and score it yourself. A rich sentence beats a digit.
- **React, then stop.** One round of follow-ups on whatever they flagged, and you're done.

## The core four — asked every week, so they trend

These four are the ones that move first. Score each **1–5, where 1 is good and 5 is a
problem**, and record them in the weekly log whether the athlete gave the number or you
inferred it from what they wrote (mark inferred scores as such).

| Item | Ask about | 1 | 5 |
|------|-----------|---|---|
| **Fatigue** | overall tiredness across the week, not today | fresh | wiped out |
| **Motivation** | appetite for the next session | keen to train | dreading it |
| **Soreness / niggles** | heaviness, aches, anything that changed how they move | nothing | constant, or altering gait |
| **Life load** | work, sleep pressure, stress outside training | calm week | swamped |

**Motivation is the one to watch.** A drop in appetite for training, with everything else
looking normal, is the earliest reliable marker of accumulated fatigue — earlier than HRV.

## Then the specific questions

Build 2–4 more from what the data actually showed this week. Good triggers:

- **A session with no feedback** — especially the key session. "How did the long run feel
  in the last 20 minutes?"
- **A data anomaly you can't explain** — HR high for the usual pace, a session cut short, a
  pace that fell off, a night far from baseline. Ask what was going on.
- **A missed or moved session** — why, without judgement. The reason matters more than the miss.
- **An open niggle from the profile** — ask about it *every* week until it resolves. For a
  known flag, ask the back-off criteria directly ("est-ce que ça a tiré *pendant* la course,
  ou seulement après ?"), not a vague "how's the psoas?"
- **Next week's shape** — the agenda, if they share it weekly rather than via the Calendar MCP.

## Reading the answers

- **The athlete's report overrides the data.** If they say they're cooked and every marker
  looks fine, they're cooked. Back off. The reverse also holds: don't manufacture fatigue
  the athlete doesn't feel because a single HRV reading dipped.
- **Combine, don't average.** Subjective and physiological agreeing is a strong signal;
  disagreeing is information — usually it means one of them is early.
- **Trend the four against their own history**, not against 1–5 in the abstract. A 3 for
  someone who lives at 2 is a real move.

### Overreaching screen — run it every week

Back off *now*, and say why, when you see any of these:

- **Motivation ≥ 4 for two weeks running**, whatever the data says.
- **Fatigue ≥ 4 together with** resting HR above baseline **or** HRV below its band, sustained.
- **Elevated RPE at familiar paces** — the same run costing more — over more than one session.
- **Sleep getting worse while fatigue rises.** Wired-and-tired is a classic overreaching sign,
  not a sleep-hygiene problem to coach around.
- **Soreness that hasn't settled in 72h**, or any niggle now felt *during* activity.
- **Load climbing three weeks or more with no deload**, even when everything reads fine —
  that's the week to insert one, not the week after something breaks.

Backing off means cutting *intensity first*, then volume: downgrade quality to easy, hold or
trim the long run, keep the week's frequency if you can. Log the decision and its trigger in
`decision-log.md`, and tell the athlete plainly what you changed and why.

## Recording it

Into `journal/weekly/<ISO-week>.md` (the **Check-in** block): the four scores with a marker
for inferred ones, a one-line summary in the athlete's own words, which sessions the feedback
covered, and any overreaching flag that fired. Derived values only — same rule as everywhere
else.

Once a month or so, refresh the **Subjective baseline** in `client-profile.md` so "normal
for this athlete" stays current. If a niggle resolves or a new one appears, update the
profile the same day.

## If they don't answer

Ask once, clearly. Don't nag mid-week. Nothing gets written or scheduled until they reply —
a plan built without the subjective read is the plan that stacks a hard session onto a week
the athlete was already finished by. If the week starts before they answer, carry the
previous week forward unchanged rather than guessing a progression.
