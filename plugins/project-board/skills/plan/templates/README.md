# {{Project name}}

{{The one-line description of the project (the same as in ROADMAP.md).}}

{{A paragraph on what it does and for whom.}}

## Setup

{{What to install and configure once: tools and versions, keys, certificates, anything outside the code.}}

## Running it

{{The commands to start it each time, and the address or entry point to open.}}

## Using it

{{What a user does with it: the main screens, commands or controls, and the options for testing.}}

## Project layout

Which file controls what, so the project can be understood without reading all of it. Each source file also starts
with a comment saying what it does. ROADMAP.md says what is built and what comes next.

{{One table per folder: | File | What it does |, one short line each. A new project starts with the folders it
will have and fills the table in as files are created.}}

| File | What it does |
| --- | --- |
| `ROADMAP.md` | what is built, what comes next, and the decisions behind each step |
| `AGENTS.md` | for an AI agent working on the project: where to start reading, and the standing rules |
| `CLAUDE.md` | one line, `@AGENTS.md`: Claude Code loads AGENTS.md through it |
| `board/` | the project board (a kanban view of ROADMAP.md): `python board/serve.py` |

## Project board

`python board/serve.py` opens ROADMAP.md as a kanban board (To do, Next, In progress, Done, On hold) with due dates
and a schedule timeline. It reads the roadmap each time it opens, so the roadmap is the one place to edit.
