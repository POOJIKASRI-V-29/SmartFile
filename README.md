# SmartFile

**OS-Based File Management & Storage Optimization System**

A desktop application that scans a directory, classifies files by type, detects
duplicate files by content, analyses storage usage, and safely organises files
into category folders — with a preview before every change and an undo
afterwards.

Built as an Operating Systems course project.

---

## 1. Problem Statement

Folders such as `Downloads` accumulate hundreds of unsorted files. The operating
system stores each file's metadata (name, size, timestamps, location in the
directory tree), but it does not organise files by meaning, and it does not tell
the user which files are exact duplicates wasting disk space.

Manually sorting these files is slow and risky: a careless move can overwrite an
existing file, and a careless delete loses data permanently.

## 2. Motivation

SmartFile applies operating-system file-handling concepts to a real, everyday
problem. It demonstrates directory traversal, file metadata, file operations and
storage management — while being safe enough to run on a real folder, because it
never deletes anything and never overwrites an existing file.

## 3. Features

| Feature | Description |
|---|---|
| Recursive scanning | Walks the whole directory tree and reads each file's metadata |
| Automatic classification | Sorts files into 8 categories by extension |
| Preview before action | Shows every proposed move, conflict and skip before anything happens |
| Safe organisation | Moves files into category folders; auto-renames instead of overwriting |
| Duplicate detection | Finds byte-identical files using SHA-256 content hashing |
| Storage analysis | Charts and tables of storage usage by category, extension and size |
| Operation history | Every organise run is logged to a JSON file |
| Undo | Restores files from the last operation to their original paths |
| Error tolerance | Permission errors, broken links and unreadable files are skipped, not fatal |

## 4. Operating Systems Concepts Demonstrated

| OS Concept | Where it appears in SmartFile |
|---|---|
| File system & directory structure | Recursive traversal of the directory tree with `os.walk` |
| File metadata | Reading size and timestamps via the `stat()` system call |
| File operations | Move (`shutil.move`), create directory (`mkdir`), read (`open`) |
| Storage management | Aggregating file sizes; reporting recoverable space from duplicates |
| File permissions & access control | Read-permission checks; `PermissionError` handled per file |
| Path management | Absolute vs relative paths, path resolution, symbolic-link handling |
| Safe file manipulation | No deletes, no overwrites, unique-name generation, preview + undo |
| File organisation | Classification and grouping of files into category directories |
| Buffered I/O | Hashing large files in fixed 64 KB chunks instead of loading them whole |

SmartFile is an *application that uses* operating-system file services. It does
not implement an operating system or a file system of its own.

## 5. Architecture

```
                 ┌──────────────────────────┐
                 │  Streamlit UI (main.py)  │
                 │  6 sections, no FS logic │
                 └────────────┬─────────────┘
                              │ calls
   ┌──────────┬───────────┬───┴──────┬────────────┬──────────┐
   │ scanner  │classifier │organizer │ duplicate_ │ storage_ │
   │          │           │          │ detector   │ analyzer │
   └────┬─────┴─────┬─────┴────┬─────┴──────┬─────┴────┬─────┘
        │           │          │            │          │
        └───────────┴────┬─────┴────────────┴──────────┘
                         │ uses
              ┌──────────┴───────────┬──────────────┐
              │ models.py (records)  │ utils.py     │ history.py
              └──────────────────────┴──────────────┴───────────
                         │
              ┌──────────┴──────────┐
              │  Operating System   │
              │  os / pathlib /     │
              │  shutil / hashlib   │
              └─────────────────────┘
```

The UI layer contains no file-system logic; every module can be tested on its
own without Streamlit running.

## 6. Tech Stack

- **Python 3.9+** — `os`, `pathlib`, `shutil`, `hashlib`, `json` from the standard library
- **Streamlit** — user interface
- **Pandas** — tabular aggregation
- **Plotly** — charts
- **pytest** — automated tests

No database, no web server, no cloud service, no machine learning.

## 7. Installation

```bash
cd smartfile
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 8. Running the Application

```bash
./run.sh
```

or directly:

```bash
python3 -m streamlit run app/main.py
```

The application opens at `http://localhost:8501`.

## 9. How to Use

1. **Scan** — enter a directory in the sidebar (or press *Use sample_data*) and press **SCAN**.
2. **Dashboard** — see files scanned, total storage, duplicates and recoverable space.
3. **Scanner** — browse every file with its category, size and modified time.
4. **Organize** — press **PREVIEW**, read the proposed changes, tick the confirmation box, then press **ORGANIZE**.
5. **Duplicates** — expand each group to see the shared SHA-256 hash and every copy's path.
6. **Storage Analysis** — charts of storage and file count per category, plus the largest files.
7. **History** — review past operations and press **Undo Last Operation** to reverse the most recent one.

Start with `sample_data/` — it is built for demonstration and contains no real data.

## 10. Screenshots

Place demonstration screenshots here before submission:

- `docs/screenshot_dashboard.png` — Dashboard with metric cards
- `docs/screenshot_preview.png` — Organize preview table
- `docs/screenshot_duplicates.png` — Duplicate group with SHA-256 hash
- `docs/screenshot_storage.png` — Storage analysis charts
- `docs/screenshot_history.png` — History with undo button

## 11. Testing

```bash
python3 -m pytest -v
```

67 tests cover scanning, classification, duplicate detection, preview,
conflict handling, movement, undo and storage calculations. Every test runs
inside a pytest temporary directory, so no real user file is ever touched.

## 12. Limitations

- Classification is based on the file extension only. A `.txt` file renamed to `.jpg` is classified as an image.
- Duplicate detection reports duplicates but never deletes them; the user decides what to do.
- Undo restores only the most recent organise operation that has not already been undone.
- If a file is moved or renamed outside SmartFile after being organised, undo reports that file as not found instead of guessing.
- Hashing a very large directory takes time, because files of equal size must be read in full.
- Files moved to a category folder are not tracked if the user later moves them manually.
- Tested on macOS and Linux. On Windows, creation time is read from `st_ctime`.

## 13. Future Enhancements

- Optional content-based type detection using magic numbers instead of extensions
- User-configurable classification rules saved to a settings file
- Reviewed, confirmed deletion of duplicate copies (with a recycle-bin step)
- Undo of any past operation, not only the most recent one
- Scheduled background scanning of a chosen folder
- Export of the storage report as CSV or PDF
