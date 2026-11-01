# What each version needs from a project

The session-start hook shows a project the sections newer than its `board/VERSION`, and the agent offers to apply them.
Add a section only when a release changes something a project should pick up. Newest first. Each line says what to do,
and is skipped if the project already has it.

## 1.5.0

- `init` replaces `board/roadmap.py`, so `check` also warns about stale docs: unfilled `{{...}}`, and files the layout
  lists that are gone or doesn't list. Run `check` afterwards, and fix what it reports or tell the user.

## 1.4.0

- `init` adds `board/VERSION`, so later updates are offered by themselves.

## 1.3.0

- Move the Project layout section from README.md to a new LAYOUT.md, keeping its text. Point AGENTS.md at LAYOUT.md in
  "Read first" and in the keep-the-docs-current rule. Add LAYOUT.md to its own file list.
