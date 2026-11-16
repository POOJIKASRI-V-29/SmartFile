# SmartFile: OS-Based File Management & Storage Optimization System

**Project Report — Operating Systems**

---

## Abstract

SmartFile is a desktop application that helps a user manage and optimise the
files in a directory. It recursively traverses a directory tree, reads each
file's metadata from the file system, classifies files into categories by type,
detects duplicate files by comparing their content hashes, analyses how storage
is being used, and organises files into category folders after showing the user
a complete preview of the proposed changes. Every organise operation is logged
and can be undone. The system is built in Python using the operating system's
own file-handling services, and it is designed around a strict safety rule: no
file is ever deleted and no existing file is ever overwritten.

---

## 1. Introduction

An operating system provides a file system: a way to store data as named files,
arrange them in a hierarchy of directories, and record metadata about each one
(its size, its owner, when it was created and last modified). The OS provides
system calls — `stat()`, `open()`, `read()`, `rename()` — through which programs
use these services.

What the operating system does *not* do is decide how files should be arranged
for a human being's convenience. A `Downloads` folder with 800 mixed files is
perfectly valid from the file system's point of view, and the OS has no opinion
about the three identical copies of the same PDF sitting in it.

SmartFile is an application layer built on top of those OS services. It reads
what the file system knows, adds an organising policy of its own, and then uses
the OS's file operations to act on that policy safely.

---

## 2. Problem Statement

Users accumulate large numbers of unorganised files in a small number of
directories. This causes three concrete problems:

1. **Difficulty locating files** — a flat directory of hundreds of mixed files is slow to search visually.
2. **Wasted storage** — the same file is downloaded or copied repeatedly under different names, and the duplicates are invisible.
3. **Risk during manual cleanup** — moving files by hand can silently overwrite a file with the same name, or delete something still needed.

A tool is needed that organises files automatically, identifies genuine
duplicates by content rather than by name, and does so without any risk of
data loss.

---

## 3. Objectives

1. Traverse a directory tree recursively and collect each file's metadata.
2. Classify files into meaningful categories automatically.
3. Show a complete preview of proposed changes before any file is touched.
4. Move files into category folders without deleting or overwriting anything.
5. Detect duplicate files reliably using content hashing.
6. Report storage usage with clear charts and tables.
7. Maintain a history of operations and support undo.
8. Handle permission errors, broken links and inaccessible files without crashing.
9. Validate all of the above with automated tests.

---

## 4. Existing Approach and Its Problems

| Approach | Problem |
|---|---|
| Manual sorting through a file explorer | Slow; drag-and-drop can overwrite a same-named file with no warning |
| Sorting by name or type in the file explorer | Only changes the *view*; files stay physically unorganised |
| Shell scripts (`mv *.pdf Documents/`) | No preview, no undo, overwrites silently, no duplicate detection |
| "Duplicate finder" utilities | Often match by filename or size only, producing false matches; many delete automatically |
| Commercial cleaners | Closed source, often aggressive, may delete without meaningful review |

The common weakness is that these approaches act first and inform the user
afterwards — if at all.

---

## 5. Proposed System

SmartFile separates **deciding** from **doing**.

```
   Scan  ──►  Classify  ──►  Plan (preview)  ──►  [ USER CONFIRMS ]  ──►  Execute  ──►  Log
                                    │                                                    │
                                    │  nothing on disk has changed yet                   │
                                    ▼                                                    ▼
                            user may cancel freely                                     Undo
```

The planning phase reads metadata only and produces a list of proposed moves,
including any name conflicts it detected and any files it intends to skip. The
user sees this list in full. Only after an explicit confirmation does SmartFile
execute the plan, and every executed move is recorded so that it can be reversed.

---

## 6. System Architecture

SmartFile uses a three-layer architecture:

```
┌──────────────────────────────────────────────────────────────┐
│ PRESENTATION LAYER       app/main.py (Streamlit)             │
│ Dashboard · Scanner · Organize · Duplicates · Storage · History│
│ Contains no file-system logic                                 │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│ LOGIC LAYER                                                   │
│ scanner.py  classifier.py  organizer.py                       │
│ duplicate_detector.py  storage_analyzer.py  history.py        │
│ models.py (data records)   utils.py (safety helpers)          │
└───────────────────────────┬──────────────────────────────────┘
                            │ standard library calls
┌───────────────────────────▼──────────────────────────────────┐
│ OPERATING SYSTEM LAYER                                        │
│ os.walk · Path.stat() · shutil.move · mkdir · open · hashlib  │
│           ↓ system calls ↓                                    │
│              File system (directories, inodes, blocks)        │
└──────────────────────────────────────────────────────────────┘
```

