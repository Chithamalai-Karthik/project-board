"""Checks a project's ROADMAP.md against the board's format, and plans its dates.

    python roadmap.py init <project folder>
    python roadmap.py check ROADMAP.md
    python roadmap.py schedule ROADMAP.md --start 2026-10-20 [--days-per-week 5] [--off 2026-12-25,2026-12-26]
                                          [--effort S=1,M=3,L=5,XL=10] [--from-today] [--write]

init      sets the board up in a project: copies the board page, its server, FORMAT.md and this script into
          <project>/board/ (replacing older copies), and the starting ROADMAP.md, README.md, AGENTS.md and CLAUDE.md
          (one line, @AGENTS.md) into <project>/ for each one that isn't there yet (existing files are never touched).
          A project with its own CLAUDE.md and no AGENTS.md gets no AGENTS.md: its CLAUDE.md stays its agent file.
check     reports format errors (exit code 1) and warnings: missing due dates, dates out of order or outside the
          schedule, overdue steps, parts without their step.
schedule  works out every unfinished step's due date in roadmap order, one after another, from its effort size
          (working days: S=1, M=3, L=5, XL=10 by default; "S-M" is the average; "4d" is 4 days) on working days
          only (Monday to Friday for 5 days a week, plus Saturday for 6, every day for 7; minus the days off).
          A step's parts share its days (by their own effort sizes when they have them). Done steps keep their
          dates. --from-today plans what's left from today (to reschedule after a slip). Without --write it only
          prints the plan; with it, it writes the Due column (adding it to tables that lack it) and the
          "**Schedule:**" line. Settings already in the Schedule line are used unless given again.

Python 3.8+, standard library only. The format: FORMAT.md beside this skill (and board/FORMAT.md in a project).
"""
import argparse
import math
import os
import re
import shutil
import sys
from datetime import date, timedelta

HEAD = {
    "id": re.compile(r"^(#|id|step|part|no\.?)$"),
    "text": re.compile(r"^(feature|task|what|step name|title|description)$"),
    "effort": re.compile(r"^(effort|size|estimate)$"),
    "due": re.compile(r"^(due|target|deadline|date|due date)$"),
    "status": re.compile(r"^(status|state)$"),
}
STEP_ID = re.compile(r"^[A-Z]?\d+$")
PART_ID = re.compile(r"^[A-Z]?\d+[a-z]$")
ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
SEPARATOR = re.compile(r"^\|\s*:?-{2,}")
DEFAULT_EFFORT = {"XS": 0.5, "S": 1, "M": 3, "L": 5, "XL": 10, "XXL": 20}


def column_of(status):
    s = status.replace("*", "").lower().strip()
    if "on hold" in s:
        return "hold"
    if re.match(r"^done\b", s):
        return "done"
    if re.search(r"in progress|being built|built, waiting|waiting for", s):
        return "doing"
    if re.match(r"^next\b", s):
        return "next"
    return "todo"


def iso(text):
    m = ISO.search(text or "")
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def cells_of(line):
    return [c.strip() for c in line.strip().split("|")[1:-1]]


