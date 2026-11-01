"""Runs when a session starts: tells the agent if this project's board is behind the installed plugin.

Compares board/VERSION in the current folder with the plugin's version, and prints the sections of CHANGES.md the
project hasn't had, for the agent to offer to the user. Prints nothing in a folder without a board, when the project
is up to date, or when the user said "not now" to this version (a "skip <version>" line in board/VERSION).
Local only: it reads files and never goes online. Any failure stays silent, so a session always starts.

Python 3.8+, standard library only.
"""
import json
import os
import re
import sys


def parts(version):
    """"1.3.0" as (1, 3, 0), so versions compare as numbers. Unreadable: None."""
    return tuple(int(n) for n in version.split(".")) if re.fullmatch(r"\d+(\.\d+)*", version or "") else None


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def main():
    project = os.getcwd()
    if not (os.path.exists(os.path.join(project, "board", "index.html"))
            and os.path.exists(os.path.join(project, "board", "roadmap.py"))):
        return
    plugin = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    installed = json.loads(read(os.path.join(plugin, ".claude-plugin", "plugin.json")))["version"]
    skill = os.path.join(plugin, "skills", "plan")

    # A project set up before 1.4.0 has no VERSION file: it counts as older than every section
    stamp_path = os.path.join(project, "board", "VERSION")
    stamp_text = read(stamp_path) if os.path.exists(stamp_path) else ""
    stamp_line = re.search(r"^\d[\d.]*\s*$", stamp_text, re.M)
    stamp_name = stamp_line.group(0).strip() if stamp_line else ""
    stamp = parts(stamp_name) or ()
    skipped = re.search(r"^skip (\S+)", stamp_text, re.M)
    skipped = parts(skipped.group(1)) if skipped else None

    sections = re.findall(r"^## (\S+)\n(.*?)(?=^## |\Z)", read(os.path.join(skill, "CHANGES.md")), re.M | re.S)
    behind = [(v, text.strip()) for v, text in sections if parts(v) and parts(v) > stamp]
    if not behind or (skipped and all(parts(v) <= skipped for v, _ in behind)):
        return

    script = os.path.join(skill, "scripts", "roadmap.py")
    notes = "\n\n".join(f"{v}:\n{text}" for v, text in behind)
    print(f"""The project board plugin {installed} is installed, and this project was set up with \
{stamp_name or "an older version"}. In your first reply, tell the user in one or two sentences what is new, and \
ask whether to update this project.

What is new:

{notes}

If they agree: run python "{script}" init . (it replaces only the board files and writes board/VERSION), then make the \
changes above that this project doesn't have yet, leaving out any it already has. The user's own files change only as \
those notes say.
If they say not now: add the line "skip {behind[0][0]}" to board/VERSION, and change nothing else.""")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")   # Windows consoles default to an older code page
        main()
    except Exception:
        pass
