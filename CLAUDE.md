# Project board (Claude Code plugin)

A Claude Code plugin, and its own marketplace: the agent plans a project in `ROADMAP.md` (phases, steps, parts, due
dates), shows it as a live kanban board, writes the project's `README.md` and `CLAUDE.md`, and keeps all three
current as work happens. Public repo: github.com/Chithamalai-Karthik/project-board.

## Read first

- **README.md** — what the plugin does, install, use, and **What's in here**: which file controls what. Start
  there instead of reading every file. Each script and page also opens with a comment saying what it does.
- **plugins/project-board/skills/plan/SKILL.md** — the instructions the agent follows in a user's project. This is
  the product: most features are a change here.
- **.../plan/FORMAT.md** — the roadmap format. It is the contract between the board page and `roadmap.py`.

## How it is built

- No build step and no packages. The board is one HTML page (`board/index.html`, plain JS) served by `serve.py`;
  `scripts/roadmap.py` (`init`, `check`, `schedule`) is Python 3.8+, standard library only. Keep it that way: the
  files are copied into every user's project and must run there as they are.
- `init` copies `board/`, `FORMAT.md` and `roadmap.py` into `<project>/board/`, and the templates into the project.
- `templates/` hold the starting `ROADMAP.md`, `README.md` and `CLAUDE.md`, with `{{…}}` for what the agent fills.
- `examples/demo/` is a sample project part way through; `presentation/` is the talk (slides, a scripted offline
  tour, a one-page handout).
- Match the surrounding writing: a header comment per file, short comments that say why, plain wording.

## Standing rules

- **Ask before pushing** to GitHub. The repo is public and installed copies update from it.
- **Edit this repo, never the installed copy** in `~/.claude/plugins/cache/` (it is replaced on update).
- **Bump `version`** in `plugins/project-board/.claude-plugin/plugin.json` for every change users should get;
  without a new version they don't get it.
- **A user's files are theirs:** `init` never overwrites an existing `ROADMAP.md`, `README.md` or `CLAUDE.md`, and
  the skill never rewrites the user's text (it offers to add missing sections). Only `board/` files are replaced.
- **Change the format in all its places together:** FORMAT.md, the parser in `board/index.html`, `roadmap.py`
  (`check` and `schedule`), the template, the demo, and the SKILL's "Format essentials".
- **The board stays local:** `serve.py` binds 127.0.0.1 only; no accounts, no cloud, no tracking.
- **Due dates come from `roadmap.py schedule`,** never worked out by hand (also for the presentation's tour).
- **Keep SKILL.md short and exact:** every session that uses the plugin loads it. Its `description` decides when
  the skill is picked, so keep the trigger words in it.
- **Keep the docs current as you work.** A file added, renamed or removed: README › What's in here. A feature,
  command or option changed: the README section that describes it (and the presentation, if it shows it).

## Testing

```bash
claude plugin validate .                                              # the manifest and the skill
python plugins/project-board/skills/plan/scripts/roadmap.py check examples/demo/ROADMAP.md
python plugins/project-board/skills/plan/scripts/roadmap.py init <empty temp folder>    # then run init again:
                                                                      # nothing may be overwritten
python plugins/project-board/skills/plan/board/serve.py --root examples/demo           # look at the board
```

Use a temp folder for `init` tests, never a real project. To try the skill end to end, install the plugin from this
folder (`/plugin marketplace add <this folder>`) in a throwaway project.