class Roadmap:
    def __init__(self, text):
        self.lines = text.split("\n")
        self.crlf = text.count("\r\n") > text.count("\n") / 2
        self.lines = [l.rstrip("\r") for l in self.lines]
        self.title = ""
        self.phases = []      # {id, title, line}
        self.tables = []      # {phase, header, sep, rows, cols}
        self.steps = []       # {id, phase, line, table, title, effort, status, due, col, parts}
        self.parts = []
        self.schedule_line = None
        self.schedule = {}
        self.errors = []
        self.parse()

    def parse(self):
        phase = None
        table = None
        steps_by_id = {}
        for i, line in enumerate(self.lines):
            if not self.title:
                m = re.match(r"^#\s+(.+?)\s*$", line)
                if m:
                    self.title = m.group(1)
            if re.match(r"^\**Schedule:?\**:?\s", line, re.I):
                self.schedule_line = i
                self.schedule = parse_schedule(line)
                continue
            h = re.match(r"^## Phase ([0-9A-Z]+):\s*(.+)$", line)
            if h:
                phase = {"id": h.group(1), "title": h.group(2), "line": i}
                self.phases.append(phase)
                table = None
                continue
            if re.match(r"^#{1,2} ", line):
                phase = None
                table = None
            if not line.strip().startswith("|"):
                if line.strip():
                    table = None
                continue
            cells = cells_of(line)
            if all(re.match(r"^:?-{2,}:?$", c) for c in cells):
                continue
            nxt = self.lines[i + 1].strip() if i + 1 < len(self.lines) else ""
            if SEPARATOR.match(nxt):
                cols = {}
                for k, c in enumerate(cells):
                    name = c.replace("*", "").lower().strip()
                    for key, rx in HEAD.items():
                        if rx.match(name) and key not in cols:
                            cols[key] = k
                table = {"phase": phase, "header": i, "sep": i + 1, "rows": [], "cols": cols}
                if phase:
                    self.tables.append(table)
                continue
            if not phase or not table or "id" not in table["cols"]:
                continue
            table["rows"].append(i)
            cols = table["cols"]
            get = lambda key: cells[cols[key]] if key in cols and cols[key] < len(cells) else ""
            rid = get("id")
            if "status" not in cols:
                if STEP_ID.match(rid) or PART_ID.match(rid):
                    self.errors.append(f"line {i + 1}: the table has no Status column")
                continue
            if STEP_ID.match(rid) and "text" in cols:
                m = re.match(r"^\*\*(.+?)\*\*", get("text"))
                step = {"id": rid, "phase": phase["id"], "line": i, "table": table, "title": (m.group(1) if m else get("text")).rstrip("."),
                        "effort": get("effort"), "status": get("status"), "due_text": get("due"), "due": iso(get("due")),
                        "col": column_of(get("status")), "parts": []}
                if rid in steps_by_id:
                    self.errors.append(f"line {i + 1}: step {rid} appears twice (also line {steps_by_id[rid]['line'] + 1})")
                steps_by_id[rid] = step
                self.steps.append(step)
            elif PART_ID.match(rid):
                self.parts.append({"id": rid, "parent": rid[:-1], "line": i, "table": table, "effort": get("effort"),
                                   "status": get("status"), "due_text": get("due"), "due": iso(get("due")), "col": column_of(get("status"))})
        for p in self.parts:
            if p["parent"] in steps_by_id:
                steps_by_id[p["parent"]]["parts"].append(p)
            else:
                self.errors.append(f"line {p['line'] + 1}: part {p['id']} has no step {p['parent']}")
        if not self.title:
            self.errors.append("no title: the first line should be '# <Project name> roadmap'")
        if not self.phases:
            self.errors.append("no phases: phases are '## Phase <ID>: <title>' headings")
        for ph in self.phases:
            if not any(s["phase"] == ph["id"] for s in self.steps):
                self.errors.append(f"line {ph['line'] + 1}: Phase {ph['id']} has no steps (a table with #, Feature, Effort, Due, Status)")

    def text(self):
        return ("\r\n" if self.crlf else "\n").join(self.lines)


def parse_schedule(line):
    out = {}
    m = re.search(r"start\D*(\d{4}-\d{2}-\d{2})", line, re.I)
    if m:
        out["start"] = iso(m.group(1))
    m = re.search(r"end\D*(\d{4}-\d{2}-\d{2})", line, re.I)
    if m:
        out["end"] = iso(m.group(1))
    m = re.search(r"\((\d) (?:days )?a week\)", line) or re.search(r"(\d) days a week", line)
    if m:
        out["per_week"] = int(m.group(1))
    m = re.search(r"effort ([A-Z]+=[\d.]+(?:[ ,]+[A-Z]+=[\d.]+)*)", line)
    if m:
        out["effort"] = {k: float(v) for k, v in re.findall(r"([A-Z]+)=([\d.]+)", m.group(1))}
    m = re.search(r"\boff ((?:\d{4}-\d{2}-\d{2}(?:,\s*)?)+)", line)
    if m:
        out["off"] = [iso(d) for d in re.findall(r"\d{4}-\d{2}-\d{2}", m.group(1))]
    return out