Because the logic layer never imports Streamlit, every module can be tested
directly by pytest without a UI.

---

## 7. Modules

### 7.1 `models.py`
Defines the data records passed between modules: `FileRecord` (one file's
metadata), `ScanResult` (files found plus items skipped), `PlannedMove` and
`OrganizePreview` (the proposed plan), `DuplicateGroup`, and `OperationResult`.
Using plain dataclasses keeps the data easy to inspect and easy to convert into
a pandas DataFrame.

### 7.2 `scanner.py`
Walks the directory tree with `os.walk` and calls `stat()` on each file to read
its size and timestamps. Handles hidden files, nested directories, empty
directories, broken symbolic links and permission errors. Anything that cannot
be read is added to a `skipped` list with a reason, so the scan always finishes.

### 7.3 `classifier.py`
Maps file extensions to eight categories (Documents, Images, Videos, Audio,
Archives, Code, Executables, Others). A reverse lookup dictionary is built once
at import time, making each classification a single O(1) dictionary lookup.

### 7.4 `organizer.py`
Contains the preview planner and the executor. `build_preview()` is a pure
function: it produces the plan without touching the disk. `organize()` executes
an approved plan using `shutil.move`, re-checking each destination at the moment
of the move. `undo_operation()` reverses a logged operation.

### 7.5 `duplicate_detector.py`
Implements two-pass duplicate detection: group by size first (free, from
metadata), then hash only the files whose sizes collide. Hashing reads the file
in 64 KB chunks so memory use stays constant regardless of file size.

### 7.6 `storage_analyzer.py`
Aggregates the scan into per-category and per-extension statistics using pandas,
and builds the Plotly bar, donut and table visualisations.

### 7.7 `history.py`
Appends each operation to a JSON file with its id, timestamp, root directory and
the full list of source → destination pairs. Provides lookup of the most recent
un-undone operation and marks operations as undone.

