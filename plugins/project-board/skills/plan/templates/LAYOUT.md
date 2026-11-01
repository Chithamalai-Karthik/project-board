# Project layout

Which file controls what, so the project can be understood without reading all of it. Each source file also starts
with a comment saying what it does. ROADMAP.md says what is built and what comes next.

{{One table per folder: | File | What it does |, one short line each. A new project starts with the folders it
will have and fills the table in as files are created.}}

| File | What it does |
| --- | --- |
| `README.md` | what the project is, and how to set it up, run and use it |
| `ROADMAP.md` | what is built, what comes next, and the decisions behind each step |
| `AGENTS.md` | for an AI agent working on the project: where to start reading, and the standing rules |
| `CLAUDE.md` | one line, `@AGENTS.md`: Claude Code loads AGENTS.md through it |
| `LAYOUT.md` | this file |
| `board/` | the project board (a kanban view of ROADMAP.md): `python board/serve.py` |
