# hyperhealth-skills

Agent skills for the HyperHealth / [CoachBridge](https://github.com/hyperbao/HyperHealth) ecosystem — an AI personal trainer and endurance coach.

## Install

```bash
npx skills add hyperbao/hyperhealth-skills --skill '*'
```

Install into a specific agent, globally:

```bash
npx skills add hyperbao/hyperhealth-skills --skill personal-trainer -a claude-code -g
```

List what's available without installing: append `--list`.

## Skills

| Skill | What it does |
|-------|--------------|
| `personal-trainer` | Long-term coaching: goals, training plans, weekly programming, check-ins, and progress logging. Keeps a persistent journal under `./journal/`. |
| `personal-trainer-running-expert` | Running-specific expertise the coach draws on: paces, HR zones, session design (easy/long/tempo/intervals), and periodization. |

## Data dependency

The `personal-trainer` skill reads health and workout data (sleep, HRV, resting HR, workouts, readiness) from the **CoachBridge MCP** and can schedule workouts to Apple Watch. For the data-driven features, connect the CoachBridge companion — see [hyperbao/HyperHealth](https://github.com/hyperbao/HyperHealth). Plain coaching works without it.
