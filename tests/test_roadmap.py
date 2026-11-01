"""Tests for roadmap.py and the session-start hook. Run from the repo root: python -m unittest discover tests

Standard library only. Everything runs in temp folders; "today" is fixed where it matters, so dates never go stale.
"""
import argparse
import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from datetime import date
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, "plugins", "project-board")
SCRIPT = os.path.join(PLUGIN, "skills", "plan", "scripts", "roadmap.py")
HOOK = os.path.join(PLUGIN, "hooks", "check_version.py")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


roadmap = load("roadmap", SCRIPT)
hook = load("check_version", HOOK)

SAMPLE = """# Lumen roadmap

Short intro. Last updated 20 October 2026.

## About the project

A sample.

## Schedule

**Schedule:** start 2026-11-02 · end 2026-11-30 · 29 days, 21 working days (5 days a week) · effort S=1 M=3 L=5 XL=10 working days

## Phase A: core

| # | Feature | Effort | Due | Status |
| --- | --- | --- | --- | --- |
| 1 | **Sign in.** Email. | M | 2026-11-04 | Done 2026-11-03 |
| 2 | **Profiles.** Name. | S | 2026-11-05 | In progress |
| 3 | **Search.** Fast. | L | 2026-11-12 | Not started |

Step 3 is built in two parts:

| Part | What | Effort | Due | Status |
| --- | --- | --- | --- | --- |
| 3a | The index. | S | 2026-11-09 | Done 2026-11-06 |
| 3b | The box. | S | 2026-11-12 | Not started |

## Later

| # | Feature | Status |
| --- | --- | --- |
| 9 | **Not a phase.** Left off. | Not started |
"""


def args(**kw):
    defaults = dict(start=None, days_per_week=None, off=None, effort=None, from_today=False, write=True)
    return argparse.Namespace(**{**defaults, **kw})


def run_schedule(text, **kw):
    rm = roadmap.Roadmap(text)
    with contextlib.redirect_stdout(io.StringIO()) as out:
        roadmap.schedule(rm, args(**kw))
    return rm, out.getvalue()


class TestStatus(unittest.TestCase):
    def test_columns(self):
        for status, col in [("On hold (waiting)", "hold"), ("Built, on hold", "hold"), ("Done 2026-10-22", "done"),
                            ("**Done**", "done"), ("In progress", "doing"), ("Being built", "doing"),
                            ("Built, waiting for a test", "doing"), ("Waiting for review", "doing"),
                            ("Next", "next"), ("Not started", "todo"), ("Planned", "todo"), ("Not done yet", "todo")]:
            self.assertEqual(roadmap.column_of(status), col, status)


class TestEffort(unittest.TestCase):
    def test_sizes(self):
        table = roadmap.DEFAULT_EFFORT
        for effort, days in [("S", 1), ("M", 3), ("xl", 10), ("S-M", 2), ("S–M", 2), ("4d", 4), ("4 days", 4), ("2.5", 2.5),
                             ("", None), ("huge", None)]:
            self.assertEqual(roadmap.effort_days(effort, table), days, effort)


