# SmartFile
### OS-Based File Management & Storage Optimization System

**SmartFile** is a Python-based desktop application that simplifies file management through automatic classification, duplicate detection, storage analysis, and safe file organization.

It scans directories recursively, identifies files based on their extensions, detects identical files using SHA-256 hashing, and provides storage insights through an interactive dashboard. Users can preview every proposed operation before execution and undo the most recent organization operation whenever needed.

> An Operating Systems course project demonstrating practical file-system operations, directory management, metadata handling, and storage optimization.

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Project Motivation](#2-project-motivation)
3. [Key Features](#3-key-features)
4. [Operating Systems Concepts](#4-operating-systems-concepts)
5. [System Architecture](#5-system-architecture)
6. [Technology Stack](#6-technology-stack)
7. [Project Structure](#7-project-structure)
8. [Installation](#8-installation)
9. [Running the Application](#9-running-the-application)
10. [Application Workflow](#10-application-workflow)
11. [Screenshots](#11-screenshots)
12. [Testing](#12-testing)
13. [Safety Mechanisms](#13-safety-mechanisms)
14. [Limitations](#14-limitations)
15. [Future Enhancements](#15-future-enhancements)

---

## 1. Problem Statement

Over time, directories such as Downloads and Documents accumulate large numbers of unsorted files, making file management increasingly difficult.

Although operating systems maintain file metadata such as names, sizes, timestamps, permissions, and directory locations, they do not automatically organize files according to their types or identify duplicate files occupying unnecessary storage space.

Manually organizing these files is time-consuming and potentially risky. Accidental overwrites, incorrect file movements, and unintended deletions can result in data loss.

**SmartFile addresses this problem by providing an automated, safe, and user-friendly file management system.**

## 2. Project Motivation

The primary motivation behind SmartFile is to demonstrate how fundamental Operating Systems concepts can solve practical file-management problems.

The project applies operating-system file services to:

- Navigate and traverse directory structures.
- Retrieve and analyze file metadata.
- Perform file and directory operations.
- Identify duplicate files through content hashing.
- Analyze storage consumption and file distribution.
- Implement safe file manipulation with preview and undo functionality.

SmartFile focuses on data safety. It never permanently deletes files or overwrites existing files during organization.

## 3. Key Features

| Feature | Description |
|---|---|
| Recursive Directory Scanning | Scans directories and subdirectories to identify files and retrieve metadata. |
| Automatic File Classification | Categorizes files into 8 predefined categories based on file extensions. |
| Interactive Dashboard | Displays file counts, storage consumption, duplicate counts, and recoverable storage. |
| Organization Preview | Displays proposed file movements, conflicts, and skipped files before execution. |
| Safe File Organization | Moves files into category-based folders and automatically generates unique names when conflicts occur. |
| Duplicate Detection | Identifies byte-identical files using SHA-256 content hashing. |
| Storage Analysis | Provides charts and tables showing storage usage by category, extension, and file size. |
| Operation History | Maintains a JSON-based record of organization operations. |
| Undo Functionality | Restores files to their original locations after the most recent organization operation. |
| Error Handling | Handles permission errors, inaccessible files, and broken symbolic links without terminating the entire scan. |

## 4. Operating Systems Concepts

SmartFile demonstrates several fundamental Operating Systems concepts through practical implementation.

| OS Concept | Implementation |
|---|---|
| File System and Directory Structure | Recursive directory traversal using `os.walk()`. |
| File Metadata Management | Retrieving file size and timestamps using `stat()`. |
| File Operations | Reading, moving, and creating files and directories using Python OS interfaces. |
| Storage Management | Calculating storage consumption and identifying duplicate storage usage. |
| File Permissions and Access Control | Handling read-access restrictions and `PermissionError`. |
| Path Management | Working with absolute paths, relative paths, path resolution, and symbolic links. |
| Safe File Manipulation | Preventing overwrites through unique filename generation and supporting preview and undo. |
| File Organization | Classifying and grouping files into category-based directories. |
| Buffered I/O | Reading files in fixed 64 KB chunks during SHA-256 hashing rather than loading entire files into memory. |

**Note:** SmartFile is an application that utilizes operating-system file services. It does not implement an operating system or its own file system.

## 5. System Architecture

SmartFile follows a modular architecture that separates the user interface from the underlying file-management logic.

### Architecture Overview

```text
                  ┌──────────────────────────┐
                  │       Streamlit UI       │
                  │        app/main.py       │
                  │   Presentation Layer     │
                  └────────────┬─────────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │         Core Modules           │
              ├──────────┬───────────┬─────────┤
              │ Scanner  │Classifier │Organizer│
              ├──────────┼───────────┼─────────┤
              │Duplicate │ Storage   │History  │
              │Detector  │ Analyzer  │Manager │
              └──────────┴───────────┴─────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │       Supporting Modules       │
              │                                │
              │  models.py  │  utils.py         │
              │  history.py │                  │
              └────────────────────────────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │       Operating System         │
              │                                │
              │  os │ pathlib │ shutil         │
              │  hashlib │ json                │
              └────────────────────────────────┘
```

### Architecture Components

- **Presentation Layer:** Streamlit provides the interactive interface and displays scanning results, analytics, and operation history.
- **Scanner Module:** Traverses directories and retrieves file metadata.
- **Classifier Module:** Determines file categories based on extensions.
- **Organizer Module:** Generates organization previews and safely moves files.
- **Duplicate Detector:** Calculates SHA-256 hashes and groups identical files.
- **Storage Analyzer:** Aggregates storage statistics and generates analytical results.
- **History Manager:** Records file movements and supports undo operations.
- **Supporting Modules:** Maintain shared data structures, utilities, and reusable functionality.

The user interface is separated from file-system operations, allowing individual modules to be tested independently.

## 6. Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.9+ | Core application development and file-system operations |
| Streamlit | Interactive desktop-style user interface |
| Pandas | Data aggregation and tabular analysis |
| Plotly | Interactive charts and visualizations |
| Hashlib | SHA-256 content hashing for duplicate detection |
| OS and Pathlib | Directory traversal and file metadata management |
| Shutil | File movement and directory operations |
| JSON | Persistent operation history |
| Pytest | Automated unit and functional testing |

**Project Characteristics**

- No external database.
- No cloud infrastructure.
- No machine learning models.
- No separate backend server.
- Uses Python standard-library modules for core file operations.

## 7. Project Structure

```text
SmartFile/
│
├── app/
│   └── main.py
│
├── core/
│   ├── scanner.py
│   ├── classifier.py
│   ├── organizer.py
│   ├── duplicate_detector.py
│   ├── storage_analyzer.py
│   ├── history.py
│   ├── models.py
│   └── utils.py
│
├── sample_data/
│   └── Demo files for testing
│
├── tests/
│   └── Automated test cases
│
├── docs/
│   └── Application screenshots
│
├── requirements.txt
├── run.sh
└── README.md
```

*The structure above represents the logical project organization; adjust filenames and directories to match the actual repository.*

## 8. Installation

### Prerequisites

- Python 3.9 or above.
- pip package manager.
- Git (optional, for cloning the repository).

### Step 1: Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd SmartFile
```

### Step 2: Create a Virtual Environment

```bash
python3 -m venv venv
```

### Step 3: Activate the Environment

**macOS / Linux**

```bash
source venv/bin/activate
```

**Windows**

```bash
venv\Scripts\activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

## 9. Running the Application

Start SmartFile using the provided execution script:

```bash
./run.sh
```

Alternatively, run Streamlit directly:

```bash
python3 -m streamlit run app/main.py
```

Once started, open the application in your browser:

**http://localhost:8501**

## 10. Application Workflow

SmartFile provides an interactive workflow for scanning, analyzing, and organizing files.

### Step 1: Directory Scanning

- Enter the directory path in the sidebar.
- Alternatively, select the sample data directory.
- Click **SCAN** to begin recursive scanning.
- The application retrieves file metadata and identifies file categories.

### Step 2: Dashboard

View an overview of the scanned directory, including:

- Total files scanned.
- Total storage consumed.
- Number of duplicate files.
- Estimated recoverable storage.

### Step 3: File Scanner

Browse scanned files with details such as:

- File name and path.
- File category.
- File size.
- Last modified timestamp.

### Step 4: File Organization

- Navigate to the Organize section.
- Click **PREVIEW** to generate the proposed file movements.
- Review conflicts, skipped files, and destination paths.
- Confirm the operation using the confirmation checkbox.
- Click **ORGANIZE** to execute the operation.

### Step 5: Duplicate Detection

- View groups of duplicate files.
- Expand individual groups to inspect their file paths.
- Compare their SHA-256 hashes to verify identical content.

### Step 6: Storage Analysis

Explore storage consumption through:

- Storage usage by category.
- Storage distribution by file extension.
- File count analysis.
- Largest files in the scanned directory.

### Step 7: Operation History and Undo

- Review previous organization operations.
- Inspect recorded file movements.
- Select **Undo Last Operation** to restore files to their original locations.

**Recommendation:** Start with the provided `sample_data/` directory to understand the application's functionality before scanning personal directories.

## 11. Screenshots

Application screenshots can be added to the `docs/` directory to demonstrate the major features.

| Section | Screenshot |
|---|---|
| Dashboard | `docs/screenshot_dashboard.png` |
| Organization Preview | `docs/screenshot_preview.png` |
| Duplicate Detection | `docs/screenshot_duplicates.png` |
| Storage Analysis | `docs/screenshot_storage.png` |
| Operation History | `docs/screenshot_history.png` |

To display screenshots on GitHub, add the following after placing the corresponding image files in the repository:

```markdown
### Dashboard
![SmartFile Dashboard](docs/screenshot_dashboard.png)

### Organization Preview
![Organization Preview](docs/screenshot_preview.png)

### Duplicate Detection
![Duplicate Detection](docs/screenshot_duplicates.png)

### Storage Analysis
![Storage Analysis](docs/screenshot_storage.png)

### Operation History
![Operation History](docs/screenshot_history.png)
```

## 12. Testing

SmartFile uses **pytest** for automated testing.

Run the complete test suite:

```bash
python3 -m pytest -v
```

### Test Coverage

The project includes 67 automated tests covering:

- Directory scanning.
- File classification.
- Duplicate detection.
- Organization preview generation.
- Destination conflict handling.
- File movement operations.
- Undo functionality.
- Storage calculations.

All tests execute inside pytest temporary directories, ensuring that actual user files are not modified during testing.

## 13. Safety Mechanisms

Data safety is a key design consideration in SmartFile.

| Safety Mechanism | Purpose |
|---|---|
| Preview Before Execution | Allows users to review proposed changes before applying them. |
| No Permanent Deletion | The application does not delete files during normal operations. |
| No File Overwriting | Existing destination files are protected through unique filename generation. |
| Operation Logging | Records file movements for future reference and recovery. |
| Undo Support | Restores files to their original paths when possible. |
| Error Handling | Skips inaccessible files without interrupting the complete scanning process. |
| Temporary Directory Testing | Prevents automated tests from modifying real user data. |

## 14. Limitations

- File classification relies on extensions. A file renamed with an incorrect extension may be categorized incorrectly.
- Duplicate detection identifies identical files but does not automatically remove them.
- Undo functionality supports only the most recent organization operation that has not already been undone.
- If a file is moved or renamed externally after organization, undo reports it as missing instead of guessing its new location.
- Hashing large directories can take considerable time because file contents must be read to calculate hashes.
- Files manually moved after organization are not automatically tracked.
- The application has been tested on macOS and Linux. On Windows, `st_ctime` represents creation time rather than metadata-change time.

## 15. Future Enhancements

Potential improvements that could extend SmartFile include:

1. **Content-Based File Identification:** Use file signatures and magic numbers instead of relying exclusively on extensions.
2. **Custom Classification Rules:** Allow users to configure and save their own file categories.
3. **Safe Duplicate Removal:** Introduce user-confirmed duplicate deletion with a recycle-bin recovery mechanism.
4. **Advanced Undo System:** Support undoing previously completed operations instead of only the latest operation.
5. **Scheduled Scanning:** Enable periodic background scanning of selected directories.
6. **Report Export:** Allow storage analysis reports to be exported as CSV or PDF.

---

## Conclusion

SmartFile demonstrates the practical application of Operating Systems concepts in developing a reliable file-management solution.

By combining directory traversal, file metadata retrieval, file operations, hashing algorithms, storage analysis, and safe file manipulation, the project provides an organized approach to managing digital files.

The modular architecture, interactive interface, and automated testing make SmartFile a practical demonstration of how operating-system services can be utilized to solve real-world problems.

---

**Developed as an Operating Systems Course Project.**