def effort_days(effort, table):
    """'M' -> 3, 'S-M' / 'S–M' -> the average, '4d' / '4 days' / '4' -> 4; None when unknown."""
    e = (effort or "").replace("*", "").strip()
    if not e:
        return None
    m = re.match(r"^([\d.]+)\s*(d|day|days)?$", e, re.I)
    if m:
        return float(m.group(1))
    sizes = [x.strip().upper() for x in re.split(r"\s*[-–—/]\s*", e) if x.strip()]
    vals = [table.get(x) for x in sizes]
    if sizes and all(v is not None for v in vals):
        return sum(vals) / len(vals)
    return None


class Calendar:
    def __init__(self, per_week, off):
        self.per_week = max(1, min(7, per_week))
        self.off = set(off or [])

    def working(self, d):
        return d.weekday() < self.per_week and d not in self.off

    def first_on_or_after(self, d):
        while not self.working(d):
            d += timedelta(days=1)
        return d

    def nth(self, start, n):
        """The n-th working day counting `start` (already a working day) as the first."""
        d = start
        k = 1
        while k < n:
            d += timedelta(days=1)
            if self.working(d):
                k += 1
        return d

    def count(self, a, b):
        n, d = 0, a
        while d <= b:
            n += self.working(d)
            d += timedelta(days=1)
        return n


def set_cell(line, index, value):
    raw = line.split("|")
    # raw[0] is before the first pipe; cell k is raw[k + 1]
    raw[index + 1] = f" {value} "
    return "|".join(raw)


def insert_column(rm, table, before, header, sep_cell="---"):
    """Adds a column to a table at position `before` (header, separator and every row)."""
    for i in [table["header"], table["sep"], *table["rows"]]:
        raw = rm.lines[i].split("|")
        value = header if i == table["header"] else sep_cell if i == table["sep"] else ""
        raw.insert(before + 1, f" {value} ")
        rm.lines[i] = "|".join(raw)
    cols = table["cols"]
    for k in list(cols):
        if cols[k] >= before:
            cols[k] += 1
    cols["due"] = before


def schedule(rm, args):
    sch = dict(rm.schedule)
    start = iso(args.start) if args.start else sch.get("start")
    if not start:
        sys.exit("No start date: give --start YYYY-MM-DD (or put 'start YYYY-MM-DD' in the Schedule line).")
    per_week = args.days_per_week or sch.get("per_week") or 5
    effort_map = dict(DEFAULT_EFFORT)
    effort_map.update(sch.get("effort") or {})
    if args.effort:
        effort_map.update({k.strip().upper(): float(v) for k, v in (x.split("=") for x in args.effort.split(","))})
    off = [iso(d) for d in args.off.split(",")] if args.off else sch.get("off") or []
    cal = Calendar(per_week, off)
    start = cal.first_on_or_after(start)

    cursor = start
    if args.from_today:
        cursor = cal.first_on_or_after(max(start, date.today()))
    used = 0.0          # working days used since `cursor`
    plan = []           # (step or part, new due)
    unknown = []
    for s in rm.steps:
        if s["col"] in ("done", "hold"):
            continue
        days = effort_days(s["effort"], effort_map)
        if days is None:
            unknown.append(s["id"])
            days = effort_map["M"]
        first = used
        used += days
        plan.append((s, cal.nth(cursor, max(1, math.ceil(used - 1e-9)))))
        # Parts share the step's days, by their own effort sizes when they have them
        todo = [p for p in s["parts"] if p["col"] not in ("done", "hold")]
        if todo:
            weights = [effort_days(p["effort"], effort_map) or 1 for p in todo]
            total = sum(weights)
            at = first
            for p, w in zip(todo, weights):
                at += days * w / total
                plan.append((p, cal.nth(cursor, max(1, math.ceil(at - 1e-9)))))

    end = max([d for _, d in plan] + [s["due"] for s in rm.steps if s["due"] and s["col"] == "done"] + [start])
    calendar_days = (end - start).days + 1
    working = cal.count(start, end)
    effort_text = " ".join(f"{k}={v:g}" for k, v in effort_map.items() if k in ("S", "M", "L", "XL"))
    line = (f"**Schedule:** start {start.isoformat()} · end {end.isoformat()} · {calendar_days} days, {working} working days "
            f"({per_week} days a week) · effort {effort_text} working days")
    if off:
        line += " · off " + ", ".join(d.isoformat() for d in off if d)

    # Report
    print(line.replace("**", ""))
    for ph in rm.phases:
        mine = [(x, d) for x, d in plan if x.get("phase") == ph["id"]]
        kept = [s for s in rm.steps if s["phase"] == ph["id"] and s["col"] in ("done", "hold")]
        if mine:
            print(f"  Phase {ph['id']}: due {min(d for _, d in mine).isoformat()} -> {max(d for _, d in mine).isoformat()}"
                  + (f" ({len(kept)} done or on hold kept)" if kept else ""))
    for x, d in plan:
        kind = "part" if "parent" in x else "step"
        print(f"    {kind} {x['id']:>4}  {d.isoformat()}  {d.strftime('%a')}  (was {x['due_text'] or '-'})")
    if unknown:
        print(f"Unknown effort for steps {', '.join(unknown)}: counted as M ({effort_map['M']:g} days).")
    if not args.write:
        print("\n(Only a preview: add --write to write the dates and the Schedule line.)")
        return

    # Write: the Due column (added where missing, before Status), then each date, then the Schedule line
    for t in rm.tables:
        if "due" not in t["cols"] and "status" in t["cols"] and any(
                (x["table"] is t) for x, _ in plan):
            insert_column(rm, t, t["cols"]["status"], "Due")
    for x, d in plan:
        rm.lines[x["line"]] = set_cell(rm.lines[x["line"]], x["table"]["cols"]["due"], d.isoformat())
    if rm.schedule_line is not None:
        rm.lines[rm.schedule_line] = line
    else:
        at = rm.phases[0]["line"] if rm.phases else len(rm.lines)
        rm.lines[at:at] = ["## Schedule", "", line, ""]
    print("\nWritten.")