### 7.8 `utils.py`
Shared safety helpers: human-readable sizes, timestamp formatting,
`safe_unique_path()` (never returns an existing path), `is_protected_path()`
(detects system directories), `is_app_path()` (protects SmartFile's own source)
and directory validation.

---

## 8. Operating Systems Concepts Demonstrated

### 8.1 File System and Directory Structure
A file system organises data into files and arranges files in a hierarchy of
directories, forming a tree. SmartFile's scanner traverses this tree from a
chosen root down through every subdirectory, which is exactly the structure the
OS maintains. Creating category folders adds new nodes to that tree.

### 8.2 File Metadata
The OS stores information *about* each file separately from its contents — in an
inode on UNIX-like systems, or an MFT record on NTFS. This includes size,
permissions, and timestamps. SmartFile reads this through `Path.stat()`, which
invokes the `stat()` system call. Notably, `st_mtime` (modification time) is
available everywhere, while creation time is available as `st_birthtime` only on
macOS/BSD — a genuine difference between operating systems, which the code
handles with a fallback.

### 8.3 File Operations
The standard file operations an OS provides are create, open, read, write,
rename/move, and delete. SmartFile uses create (category directories), read
(hashing file contents) and move (`shutil.move`, which uses `rename()` when the
source and destination are on the same file system, and a copy-then-remove when
they are not). It deliberately does **not** use delete.

### 8.4 File Permissions and Access Control
The OS enforces read/write/execute permissions per file and directory. A program
cannot bypass them. SmartFile checks read access before scanning and catches
`PermissionError` on every individual file, recording it as skipped rather than
crashing — which is how a well-behaved application must react to an access
denial by the kernel.

### 8.5 Storage Management
The OS allocates disk space in blocks and tracks usage. SmartFile aggregates the
sizes reported by the file system to show where storage is being consumed, and
computes how much space is redundantly occupied by duplicate content.

### 8.6 Path Management
The OS resolves paths, distinguishes absolute from relative paths, and supports
symbolic links that point to other paths. SmartFile stores both the absolute
path (for operations) and the path relative to the scan root (for display),
resolves paths before comparing them, and detects broken symbolic links —
entries that exist in a directory but point to a target that does not.

### 8.7 Buffered I/O
Reading an entire large file into memory is wasteful. SmartFile reads files in
fixed 64 KB chunks when hashing, mirroring how the OS itself transfers data in
blocks, so memory usage stays constant for a 4 GB file.

### 8.8 Safe File Manipulation
File operations are not atomic from a user's point of view: a move that
overwrites destroys data irrecoverably. SmartFile enforces safety by generating
unique destination names, re-verifying at execution time, logging every move,
and providing undo.

> **Scope note:** SmartFile is an application that *uses* operating-system file
> services. It does not implement an operating system, a kernel, or a file system.

---

## 9. Algorithms

### A. Recursive Directory Traversal

```
FUNCTION scan(root):
    result ← empty
    FOR EACH (directory, subdirs, files) IN walk(root):
        remove ignored and hidden entries from subdirs   # prunes the walk
        IF directory has no subdirs and no files:
            record as empty directory
        FOR EACH file IN files:
            TRY:
                IF file is a broken symbolic link: record as skipped; CONTINUE
                metadata ← stat(file)                    # system call
                result.add(FileRecord from metadata)
            CATCH PermissionError / OSError:
                result.skipped.add(file, reason)         # never abort the scan
    RETURN result
```

Complexity: O(n) in the number of files and directories visited.

### B. File Classification

```
Build once:  EXT_TO_CATEGORY = { ".pdf": "Documents", ".jpg": "Images", ... }

FUNCTION classify(filename):
    ext ← lowercase extension of filename      # "" for dotfiles like .gitignore
    RETURN EXT_TO_CATEGORY.get(ext, "Others")
```

Complexity: O(1) per file.

### C. Duplicate Detection

```
FUNCTION find_duplicates(files):
    size_groups ← group files by size_bytes            # pass 1: free, no I/O

    duplicate_groups ← empty
    FOR EACH (size, candidates) IN size_groups:
        IF count(candidates) < 2: CONTINUE              # unique size ⇒ unique file
        IF size = 0: CONTINUE                           # empty files are not "duplicates"

        hash_groups ← empty
        FOR EACH file IN candidates:                    # pass 2: hash only collisions
            h ← SHA256 of file read in 64 KB chunks
            hash_groups[h].add(file)

        FOR EACH (h, matched) IN hash_groups:
            IF count(matched) > 1:
                duplicate_groups.add(DuplicateGroup(h, size, matched))

    RETURN duplicate_groups sorted by wasted space descending
```

**Why two passes:** hashing every file would mean reading every byte on disk.
Two files of different sizes cannot possibly be identical, and size is already
known from metadata. So the expensive step runs only on files that could
plausibly match.

```
   100 files
       │  group by size (no disk reads)
       ▼
   ┌──────────────┬──────────────┬──────────────┐
   │ size 2 KB: 3 │ size 5 KB: 2 │ size 9 KB: 1 │ ... 
   └──────┬───────┴───────┬──────┴──────────────┘
          │ hash these 5 files only    ✗ skipped (unique size)
          ▼
   compare SHA-256 digests → identical content ⇒ duplicate group
```

**Why SHA-256 and not filename:** two files called `report.pdf` may contain
completely different documents, and the same document may be saved as
`report.pdf`, `report_final.pdf` and `Copy of report.pdf`. Only the content
decides. SHA-256 produces a 256-bit digest; two different files producing the
same digest is computationally infeasible.

### D. Safe File Organisation

```
FUNCTION build_preview(scan_result):           # PLANNING — touches nothing
    claimed ← empty set
    FOR EACH file IN scan_result.files:
        IF file belongs to SmartFile itself:   mark SKIPPED; CONTINUE
        IF file already in its category folder: mark SKIPPED; CONTINUE
        destination ← root / category / filename
        IF destination exists on disk OR destination ∈ claimed:
            destination ← next free name (name_1, name_2, ...)
            mark RENAMED
        ELSE mark READY
        claimed.add(destination)
    RETURN preview

FUNCTION organize(preview):                    # EXECUTION — after confirmation
    FOR EACH move IN preview.ready:
        IF source no longer exists: record failure; CONTINUE
        create destination folder if needed
        IF destination exists now:             # re-check: the disk may have changed
            destination ← next free name
        shutil.move(source, destination)
        log { source, destination, status }
    write log entry to history.json
```

The destination is checked twice — once while planning and again immediately
before the move — because time passes between the preview and the confirmation,
and another program may have created a file in the meantime.

### E. Undo Operation

```
FUNCTION undo(operation):
    IF operation.undone: RETURN "already undone"
    FOR EACH move IN operation.moves:
        IF file not at move.destination:
            record "not found — it was changed outside SmartFile"
            CONTINUE                            # explain, never guess
        target ← move.source
        IF target is occupied again:
            target ← next free name             # never overwrite the newcomer
        shutil.move(move.destination, target)
    mark operation as undone
    remove category folders that are now empty
```

Undo follows the same safety rule as organise: it restores rather than
overwrites, and when it cannot restore a file it reports the reason instead of
risking data loss.

---

## 10. File Organisation Workflow

```
 ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────┐
 │  SCAN   │──►│ CLASSIFY │──►│ PREVIEW  │──►│ USER REVIEWS │
 └─────────┘   └──────────┘   └──────────┘   └──────┬───────┘
                                                    │
                                    ┌───────────────┴───────────┐
                                    │                           │
                              cancel│                    confirm│
                                    ▼                           ▼
                            nothing changed            ┌─────────────────┐
                                                       │ create folders  │
                                                       │ move each file  │
                                                       │ rename conflicts│
                                                       └────────┬────────┘
                                                                ▼
                                                       ┌─────────────────┐
                                                       │ log to history  │
                                                       └────────┬────────┘
                                                                ▼
                                                        UNDO available
```

Example for a `Downloads` folder:

```
BEFORE                        AFTER
Downloads/                    Downloads/
├── report.pdf                ├── Documents/
├── photo.jpg                 │   ├── report.pdf
├── song.mp3                  │   └── report_1.pdf   ← was nested/report.pdf
├── project.py                ├── Images/
└── nested/                   │   └── photo.jpg
    └── report.pdf            ├── Audio/
                              │   └── song.mp3
                              └── Code/
                                  └── project.py
```

Both `report.pdf` files survive. Neither is overwritten.

---

## 11. Storage Analysis

After a scan, SmartFile aggregates metadata with pandas and reports:

- total number of files and total storage consumed
- average file size and largest file
- file count and total storage per category
- percentage share of storage per category
- the ten largest files, with their paths
- the most common file extensions
- storage recoverable if duplicate copies were removed

Visualised as a bar chart (storage per category), a second bar chart (file count
per category), a donut chart (share of total storage) and tables for the largest
files and commonest extensions.

This is a direct application of storage management: the file system reports how
much space each file occupies, and SmartFile turns thousands of those individual
numbers into a picture of where the disk is actually going.

---

## 12. Safety Mechanisms

| Risk | Mechanism |
|---|---|
| Accidental deletion | There is no delete feature. Duplicates are reported only. |
| Overwriting a file | `safe_unique_path()` generates `name_1`, `name_2`, … Destination is re-checked at execution time. |
| Unexpected changes | Full preview with source, destination, status and notes before confirmation. |
| Irreversible mistakes | Every operation logged; undo restores original paths. |
| Undo overwriting new files | If the original path is occupied again, the restored file gets a unique name. |
| Moving the application itself | `is_app_path()` excludes SmartFile's own source files. |
| Damaging system directories | `is_protected_path()` warns on `/System`, `/usr`, `/etc`, home root, etc. |
| Permission denied | Caught per file; the file is skipped with a reason and the scan continues. |
| Broken symbolic links | Detected and skipped rather than followed. |
| Invalid or missing path | Validated before the scan starts, with a clear message. |
| Corrupted history file | Read defensively; a malformed log is treated as empty rather than crashing. |

---

## 13. Testing

Testing uses pytest. Every test runs inside a temporary directory created by
pytest's `tmp_path` fixture, so no real user file is ever read, moved or
modified.

| Test file | Tests | Covers |
|---|---|---|
| `test_scanner.py` | 10 | recursion, metadata, hidden files, empty directories, broken links, unreadable directories, non-directory input |
| `test_classifier.py` | 10 | known extensions, case-insensitivity, unknown extensions, no extension, dotfiles, multiple dots, category disjointness |
| `test_duplicates.py` | 12 | same content/different names, same name/different content, same size/different content, nested duplicates, three-way groups, empty files, chunked hashing of large files |
| `test_organizer.py` | 18 | preview purity, destinations, conflict renaming, no-overwrite guarantee, skipping in-place files, file count preservation, history logging, undo, double-undo prevention, undo with missing or recreated files |
| `test_storage.py` | 9 | totals, averages, empty directories, per-category aggregation, largest files, extension counts, size formatting, chart construction |

**Result: 67 tests, all passing.**

```
$ python3 -m pytest -q
...................................................................  [100%]
67 passed
```

---

## 14. Results

The application was run end to end on the `sample_data/` directory (15 files
across 8 categories, including deliberate duplicates and a deliberate name
conflict).

| Step | Observed result |
|---|---|
| Scan | 15 files found in 2 directories, 3.9 KB total, 0 skipped |
| Classification | Files correctly sorted into 7 categories; `unknownfile.xyz` → Others |
| Duplicate detection | 1 group, 3 identical files (`notes.txt`, `notes_copy.txt`, `nested/meeting_notes.txt`) sharing one SHA-256 hash, 158 B recoverable |
| Preview | 15 files to move, 1 name conflict detected, 0 skipped, 7 destination folders |
| Organize | 15 files moved, 0 failures. Both `report.pdf` files preserved as `report.pdf` and `report_1.pdf` |
| Storage analysis | Charts and tables generated correctly; category totals summed to the scan total |
| History | Operation logged with all 15 source → destination pairs |
| Undo | All 15 files restored to their exact original paths, including `nested/report.pdf`; emptied category folders removed |
| Repeat undo | Correctly refused with "This operation has already been undone." |

Two defects were found during verification and fixed: a Streamlit session-state
conflict when setting a widget value after the widget was created, and duplicate
auto-generated chart identifiers. Both were corrected and re-verified.

---

## 15. Limitations

1. Classification relies on the file extension, not the file's actual content. A misnamed file is misclassified.
2. Duplicate detection requires reading the full contents of every same-size file, so a very large directory takes time.
3. Undo applies only to the most recent operation that has not already been undone.
4. If files are moved or renamed outside SmartFile after being organised, undo reports them as not found rather than searching for them.
5. There is no delete feature, so recovering the space identified by duplicate detection is a manual decision by the user.
6. The history file is local, plain JSON, with no access control.
7. Creation time is not available on all operating systems; on Linux, `st_ctime` is used as a substitute.

---

## 16. Future Enhancements

1. Detect file type from magic numbers (file signatures) as well as extension.
2. Allow the user to define custom categories and rules, saved in a settings file.
3. Support reviewed removal of duplicate copies via the system recycle bin, never a hard delete.
4. Allow undo of any operation in the history, not only the most recent.
5. Add a scheduled or watched-folder mode that organises new downloads automatically.
6. Export the storage report to CSV or PDF.
7. Show disk-level free-space information alongside directory usage.
8. Parallelise hashing across CPU cores for large directories.

---

## 17. Conclusion

SmartFile demonstrates how an application uses the file-handling services an
operating system provides. It traverses the directory hierarchy, reads file
metadata through the `stat()` system call, performs file operations through the
OS, respects the permission boundaries the kernel enforces, and manages storage
by analysing how space is consumed.

Its most important design decision is the separation of planning from execution.
By building a complete preview without touching the disk, and only then acting
on an explicit confirmation, the system gives the user full visibility before
any irreversible change. Combined with the rules that nothing is ever deleted
and nothing is ever overwritten, plus a logged history and a working undo, this
makes a file-management tool that is safe to run on real data.

The project is deliberately small — around 1,400 lines of application code
across eight modules — and is covered by 67 automated tests, all passing.

---

## 18. References

1. Silberschatz, A., Galvin, P. B., and Gagne, G. *Operating System Concepts*, 10th Edition — Chapters 13–15 (File-System Interface, File-System Implementation, File-System Internals).
2. Tanenbaum, A. S., and Bos, H. *Modern Operating Systems*, 4th Edition — Chapter 4 (File Systems).
3. Python Software Foundation. `os` — Miscellaneous operating system interfaces. https://docs.python.org/3/library/os.html
4. Python Software Foundation. `pathlib` — Object-oriented filesystem paths. https://docs.python.org/3/library/pathlib.html
5. Python Software Foundation. `shutil` — High-level file operations. https://docs.python.org/3/library/shutil.html
6. Python Software Foundation. `hashlib` — Secure hashes and message digests. https://docs.python.org/3/library/hashlib.html
7. National Institute of Standards and Technology. *FIPS 180-4: Secure Hash Standard (SHS)*, 2015.
8. Streamlit Inc. Streamlit documentation. https://docs.streamlit.io
