# {{Project name}} roadmap

{{One or two sentences: what this file is and how it's used.}} The project board (`board/`) shows it as a kanban
board: `python board/serve.py`. Format: `board/FORMAT.md`. Last updated {{D Month YYYY}}.

## About the project

{{The one-line description of the project.}}

{{A paragraph on what it does and for whom.}}

{{A paragraph on how it works, or what makes it different.}}

## Schedule

**Schedule:** start {{YYYY-MM-DD}} · end {{YYYY-MM-DD}} · {{N}} days, {{N}} working days ({{5}} days a week) · effort S=1 M=3 L=5 XL=10 working days

## How we work

- **Statuses:** Not started → Next → In progress → Done YYYY-MM-DD. "Built, waiting for …" while something outside
  the code is pending (a test, a review). On hold (with a "Step N is **on hold**" note saying why).
- **Dates:** each step's Due date comes from its effort size and its order (`roadmap.py schedule`). When a step slips,
  the steps after it are rescheduled and the change is noted under the phase's decisions.
- **Decisions** are recorded under each phase, with the date, so the reasons stay with the plan.

## Phase A: {{the first phase}}

{{One sentence: what this phase delivers.}}

| # | Feature | Effort | Due | Status |
| --- | --- | --- | --- | --- |
| 1 | **{{Step title}}.** {{What it does, in a sentence or two.}} | M | {{YYYY-MM-DD}} | Not started |
| 2 | **{{Step title}}.** {{What it does.}} | S | {{YYYY-MM-DD}} | Not started |

Decisions for Phase A:

- {{Decision (date): what was decided and why.}}

## Phase B: {{the second phase}}

{{One sentence: what this phase delivers.}}

| # | Feature | Effort | Due | Status |
| --- | --- | --- | --- | --- |
| 3 | **{{Step title}}.** {{What it does.}} | L | {{YYYY-MM-DD}} | Not started |

Step 3 is built in parts:

| Part | What | Effort | Due | Status |
| --- | --- | --- | --- | --- |
| 3a | {{The first part.}} | M | {{YYYY-MM-DD}} | Not started |
| 3b | {{The second part.}} | S | {{YYYY-MM-DD}} | Not started |

## Later

{{Ideas not planned yet. Steps here are not on the board until they move into a phase.}}

## Risks and open questions

- {{Risk or question: what could go wrong, and the plan for it.}}
