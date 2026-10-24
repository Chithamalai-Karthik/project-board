# The roadmap format

The project board (`board/index.html`) reads `ROADMAP.md` in the project folder. These are the only rules it relies
on. Everything else in the file (decisions, notes, other sections and tables) is free text that the board ignores.
Check a roadmap with `python roadmap.py check ROADMAP.md`.

## Title, description and dates

```markdown
# Lumen roadmap

Short intro. Last updated 20 October 2026.

## About the project

The one-line description: the board shows it in bold at the top.

Each further paragraph shows under "About the project" on the board.

## Schedule

**Schedule:** start 2026-10-20 · end 2026-12-18 · 60 days, 44 working days (5 days a week) · effort S=1 M=3 L=5 XL=10 working days · off 2026-12-25
```

- **Title:** the first `# ` heading. A trailing "roadmap" is dropped, so the board above is called "Lumen board".
- **Last updated:** "Last updated <date>." anywhere. The board shows it under the title.
- **About the project:** paragraphs under `## About the project`, until the next heading.
- **Schedule:** one line starting `**Schedule:**`, with `start YYYY-MM-DD` and `end YYYY-MM-DD`. The board draws the
  timeline from it. The rest is for people and for `roadmap.py schedule`: days a week, the effort sizes and days off.

## Phases

```markdown
## Phase A: the core app (anything in brackets is left off the board)
```

- `## Phase <ID>: <title>`. The ID is letters or digits (`0`, `A`, `B`, `1`, `2`). Phases are coloured in the order
  they appear (8 colours, then they repeat).
- The phase lasts until the next `# ` or `## ` heading. `###` subheadings stay inside the phase.

## Steps: one card each

```markdown
| # | Feature | Effort | Due | Status |
| --- | --- | --- | --- | --- |
| 1 | **Sign in.** Email and password, a reset link. | M | 2026-10-23 | Done 2026-10-22 |
| 2 | **Profiles.** Name, photo and settings. | S | 2026-10-24 | In progress |
| 3 | **Search.** Find anything in under a second. | L | 2026-10-31 | Not started |
```

- A table inside a phase, with a header row. Columns are found **by their header names**, in any order:
  - `#`: the step's ID. Numbers (`1`, `12`) or a letter and a number (`F3`). IDs must be unique in the file.
  - `Feature` (or `Task`, `What`): `**Title.**` in bold first, then the description, which shows under "Details".
  - `Effort` (or `Size`): `S`, `M`, `L`, `XL`, a range like `S–M`, or days like `4d`. Optional.
  - `Due` (or `Target`, `Deadline`): `YYYY-MM-DD`. Optional; without it the card shows no date.
  - `Status`: decides the column (below). Required.
- Steps appear on the board in roadmap order.

## Status → column

| Status starts with or contains | Column |
| --- | --- |
| `On hold` (anywhere) | On hold |
| `Done` (at the start), best as `Done 2026-10-22` | Done (the card shows ✓ and the date) |
| `In progress`, `Being built`, `Built, waiting for …`, `Waiting for …` | In progress |
| `Next` (at the start) | Next |
| anything else (`Not started`, `Planned`) | To do |

Anything after those words shows on the card, for example "Built, waiting for a headset test". `**bold**` and
`` `code` `` work in all text.

## Parts: a checklist on the card

```markdown
Step 3 is built in three parts:

| Part | What | Due | Status |
| --- | --- | --- | --- |
| 3a | The index: every record searchable. | 2026-10-27 | Done 2026-10-27 |
| 3b | The search box and results page. | 2026-10-29 | In progress |
| 3c | Filters and sorting. | 2026-10-31 | Not started |
```

- A part's ID is its step's ID plus a letter (`3a`, `F3b`). It shows as a checklist on that step's card, with its own
  status dot and due date. The part's text up to the first full stop is shown.
- Parts tables can have an `Effort` column too. `roadmap.py schedule` then shares the step's days by those sizes.

## On hold notes

```markdown
Step 7 is **on hold**. Why it's on hold and what has to happen first, in one paragraph.
```

- A paragraph starting `Step <ID> is **on hold**` shows as "Why on hold" on that card. The step's status should say
  `On hold (…)` too.

## Dates on the board

- **Timeline (top):** start → end, today's marker, each phase's stretch of time (from the end of the phase before to
  its last due date), the work done against the time used, and "On track", "N overdue" or "Past the end date".
- **Cards:** "Due 24 Oct", "Due in 2 d" or "Due today" (amber), "Overdue · 3 d" (red, for unfinished steps that aren't
  on hold), and "✓ 22 Oct" once done.
- Dates are calendar dates in local time. A step is overdue from the day after its due date.