def check(rm):
    warnings = []
    sch = rm.schedule
    today = date.today()
    if rm.schedule_line is not None and not (sch.get("start") and sch.get("end")):
        rm.errors.append(f"line {rm.schedule_line + 1}: the Schedule line needs 'start YYYY-MM-DD' and 'end YYYY-MM-DD'")
    if sch.get("start") and sch.get("end") and sch["start"] > sch["end"]:
        rm.errors.append("the Schedule's start is after its end")
    for x in rm.steps + rm.parts:
        if x["due_text"] and x["due_text"] not in ("-", "–") and not x["due"]:
            rm.errors.append(f"line {x['line'] + 1}: {x['id']}: due date '{x['due_text']}' is not YYYY-MM-DD")
    dated = any(s["due"] for s in rm.steps) or sch
    prev = None
    for s in rm.steps:
        if dated and not s["due"] and s["col"] != "hold":
            warnings.append(f"step {s['id']} has no due date")
        if s["due"] and sch.get("start") and s["due"] < sch["start"]:
            warnings.append(f"step {s['id']} is due {s['due']}, before the start ({sch['start']})")
        if s["due"] and sch.get("end") and s["due"] > sch["end"]:
            warnings.append(f"step {s['id']} is due {s['due']}, after the end ({sch['end']}): update the Schedule line")
        if s["due"] and prev and s["due"] < prev["due"] and s["col"] != "done":
            warnings.append(f"step {s['id']} (due {s['due']}) comes before step {prev['id']} (due {prev['due']}) in time but after it in the roadmap")
        if s["due"]:
            prev = s
        for p in s["parts"]:
            if p["due"] and s["due"] and p["due"] > s["due"]:
                warnings.append(f"part {p['id']} is due {p['due']}, after its step ({s['due']})")
        if s["col"] == "done" and dated and not iso(s["status"]):
            warnings.append(f"step {s['id']} is Done without a date: write 'Done {today.isoformat()}' (the board shows it)")
        if s["due"] and s["col"] not in ("done", "hold") and s["due"] < today:
            warnings.append(f"step {s['id']} is overdue (due {s['due']}): finish it, or reschedule (schedule --from-today --write)")
        if effort_days(s["effort"], {**DEFAULT_EFFORT, **(sch.get("effort") or {})}) is None and s["effort"]:
            warnings.append(f"step {s['id']}: effort '{s['effort']}' is not a size (S, M, L, XL) or a number of days")
    cols = {}
    for s in rm.steps:
        cols[s["col"]] = cols.get(s["col"], 0) + 1
    print(f"{rm.title or '(no title)'}: {len(rm.phases)} phases, {len(rm.steps)} steps, {len(rm.parts)} parts · "
          + ", ".join(f"{k} {v}" for k, v in sorted(cols.items())))
    for e in rm.errors:
        print("ERROR  " + e)
    for w in warnings:
        print("warn   " + w)
    if not rm.errors and not warnings:
        print("OK")
    return 1 if rm.errors else 0


