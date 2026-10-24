# Shelf roadmap

The plan for Shelf, phase by phase. The project board (`board/`) shows it as a kanban board:
`python board/serve.py`. Format: `board/FORMAT.md`. Last updated 16 October 2026.

## About the project

A calm reading tracker: keep the books you want to read, the one you're reading and what you thought of it.

Shelf is a small web app for people who read on paper and on screens. Add a book in seconds by scanning its barcode
or typing a title, track pages read, and keep a short note when you finish.

It works offline first and syncs when it can, so it's as quick on a train as at home.

## Schedule

**Schedule:** start 2026-10-05 · end 2026-11-23 · 50 days, 35 working days (5 days a week) · effort S=1 M=3 L=5 XL=10 working days · off 2026-10-26

## How we work

- **Statuses:** Not started → Next → In progress → Done YYYY-MM-DD. "Built, waiting for …" while something outside
  the code is pending. On hold (with a note saying why).
- **Dates:** each step's Due date comes from its effort size and its order (`roadmap.py schedule`).

## Phase A: the reading list

A list of books that works offline: add, edit, mark as reading or read.

| # | Feature | Effort | Due | Status |
| --- | --- | --- | --- | --- |
| 1 | **Project setup.** The app shell, offline storage and deployment to a test address. | S | 2026-10-05 | Done 2026-10-05 |
| 2 | **Add a book.** Title, author and cover from a search, or typed by hand. | M | 2026-10-08 | Built, waiting for a design review |
| 3 | **The list.** Want to read, Reading and Read, with drag to reorder. | M | 2026-10-13 | Done 2026-10-14 |
| 4 | **Barcode scan.** Add a book by pointing the phone camera at its barcode. | L | 2026-10-20 | In progress |

Step 4 is built in parts:

| Part | What | Effort | Due | Status |
| --- | --- | --- | --- | --- |
| 4a | The camera view and barcode reading. | M | 2026-10-16 | Done 2026-10-16 |
| 4b | Looking the ISBN up and filling in the book. | S | 2026-10-19 | In progress |
| 4c | Fallbacks: no camera, unknown ISBN, poor light. | S | 2026-10-20 | Not started |

Decisions for Phase A:

- Offline first (5 October 2026): the list must work with no connection; sync comes in Phase B.

## Phase B: progress and sync

Track pages and sync between devices.

| # | Feature | Effort | Due | Status |
| --- | --- | --- | --- | --- |
| 5 | **Pages read.** Log pages per session; a progress bar per book. | M | 2026-10-23 | Next |
| 6 | **Accounts and sync.** Sign in and sync the shelf between devices. | XL | 2026-11-09 | Not started |
| 7 | **Notes.** A short note and a star rating when you finish a book. | S | 2026-11-10 | Not started |

## Phase C: launch

| # | Feature | Effort | Due | Status |
| --- | --- | --- | --- | --- |
| 8 | **Reading stats.** Books and pages per month, the current streak. | M | 2026-11-13 | Not started |
| 9 | **Import.** From a Goodreads export file. | M | 2026-11-18 | On hold (14 October 2026: waiting for the export format) |
| 10 | **Launch.** App icons, store listing, a landing page. | M | 2026-11-23 | Not started |

Step 9 is **on hold**. Goodreads is changing its export file; the import waits until the new format is published.

## Later

- Book clubs: share a shelf with friends.