class TestParse(unittest.TestCase):
    def test_sample(self):
        rm = roadmap.Roadmap(SAMPLE)
        self.assertEqual(rm.errors, [])
        self.assertEqual(rm.title, "Lumen roadmap")
        self.assertEqual([s["id"] for s in rm.steps], ["1", "2", "3"])
        self.assertEqual(rm.steps[0]["title"], "Sign in")
        self.assertEqual([p["id"] for p in rm.steps[2]["parts"]], ["3a", "3b"])

    def test_columns_in_any_order_and_other_names(self):
        text = "# X roadmap\n\n## Phase A: a\n\n| Status | Target | Task | # |\n| --- | --- | --- | --- |\n| Next | 2026-11-02 | **T.** d | F3 |\n"
        rm = roadmap.Roadmap(text)
        self.assertEqual(rm.errors, [])
        self.assertEqual((rm.steps[0]["id"], rm.steps[0]["col"], rm.steps[0]["due"]), ("F3", "next", date(2026, 11, 2)))

    def test_errors(self):
        self.assertTrue(any("no title" in e for e in roadmap.Roadmap("## Phase A: a\n").errors))
        self.assertTrue(any("no phases" in e for e in roadmap.Roadmap("# X roadmap\n").errors))
        self.assertTrue(any("no steps" in e for e in roadmap.Roadmap("# X\n\n## Phase A: a\n\nText.\n").errors))
        twice = "# X\n\n## Phase A: a\n\n| # | Feature | Status |\n| --- | --- | --- |\n| 1 | **A.** | Next |\n| 1 | **B.** | Next |\n"
        self.assertTrue(any("appears twice" in e for e in roadmap.Roadmap(twice).errors))
        orphan = "# X\n\n## Phase A: a\n\n| # | Feature | Status |\n| --- | --- | --- |\n| 1 | **A.** | Next |\n| 2a | **B.** | Next |\n"
        self.assertTrue(any("no step 2" in e for e in roadmap.Roadmap(orphan).errors))
        no_status = "# X\n\n## Phase A: a\n\n| # | Feature |\n| --- | --- |\n| 1 | **A.** |\n"
        self.assertTrue(any("no Status column" in e for e in roadmap.Roadmap(no_status).errors))

    def test_schedule_line(self):
        s = roadmap.parse_schedule("**Schedule:** start 2026-10-20 · end 2026-12-18 · 60 days, 44 working days (6 days a week) · effort S=1 M=2 working days · off 2026-12-25, 2026-12-26")
        self.assertEqual(s["start"], date(2026, 10, 20))
        self.assertEqual(s["end"], date(2026, 12, 18))
        self.assertEqual(s["per_week"], 6)
        self.assertEqual(s["effort"], {"S": 1.0, "M": 2.0})
        self.assertEqual(s["off"], [date(2026, 12, 25), date(2026, 12, 26)])

    def test_crlf_is_kept(self):
        text = SAMPLE.replace("\n", "\r\n")
        self.assertEqual(roadmap.Roadmap(text).text(), text)


class TestCalendar(unittest.TestCase):
    def test_weeks(self):
        friday, saturday, monday = date(2026, 11, 6), date(2026, 11, 7), date(2026, 11, 9)
        self.assertFalse(roadmap.Calendar(5, []).working(saturday))
        self.assertTrue(roadmap.Calendar(6, []).working(saturday))
        self.assertEqual(roadmap.Calendar(5, []).first_on_or_after(saturday), monday)
        self.assertEqual(roadmap.Calendar(5, []).nth(friday, 2), monday)

    def test_days_off(self):
        cal = roadmap.Calendar(5, [date(2026, 11, 9)])
        self.assertEqual(cal.nth(date(2026, 11, 6), 2), date(2026, 11, 10))
        self.assertEqual(cal.count(date(2026, 11, 2), date(2026, 11, 13)), 9)


