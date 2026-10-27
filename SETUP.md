# Halal Money Plan — AMU 2027

Open **Halal-Income-Enhanced.html** in a modern browser. It contains the complete application, styles, JavaScript, SVG icons and all 30 supplied opportunities. It has no framework, build step, backend, tracking or runtime network dependency.

For a consistent browser-storage origin during development, run:

```sh
cd /workspace/AMU-money
python -m http.server 8765 --bind 127.0.0.1
```

Open the HTML file through that server in your browser. Some managed browsers block local `file:` URLs. Browser storage for a local file can also differ between browsers; importing a backup is the supported way to move data between origins, browsers or devices.

## Using the planner

- **Explore:** combine search words, category, capital, difficulty, hardware and quick tags. Remove individual filter chips or reset all filters. Switch between cards and a table; choose table columns and desktop card columns. Preferences survive reloads.
- **Student mode:** combine a preset with an upper weekly-hours limit. Zero means no additional limit. These are estimates from the supplied content, not scheduling guarantees.
- **Plan:** track each roadmap step, save exact-text notes, inspect note version history, bookmark, compare or copy a summary. The dashboard offers a shortcut to your most recently opened plan.
- **Compare:** keep up to three unique opportunities. A fourth choice offers explicit replacement. On narrow screens, comparison details become vertically stacked cards.
- **Launch path and vault:** track the general launch checklist and capture ideas. Removing ideas, clearing saved plans/comparisons and hiding widgets offer Undo.
- **Customize:** choose themes, typography, spacing, motion, appearance and widget order/visibility. Export a backup or preview an import here. Import merges personal data; choose which conflicting notes to use and whether to restore appearance. Both note versions remain recoverable.
- **Gestures:** hold a card's icon to bookmark it; swipe only the labelled navigation rail to change pages. Moving, scrolling, cancelling a pointer, selecting text or adding a second touch cancels a hold. Every action has button/keyboard alternatives.
- **Keyboard:** `?` opens help. `/` focuses search. `1`–`7` navigate pages. `G`, then `D/S/T/C/P/B/U`, also navigates. `Ctrl/Command K` opens Quick jump outside ordinary text inputs. Escape closes the active dialog. Shortcuts do not interpret ordinary typing as navigation.

## Data and recovery

The existing `hios.settings`, `hios.favs`, `hios.notes`, `hios.checklist`, `hios.vault` and `hios.compare` values are migrated without deleting those original entries. New state uses a validated `hios.base.v2` plus immutable `hios.op.*` field-change records. Tabs merge unrelated changes instead of writing stale full snapshots. Concurrent changes to the same field resolve in a deterministic order; note versions remain available. This is browser-local storage, **not encrypted storage** or a cloud backup.

Notes preserve literal HTML entities, whitespace and multilingual text. Content is escaped at HTML rendering boundaries, and notes are assigned to textarea values. Note history shows up to 20 recent distinct versions per plan; imports can retain up to 600 recovered versions in total. The idea vault holds 200 entries of up to 1,000 characters. Backups accept supported version 1 or version 2 JSON up to 12 MB; invalid IDs, duplicate comparison entries and malformed structures are rejected.

Storage may be blocked, full or cleared by a browser. Changes remain available in the current tab and can be exported when writing fails. The UI reports session-only storage. Journal records are intentionally retained to support conflict recovery; they consume browser quota over time. Export regularly and keep backups private. Neither this application nor a backup file supplies encryption.

The planner is independent and does not claim official AMU affiliation. Earnings and timelines are unverified illustrations preserved from the supplied guide. Religious considerations are educational, not individual scholarly rulings. No current market research, endorsements or certifications were added.

## Developer validation

`tests/regression.py` uses Python Playwright, a system Chromium binary and axe-core for QA only. None is loaded by the application. With these tools installed, run the local server above, then:

```sh
python tests/regression.py
```

Optional environment overrides: `AMU_TEST_URL`, `CHROMIUM_PATH`, `AXE_PATH`. `AXE_PATH` defaults to `/tmp/amu-qa/node_modules/axe-core/axe.min.js`. To install the QA scanner outside the application:

```sh
npm install --prefix /tmp/amu-qa --cache /tmp/amu-npm-cache --no-audit --no-fund axe-core
```

Install Python Playwright in your preferred development environment if it is absent. The test runner saves JSON results and screenshots under `qa/`. The final validation report describes executed checks and coverage limits; passing an automated accessibility scanner does not constitute a WCAG certification.
