---
name: plan
description: Plan a project as phases, steps and dated tasks in ROADMAP.md, shown as a live kanban board (board/index.html) with a schedule timeline, due dates and overdue flags; then keep it up to date as work happens. Use when the user wants to plan, roadmap or schedule a project or new feature set, set up or open the project board, add or reschedule steps, or mark progress on the roadmap.
---

# Project board: plan and keep a roadmap

A project's plan lives in one file, `ROADMAP.md`, in a fixed Markdown format. The board page
(`board/index.html`) shows it as a kanban board: five columns (To do, Next, In progress, Done, On hold), one card
per step, phase progress, a schedule timeline, due dates and overdue warnings. Cards fly to their new column when
a status changes. The roadmap is the only source: you edit it, the board follows.

Files beside this SKILL.md (in Claude Code: `${CLAUDE_SKILL_DIR}`):

- `board/index.html`, `board/serve.py`: the board, and a tiny local server to open it
- `FORMAT.md`: the exact format the board reads. **Read it before writing or editing a roadmap.**
- `templates/ROADMAP.md`: the starting roadmap
- `scripts/roadmap.py`: `check` (format and dates) and `schedule` (works out every due date). Python 3.8+, no packages.

## Which job

- **No `ROADMAP.md` yet, or "plan this project":** set up (1), interview (2), plan (3), schedule (4), hand over (5).
- **A `ROADMAP.md` already exists** (planned before, or another format): set up (1) only, then run `check`. If it
  isn't in this format, offer to convert it, keeping its content and decisions.
- **"Open the board":** `python board/serve.py` in the project folder (it opens the browser).
- **During work:** keep the roadmap live (6).
- **"We're behind" or a step slipped:** reschedule (7).

## 1. Set up the board in the project

```
python "${CLAUDE_SKILL_DIR}/scripts/roadmap.py" init <project folder>
```

This copies the board page, its server, `FORMAT.md` and the script into `<project>/board/`, and the template to
`ROADMAP.md` if there isn't one (it never overwrites a roadmap). The project then works for anyone, with or without
this plugin. If `board/` already holds other files of the project's own, ask before running it. Older copies of
these four files are simply replaced (they hold no project data). Outside Claude Code, use the path of the folder
holding this SKILL.md instead of `${CLAUDE_SKILL_DIR}`.

## 2. Interview: ask only what you can't infer

Read what's there first: README, code, existing notes. Then ask the user, in one round (at most four questions, each
with a recommended option), only what's missing:

- What the project is, for whom, and what "done" looks like (the one-line description comes from this).
- **Start date, deadline (if any) and days a week** worked on it (5 by default; 6 or 7 for weekends, fewer part time).
- The must-haves versus nice-to-haves, and anything already built.
- Constraints: platforms, tools, budget, people.

## 3. Plan: phases, steps, parts

- **Phases:** 2–6, each delivering something usable or testable on its own, in the order it can be built. IDs `A`,
  `B`, `C`… (or `0` for groundwork). One sentence each on what it delivers.
- **Steps:** one card each, a result someone can check ("Sign in works with email and password"), not an activity
  ("Work on auth"). Number them **1, 2, 3… across the whole roadmap** in build order. Give each an effort size:
  S = 1 day, M = 3, L = 5, XL = 10 working days. Split anything bigger than XL into steps.
- **Parts:** for L and XL steps, 2–5 parts (`7a`, `7b`…) when that helps track progress. Parts can have their own
  effort sizes.
- Write `ROADMAP.md` from `templates/ROADMAP.md`. Fill every `{{…}}`, leave Due cells empty, and set all statuses to
  `Not started` (the first step `Next`). Add "Decisions for Phase X" bullets for what the interview settled, with the
  date. Put ideas that didn't make the cut under `## Later` (not a phase, so they stay off the board).
- Keep the user's own words where they gave them (for example their description of the project).

## 4. Schedule: let the script work out the dates

Never work out due dates by hand: the script counts working days, days off and effort sizes exactly.

```
python board/roadmap.py schedule ROADMAP.md --start 2026-10-20 --days-per-week 5 [--off 2026-12-25,2026-12-26] --write
python board/roadmap.py check ROADMAP.md
```

- Steps are scheduled one after another in roadmap order, and parts share their step's days.
- The `**Schedule:**` line (start, end, days) is written for you.
- If the end date is past the user's deadline, don't hide it. Show the gap and offer choices: move steps to Later,
  shrink sizes the user agrees are too big, or add days a week. Then reschedule.
- `--effort S=1,M=2,L=4,XL=8` changes the sizes if the user's pace differs (it's kept in the Schedule line).
- Fix every `ERROR` from `check`. Warnings are for judgement.

## 5. Hand over

Tell the user, briefly:

- the phases with their date ranges, the end date, and the total working days;
- how to open the board: `python board/serve.py` (from the project folder; it serves on this computer only);
- anything assumed that they should confirm.

Ask them to approve the plan (or change it) before starting work. Then offer to add the "keep the board live" note
below to the project's `CLAUDE.md` (and `AGENTS.md`, for other agents), so every later session follows it:

```markdown
## Roadmap and board
The plan is in ROADMAP.md (format: board/FORMAT.md); the board is board/index.html (`python board/serve.py`).
Keep it live: set a step In progress when you start it and `Done YYYY-MM-DD` when it's finished, update parts the
same way, add decisions with their date, and update "Last updated". Check after each edit:
`python board/roadmap.py check ROADMAP.md`. Never renumber steps; new steps take the next free number.
```

## 6. Keep the roadmap live while working

Update the roadmap as part of the work, in the same turn as the change, without being asked:

- **Starting a step:** `In progress` (and its first part). Only the steps really being worked on.
- **Finished:** `Done YYYY-MM-DD` with today's date (the board shows ✓ and the date). A step is done when all its
  parts are.
- **Built, but waiting** for something outside the code (a test on a device, a review, a release):
  `Built, waiting for <what>`.
- **Paused or blocked:** `On hold (<date>: <short reason>)` plus a `Step N is **on hold**. …` paragraph with why
  and what has to happen first.
- **Decisions** the user makes: add a bullet under that phase with the date and the reason.
- **New work:** a new step takes the next free number (never renumber) and goes in the right phase, with an effort
  size. Then reschedule (7), or give it a Due date if the user wants to keep the others fixed.
- **Every edit:** update "Last updated <date>." and run `python board/roadmap.py check ROADMAP.md`.
- Don't rewrite history: done steps, their dates and recorded decisions stay as they were.

## 7. Reschedule when things slip

When `check` reports overdue steps or the user says the plan has changed:

1. Preview: `python board/roadmap.py schedule ROADMAP.md --from-today`. This plans what's left from today and keeps
   done and on-hold steps.
2. Show the user the new end date and what moved. Changing dates is a plan change, so confirm before writing.
3. `... --from-today --write`, then add a decision bullet: "Rescheduled (date): <why>, end moved from X to Y".

## Format essentials (full rules: FORMAT.md)

- `# <Name> roadmap` first. The board is called "<Name> board".
- `## About the project`: the first paragraph is the one-line description.
- `**Schedule:** start YYYY-MM-DD · end YYYY-MM-DD · …`
- `## Phase A: title`, each with a table `| # | Feature | Effort | Due | Status |`. The Feature cell starts with
  `**Title.**`.
- Parts: `| Part | What | Effort | Due | Status |` with IDs like `7a`.
- Statuses: `Not started`, `Next`, `In progress`, `Built, waiting for …`, `Done YYYY-MM-DD`, `On hold (…)`.
