---
name: plan
description: Plan a project as phases, steps and dated tasks in ROADMAP.md, shown as a live kanban board (board/index.html) with a schedule timeline, due dates and overdue flags, together with the project's documentation (README.md with a map of which file controls what, and CLAUDE.md for agents); then keep the roadmap and the docs up to date as work happens. Use when the user wants to plan, roadmap or schedule a project or new feature set, set up or open the project board, add or reschedule steps, mark progress on the roadmap, or set up or update the project's documentation.
---

# Project board: plan and keep a roadmap

A project's plan lives in one file, `ROADMAP.md`, in a fixed Markdown format. The board page
(`board/index.html`) shows it as a kanban board: five columns (To do, Next, In progress, Done, On hold), one card
per step, phase progress, a schedule timeline, due dates and overdue warnings. Cards fly to their new column when
a status changes. The roadmap is the only source: you edit it, the board follows.

The plan comes with the project's documentation, kept current the same way:

- `README.md`: what the project is, how to set it up, run and use it, and **Project layout**: one line per file
  saying what it controls. A new team member, or a new agent session, reads this map instead of the whole
  codebase, and opens only the files a task needs (far fewer tokens).
- `CLAUDE.md`: read by every Claude Code session in the project: where to start reading, how it's built, the
  standing rules (what not to touch, what to ask first) and how to keep the roadmap and the docs current.

Files beside this SKILL.md (in Claude Code: `${CLAUDE_SKILL_DIR}`):

- `board/index.html`, `board/serve.py`: the board, and a tiny local server to open it
- `FORMAT.md`: the exact format the board reads. **Read it before writing or editing a roadmap.**
- `templates/ROADMAP.md`, `templates/README.md`, `templates/CLAUDE.md`: the starting roadmap and docs
- `scripts/roadmap.py`: `init` (sets it all up), `check` (format and dates) and `schedule` (works out every due
  date). Python 3.8+, no packages.

## Which job

- **No `ROADMAP.md` yet, or "plan this project":** set up (1), interview (2), plan (3), schedule (4), write the
  docs (5), hand over (6).
- **A `ROADMAP.md` already exists** (planned before, or another format): set up (1) only, then run `check`. If it
  isn't in this format, offer to convert it, keeping its content and decisions. Then the docs (5).
- **"Open the board":** `python board/serve.py` in the project folder (it opens the browser).
- **"Document this project" / the docs are missing or stale:** write the docs (5).
- **During work:** keep the roadmap and the docs live (7).
- **"We're behind" or a step slipped:** reschedule (8).

## 1. Set up the board in the project

```
python "${CLAUDE_SKILL_DIR}/scripts/roadmap.py" init <project folder>
```

This copies the board page, its server, `FORMAT.md` and the script into `<project>/board/`, and the templates to
`ROADMAP.md`, `README.md` and `CLAUDE.md` for each one the project doesn't have yet (it never overwrites any of
them: an existing README or CLAUDE.md is the user's, see 5). The project then works for anyone, with or without
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
- Rules for later sessions, if the code doesn't show them: anything that must never be touched (a running server, a
  port, live data), and what to always ask before doing. These go in CLAUDE.md.

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

## 5. Write the docs: README.md and CLAUDE.md

Write only what you have checked in the code or heard from the user; leave a `{{…}}` the user must fill rather than
guess (a key's location, a deployment step).

- **README.md** from `templates/README.md`: the one-line description (the same as the roadmap's), setup, running,
  using, and **Project layout**. In the layout, one table per folder with one short line per file on what it
  controls (read each file's opening comment or skim it; don't guess from the name). Include the roadmap, the
  CLAUDE.md and `board/`. A new project with no code yet gets the folders it will have, filled in as files appear.
- **CLAUDE.md** from `templates/CLAUDE.md`: keep it short, since every session loads it. "Read first" points to the
  README's layout and the roadmap; "How it is built" names the stack and conventions; "Standing rules" holds the
  interview's rules, one bullet each with the reason, plus the "keep the docs current" bullet; keep the "Roadmap and
  board" section as it is.
- **The project already has them:** never rewrite the user's text. Read them, then offer to add only what's
  missing (usually Project layout in the README, and the Read first, Standing rules, keep-the-docs-current and
  Roadmap and board sections in CLAUDE.md), and add them once the user agrees.
- **Other agents:** if the project uses `AGENTS.md` (or the user works with other agents), offer the same content
  there.
- Remove every `{{…}}` you could fill. List the ones left for the user at hand-over.

## 6. Hand over

Tell the user, briefly:

- the phases with their date ranges, the end date, and the total working days;
- how to open the board: `python board/serve.py` (from the project folder; it serves on this computer only);
- the docs: what README.md and CLAUDE.md now cover, and any `{{…}}` left for them;
- anything assumed that they should confirm.

Ask them to approve the plan (or change it) before starting work.

## 7. Keep the roadmap and the docs live while working

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
  size. Then reschedule (8), or give it a Due date if the user wants to keep the others fixed.
- **Every edit:** update "Last updated <date>." and run `python board/roadmap.py check ROADMAP.md`.
- Don't rewrite history: done steps, their dates and recorded decisions stay as they were.

And the docs, in the same turn as the code change:

- **A file added, renamed or removed:** its line in README › Project layout (a new file also opens with a comment
  saying what it does).
- **A feature, command, control or option changed:** the README section that describes it.
- **A new standing rule** from the user ("never…", "always ask before…"): a bullet in CLAUDE.md › Standing rules.
- Nothing stale: when a heading or line no longer matches what was built, fix it.

## 8. Reschedule when things slip

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
