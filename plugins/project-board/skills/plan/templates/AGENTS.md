# {{Project name}}

{{The one-line description of the project.}}

## Read first

- **README.md**: how to set it up, run and use it, and **Project layout**: which file controls what. Start there
  instead of reading the whole codebase, then open only the files the task needs.
- **ROADMAP.md**: what is built, what comes next and the decisions behind each step.

## How it is built

{{Languages, frameworks, build or no build, how the parts talk to each other; the conventions to follow.}}

## Standing rules

{{What must not be touched or broken (ports, servers, data, files), what to ask before doing, the user's settled
preferences. One bullet each, with the reason when it isn't obvious.}}

- **Keep the docs current as you work.** When you add, rename or remove a file, update README › Project layout;
  when a feature, command, control or option changes, update the README section that describes it.

## Roadmap and board

The plan is in ROADMAP.md (format: board/FORMAT.md); the board is board/index.html (`python board/serve.py`).
Keep it live: set a step In progress when you start it and `Done YYYY-MM-DD` when it's finished, update parts the
same way, add decisions with their date, and update "Last updated". Check after each edit:
`python board/roadmap.py check ROADMAP.md`. Never renumber steps; new steps take the next free number.

## Testing

{{How to test a change: commands, test data, what only a person can check (a device, a look and feel).}}