class TestSchedule(unittest.TestCase):
    def test_done_steps_keep_their_dates_and_the_rest_follow_in_order(self):
        rm, _ = run_schedule(SAMPLE)
        by_id = {s["id"]: s for s in roadmap.Roadmap(rm.text()).steps}
        self.assertEqual(by_id["1"]["due"], date(2026, 11, 4))      # done: untouched
        self.assertEqual(by_id["2"]["due"], date(2026, 11, 2))      # S from the Monday start
        self.assertEqual(by_id["3"]["due"], date(2026, 11, 9))      # then L: 6 working days in

    def test_parts_share_their_steps_days(self):
        rm, _ = run_schedule(SAMPLE)
        parts = {p["id"]: p for p in roadmap.Roadmap(rm.text()).parts}
        self.assertEqual(parts["3a"]["due"], date(2026, 11, 9))     # done: untouched
        self.assertEqual(parts["3b"]["due"], date(2026, 11, 9))     # the only part left ends with the step

    def test_preview_changes_nothing(self):
        rm, out = run_schedule(SAMPLE, write=False)
        self.assertEqual(rm.text(), SAMPLE)
        self.assertIn("Only a preview", out)

    def test_settings_come_from_the_schedule_line_and_are_kept(self):
        rm, _ = run_schedule(SAMPLE, days_per_week=6, off="2026-11-03", effort="L=2")
        line = rm.lines[rm.schedule_line]
        self.assertIn("(6 days a week)", line)
        self.assertIn("off 2026-11-03", line)
        self.assertIn("L=2", line)
        again, _ = run_schedule(rm.text())
        self.assertEqual(again.lines[again.schedule_line], line)

    def test_a_start_on_a_weekend_moves_to_the_next_working_day(self):
        rm, _ = run_schedule(SAMPLE, start="2026-11-07")
        self.assertIn("start 2026-11-09", rm.lines[rm.schedule_line])

    def test_due_column_is_added_before_status(self):
        text = "# X roadmap\n\n## Phase A: a\n\n| # | Feature | Effort | Status |\n| --- | --- | --- | --- |\n| 1 | **A.** | S | Next |\n"
        rm, _ = run_schedule(text, start="2026-11-02")
        again = roadmap.Roadmap(rm.text())
        self.assertEqual(again.errors, [])
        self.assertEqual(again.steps[0]["due"], date(2026, 11, 2))
        self.assertEqual(again.steps[0]["col"], "next")
        self.assertIn("**Schedule:**", rm.text())

    def test_on_hold_steps_are_left_out(self):
        text = SAMPLE.replace("| In progress |", "| On hold (why) |")
        rm, _ = run_schedule(text)
        by_id = {s["id"]: s for s in roadmap.Roadmap(rm.text()).steps}
        self.assertEqual(by_id["2"]["due"], date(2026, 11, 5))      # kept
        self.assertEqual(by_id["3"]["due"], date(2026, 11, 6))      # L from the start

    def test_from_today(self):
        class Today(date):
            @classmethod
            def today(cls):
                return date(2026, 11, 16)

        with mock.patch.object(roadmap, "date", Today):
            rm, _ = run_schedule(SAMPLE, from_today=True)
        by_id = {s["id"]: s for s in roadmap.Roadmap(rm.text()).steps}
        self.assertEqual(by_id["2"]["due"], date(2026, 11, 16))
        self.assertIn("start 2026-11-02", rm.lines[rm.schedule_line])  # the start itself stays

    def test_no_start_date_stops(self):
        with self.assertRaises(SystemExit):
            run_schedule("# X roadmap\n\n## Phase A: a\n\n| # | Feature | Status |\n| --- | --- | --- |\n| 1 | **A.** | Next |\n")

    def test_scheduled_roadmap_passes_check(self):
        rm, _ = run_schedule(SAMPLE)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(roadmap.check(roadmap.Roadmap(rm.text())), 0)