def init(project):
    """Copies the board into <project>/board/, and the template roadmap and docs the project doesn't have yet."""
    skill = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    board = os.path.join(project, "board")
    os.makedirs(board, exist_ok=True)
    copies = [
        (os.path.join(skill, "board", "index.html"), os.path.join(board, "index.html")),
        (os.path.join(skill, "board", "serve.py"), os.path.join(board, "serve.py")),
        (os.path.join(skill, "FORMAT.md"), os.path.join(board, "FORMAT.md")),
        (os.path.abspath(__file__), os.path.join(board, "roadmap.py")),
    ]
    for src, dst in copies:
        # (run from a project's own board/roadmap.py, the sources are the board's files themselves, or not there)
        if os.path.exists(src) and os.path.abspath(src) != os.path.abspath(dst):
            shutil.copyfile(src, dst)
        print("board:  ", os.path.relpath(dst, project))
    # The roadmap and the project's documentation: started from the templates, never overwritten
    # (a project's own board/roadmap.py has no templates beside it, so it only reports what's missing)
    for name in ("ROADMAP.md", "README.md", "AGENTS.md", "CLAUDE.md"):
        path = os.path.join(project, name)
        template = os.path.join(skill, "templates", name)
        if os.path.exists(path):
            print(f"kept:    {name} (already there)")
        elif name == "AGENTS.md" and os.path.exists(os.path.join(project, "CLAUDE.md")):
            # Nothing would load a template AGENTS.md beside the project's own CLAUDE.md
            print("skipped: AGENTS.md (the project's CLAUDE.md is its agent file)")
        elif os.path.exists(template):
            shutil.copyfile(template, path)
            if name == "CLAUDE.md":
                print("new:     CLAUDE.md (one line, @AGENTS.md: Claude Code loads AGENTS.md through it)")
            else:
                print(f"new:     {name} (the template: fill in every {{{{...}}}})")
        else:
            print(f"missing: {name} (run init from the plugin to start it from the template)")
    print("Open the board: python board/serve.py")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")   # Windows consoles default to an older code page
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init")
    i.add_argument("project", nargs="?", default=".")
    c = sub.add_parser("check")
    c.add_argument("roadmap")
    s = sub.add_parser("schedule")
    s.add_argument("roadmap")
    s.add_argument("--start")
    s.add_argument("--days-per-week", type=int)
    s.add_argument("--off", help="days off, comma-separated YYYY-MM-DD")
    s.add_argument("--effort", help="working days per size, e.g. S=1,M=2,L=4,XL=8")
    s.add_argument("--from-today", action="store_true", help="plan what's left from today")
    s.add_argument("--write", action="store_true")
    args = ap.parse_args()
    if args.cmd == "init":
        init(os.path.abspath(args.project))
        return
    with open(args.roadmap, encoding="utf-8", newline="") as f:
        rm = Roadmap(f.read())
    if args.cmd == "check":
        sys.exit(check(rm))
    if rm.errors:
        for e in rm.errors:
            print("ERROR  " + e)
        sys.exit("Fix the format errors first (roadmap.py check).")
    schedule(rm, args)
    if args.write:
        with open(args.roadmap, "w", encoding="utf-8", newline="") as f:
            f.write(rm.text())


if __name__ == "__main__":
    main()
