# csv-dis

A local, read-only CSV viewer for Windows. `csv-dis` opens **one** CSV file and shows it as a fast, sortable, filterable table with cross-column search. The file on disk is never modified — everything you do only affects the view.

![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)
![License: GPLv3](https://img.shields.io/badge/license-GPLv3-blue)

## Features

- **One file per window** — open via file dialog, command line, or drag & drop.
- **Read-only** — no editing, no saving, no accidental changes to your data.
- **Fast table** — virtualised model, tested with up to 1,000,000 rows / ~100 MB.
- **Automatic parser detection** — BOM, encoding (UTF-8, Windows-1252 fallback), and delimiter (`;`, `,`, tab, `|`).
- **Manual parser correction** — change delimiter and encoding after opening via *File → Delimiter and Encoding…* and reload.
- **Column types** — numbers, ISO dates, and text are detected automatically. The original text is always displayed unchanged; the type only affects sorting and filter operators.
- **Filtering** — one filter per column, combined with AND, shown as removable chips in a filter bar.
- **Sorting** — click a column header to sort ascending, click again for descending. Empty cells sort to the end in both directions.
- **Hide columns** — via the header menu; show them again at any time.
- **Cross-column search** — highlights matches in all visible columns without changing the rows shown. Navigate hits with *Back*/*Next*; multiple terms are AND-combined per row.
- **Non-blocking** — loading, filtering, sorting, and searching run in the background with cancellation, so the window stays responsive.
- **No state kept** — after a restart, no file is open and no filter is active.
- **Packaged build** — ships as a self-contained `csv-dis.exe` with its own icon, splash screen, and an *About* dialog listing runtime library versions.

## Non-goals

`csv-dis` deliberately does **not** support:

- editing or saving data
- exporting the view (CSV, Excel, PDF, …)
- servers, databases, or user management
- multiple files at once or file comparison
- grouping, aggregation, charts, or formulas

## Requirements

- Windows 10/11 (primary target)
- Python **3.12 or newer** for running from source
- [PyQt6](https://pypi.org/project/PyQt6/) ≥ 6.7 and [Polars](https://pypi.org/project/polars/) ≥ 2.1 (installed automatically)

The user interface is in **German**; the source code, comments, and project documentation are German as well.

## Installation

Clone the repository and install into a virtual environment:

```powershell
git clone https://github.com/ralfJoswig/csv-dis.git
cd csv-dis
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

## Running

Start the application:

```powershell
.\.venv\Scripts\python.exe -m csv_dis
```

Or open a file directly:

```powershell
.\.venv\Scripts\python.exe -m csv_dis "C:\path\to\file.csv"
```

After an editable install, the `csv-dis` entry point is available as well.

### Prebuilt executable

If a build is present, run it directly:

```powershell
.\dist\csv-dis\csv-dis.exe "C:\path\to\file.csv"
```

The whole `dist\csv-dis\` folder is required — not just the `.exe`. Note that only the packaged executable shows the application's own icon in the Windows taskbar; when started with `python -m csv_dis`, Windows uses the Python host icon.

## Supported CSV input

- **Encoding:** BOM is stripped; UTF-8 is read strictly, falling back to Windows-1252 with a warning. The encoding can be overridden manually.
- **Delimiters:** semicolon, comma, tab, and pipe. Detection uses the header's field count as an anchor.
- **Quoting:** RFC 4180, including delimiters and line breaks inside quoted fields.
- **Header:** the first line is always treated as the header. Empty names become `Spalte N`; duplicates are made unique as `Name (2)`.
- **Ragged rows:** short rows are padded with empty cells; surplus fields are dropped and reported.
- **Empty cells** are ignored during type detection.

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+O` | Open file |
| `Ctrl+F` | Focus search field |
| `Enter` / `Shift+Enter` | Next / previous search hit |
| `Esc` | Clear search and remove highlights |
| `Ctrl+Q` | Quit |

## Building the executable

PyInstaller is included in the `dev` extra. Build with:

```powershell
.\.venv\Scripts\python.exe tools\build_exe.py
```

The result is written to `dist\csv-dis\` (windowed `.exe` with embedded icon, plus `LICENSE` and `THIRD-PARTY-NOTICES.md`). The build folder is large (~250 MB) and must be distributed as a whole.

## Development

### Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

The GUI tests run headless via `QT_QPA_PLATFORM=offscreen` (set in `tests/conftest.py`). Current status: **120 tests passing**.

Useful helpers:

```powershell
# Generate a large synthetic CSV for performance checks
.\.venv\Scripts\python.exe tools\make_large_csv.py --rows 1000000

# Regenerate the application icon
.\.venv\Scripts\python.exe tools\make_icon.py
```

### Project layout

```
src/csv_dis/
  app.py            entry point, splash screen, AppUserModelID
  main_window.py    window, file handling, filter bar, search, live queries
  csv_loader.py     delimiter/encoding detection and parsing
  column_types.py   number/date/text detection
  query.py          filter expressions (AND) and sorting via Polars
  search.py         hit calculation without GUI
  search_bar.py     search field, hit counter, navigation
  model.py          QAbstractTableModel over Polars, hit highlighting
  header.py         header row with filter icon
  filter_dialog.py  per-column filter popup
  parser_dialog.py  delimiter/encoding dialog
  about_dialog.py   "About csv-dis" with license and library versions
  splash.py         splash screen
  resources.py      icon loading from package data
tests/              pytest suite (unit + headless GUI)
tools/              build, icon, and test-data generators
docs/               specifications and architecture decision records
```

### Documentation

Project documentation is written in German:

- `docs/v1-spec.md` — v1 scope and acceptance criteria
- `docs/v2-spec.md` — v2 scope and acceptance criteria (current)
- `CONTEXT.md` — domain glossary
- `docs/adr/` — architecture decision records
- `STATUS.md`, `TODO.md`, `CHANGELOG.md`, `HANDOFF.md` — project memory
- `AGENTS.md` — working rules for contributors and AI agents

## License

`csv-dis` is licensed under the **GNU General Public License v3.0** (GPLv3), copyright Ralf Joswig. See [`LICENSE`](LICENSE) for the full text.

PyQt6 is licensed under GPL-3.0-only, which is why the application as a whole is GPLv3. Third-party license texts are collected in [`THIRD-PARTY-NOTICES.md`](THIRD-PARTY-NOTICES.md):

- PyQt6 — GPL-3.0-only
- Qt — LGPLv3
- Polars — MIT
- Python — PSF License