class TempProject(unittest.TestCase):
    def setUp(self):
        self.project = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.project, ignore_errors=True)

    def write(self, name, text=""):
        path = os.path.join(self.project, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def read(self, name):
        with open(os.path.join(self.project, name), encoding="utf-8") as f:
            return f.read()

    def git(self):
        subprocess.run(["git", "init", "-q"], cwd=self.project, check=True)
        subprocess.run(["git", "add", "-A"], cwd=self.project, check=True)


class TestCheck(TempProject):
    def report(self, text):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = roadmap.check(roadmap.Roadmap(text))
        return code, out.getvalue()

    def test_warnings_do_not_fail_but_errors_do(self):
        with mock.patch.object(roadmap, "date", wraps=date) as fake:
            fake.today.return_value = date(2026, 12, 25)
            code, out = self.report(SAMPLE)
        self.assertEqual(code, 0)
        self.assertIn("overdue", out)
        self.assertEqual(self.report("## Phase A: a\n")[0], 1)

    def test_bad_date_is_an_error(self):
        code, out = self.report(SAMPLE.replace("2026-11-12 | Not started |\n\nStep", "soon | Not started |\n\nStep"))
        self.assertEqual(code, 1)
        self.assertIn("is not YYYY-MM-DD", out)

    def test_project_without_docs_gets_no_warnings(self):
        self.assertEqual(roadmap.docs_warnings(self.project), [])

    def test_unfilled_placeholders(self):
        self.write("README.md", "# X\n\n{{Fill this.}}\n\nAnd {{this}}.\n")
        self.assertEqual(len(roadmap.docs_warnings(self.project)), 1)
        self.assertIn("README.md has 2 unfilled", roadmap.docs_warnings(self.project)[0])

    def test_placeholders_in_code_are_the_projects_own(self):
        self.write("README.md", "Use `{{ name }}` here.\n\n```\n{{ other }}\n```\n")
        self.assertEqual(roadmap.docs_warnings(self.project), [])

    def test_listed_file_that_is_gone(self):
        self.write("a.py")
        self.write("LAYOUT.md", "| File | What |\n| --- | --- |\n| `a.py` | a |\n| `gone.py` | b |\n")
        warnings = roadmap.docs_warnings(self.project)
        self.assertEqual(len(warnings), 1)
        self.assertIn("gone.py", warnings[0])
        self.assertNotIn("a.py", warnings[0])

    def test_a_folders_table_may_use_bare_names(self):
        self.write("src/deep/a.py")
        self.write("LAYOUT.md", "### src/deep\n\n| File | What |\n| --- | --- |\n| `a.py` | a |\n")
        self.assertEqual(roadmap.docs_warnings(self.project), [])

    def test_commands_and_patterns_are_not_paths(self):
        self.write("LAYOUT.md", "| File | What |\n| --- | --- |\n| `python x.py` | a |\n| `*.log` | b |\n| `.../f.md` | c |\n")
        self.assertEqual(roadmap.docs_warnings(self.project), [])

    def test_tracked_file_not_listed(self):
        self.write("a.py")
        self.write("new.py")
        self.write(".gitignore", "ignored.py\n")
        self.write("ignored.py")
        self.write("LAYOUT.md", "| File | What |\n| --- | --- |\n| `a.py` | a |\n| `LAYOUT.md` | this |\n")
        self.git()
        warnings = roadmap.docs_warnings(self.project)
        self.assertEqual(len(warnings), 1)
        self.assertIn("doesn't list: new.py", warnings[0])

    def test_a_folders_line_covers_its_files(self):
        self.write("LAYOUT.md", "| File | What |\n| --- | --- |\n| `LAYOUT.md` | this |\n| `board/` | the board |\n")
        self.write("board/index.html")
        self.write("board/deep/x.js")
        self.git()
        self.assertEqual(roadmap.docs_warnings(self.project), [])

    def test_a_folder_listed_file_by_file_is_not_covered_by_its_line(self):
        self.write("src/a.py")
        self.write("src/new.py")
        self.write("LAYOUT.md", "| File | What |\n| --- | --- |\n| `LAYOUT.md` | this |\n| `src/` | code |\n| `src/a.py` | a |\n")
        self.git()
        self.assertIn("src/new.py", " ".join(roadmap.docs_warnings(self.project)))

    def test_a_long_list_is_shortened(self):
        for i in range(8):
            self.write(f"f{i}.py")
        self.write("LAYOUT.md", "| File | What |\n| --- | --- |\n| `LAYOUT.md` | this |\n")
        self.git()
        self.assertIn("and 3 more", roadmap.docs_warnings(self.project)[0])

    def test_outside_git_only_the_listed_files_are_checked(self):
        self.write("a.py")
        self.write("new.py")
        self.write("LAYOUT.md", "| File | What |\n| --- | --- |\n| `a.py` | a |\n")
        with mock.patch.object(roadmap, "tracked_files", return_value=None):
            self.assertEqual(roadmap.docs_warnings(self.project), [])

    def test_a_layout_still_in_the_readme_is_read(self):
        self.write("README.md", "# X\n\n## Project layout\n\n| File | What |\n| --- | --- |\n| `gone.py` | a |\n\n## Next\n\n| File | What |\n| --- | --- |\n| `other.py` | not the map |\n")
        warnings = roadmap.docs_warnings(self.project)
        self.assertEqual(len(warnings), 1)
        self.assertIn("README › Project layout", warnings[0])
        self.assertNotIn("other.py", warnings[0])


class TestInit(TempProject):
    def init(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            roadmap.init(self.project)
        return out.getvalue()

    def test_new_project_gets_everything(self):
        self.init()
        for name in ("ROADMAP.md", "README.md", "LAYOUT.md", "AGENTS.md", "CLAUDE.md", "board/index.html", "board/serve.py",
                     "board/FORMAT.md", "board/roadmap.py"):
            self.assertTrue(os.path.exists(os.path.join(self.project, name)), name)
        with open(os.path.join(PLUGIN, ".claude-plugin", "plugin.json"), encoding="utf-8") as f:
            self.assertEqual(self.read("board/VERSION").strip(), json.load(f)["version"])

    def test_nothing_of_the_users_is_overwritten(self):
        names = ("ROADMAP.md", "README.md", "LAYOUT.md", "AGENTS.md", "CLAUDE.md")
        for name in names:
            self.write(name, "mine")
        self.init()
        for name in names:
            self.assertEqual(self.read(name), "mine", name)

    def test_older_board_files_are_replaced(self):
        self.write("board/index.html", "old")
        self.write("board/VERSION", "1.0.0\nskip 1.1.0\n")
        self.init()
        self.assertNotEqual(self.read("board/index.html"), "old")
        self.assertNotIn("skip", self.read("board/VERSION"))

    def test_own_claude_md_means_no_agents_md(self):
        self.write("CLAUDE.md", "mine")
        self.assertIn("skipped: AGENTS.md", self.init())
        self.assertFalse(os.path.exists(os.path.join(self.project, "AGENTS.md")))

    def test_readme_with_a_layout_means_no_layout_md(self):
        self.write("README.md", "# X\n\n## Project layout\n\nmine\n")
        self.assertIn("skipped: LAYOUT.md", self.init())
        self.assertFalse(os.path.exists(os.path.join(self.project, "LAYOUT.md")))

    def test_a_projects_own_copy_keeps_the_version(self):
        self.init()
        self.write("board/VERSION", "1.3.0\n")
        copy = load("project_copy", os.path.join(self.project, "board", "roadmap.py"))
        with contextlib.redirect_stdout(io.StringIO()):
            copy.init(self.project)
        self.assertEqual(self.read("board/VERSION"), "1.3.0\n")


class TestHook(TempProject):
    def setUp(self):
        super().setUp()
        self.write("board/index.html")
        self.write("board/roadmap.py")
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self.project)

    def run_hook(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            hook.main()
        return out.getvalue()

    def newest(self):
        with open(os.path.join(PLUGIN, "skills", "plan", "CHANGES.md"), encoding="utf-8") as f:
            versions = [line.split()[1] for line in f if line.startswith("## ")]
        return versions[0], versions[-1]

    def test_up_to_date_is_silent(self):
        self.write("board/VERSION", self.newest()[0] + "\n")
        self.assertEqual(self.run_hook(), "")

    def test_no_stamp_shows_every_section(self):
        out = self.run_hook()
        self.assertIn("an older version", out)
        self.assertIn(f"{self.newest()[1]}:", out)

    def test_an_older_stamp_shows_only_what_is_newer(self):
        newest, oldest = self.newest()
        self.write("board/VERSION", oldest + "\n")
        out = self.run_hook()
        self.assertIn(f"{newest}:", out)
        self.assertNotIn(f"\n{oldest}:\n", out)

    def test_not_now_is_silent_until_a_newer_section(self):
        newest, oldest = self.newest()
        self.write("board/VERSION", f"{oldest}\nskip {newest}\n")
        self.assertEqual(self.run_hook(), "")
        self.write("board/VERSION", f"{oldest}\nskip {oldest}\n")
        self.assertIn(f"set up with {oldest}", self.run_hook())

    def test_not_now_without_a_stamp(self):
        self.write("board/VERSION", f"skip {self.newest()[1]}\n")
        self.assertIn("an older version", self.run_hook())

    def test_a_folder_without_a_board_is_silent(self):
        os.remove("board/roadmap.py")
        self.assertEqual(self.run_hook(), "")


if __name__ == "__main__":
    unittest.main()
