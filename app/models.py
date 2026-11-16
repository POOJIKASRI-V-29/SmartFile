"""Plain data structures used across SmartFile modules.

Keeping these as simple dataclasses (instead of a database) keeps the project
small and makes the data easy to convert into a pandas DataFrame for analysis.
"""

from dataclasses import dataclass, asdict, field
from typing import Optional


@dataclass
class FileRecord:
    """Metadata collected for a single file during a directory scan.

    These fields mirror the metadata an operating system keeps for a file in
    its file-system tables (inode / MFT entry): name, size and timestamps.
    """

    name: str
    path: str               # absolute path
    relative_path: str      # path relative to the scanned root
    extension: str          # lowercase, including the dot (".pdf"); "" if none
    category: str           # Documents, Images, ... , Others
    size_bytes: int
    size_human: str
    modified_time: float    # epoch seconds (st_mtime)
    created_time: float     # epoch seconds (st_birthtime / st_ctime fallback)
    parent_dir: str

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class ScanResult:
    """Everything one scan produced, including problems we skipped over."""

    root: str
    files: list = field(default_factory=list)          # list[FileRecord]
    skipped: list = field(default_factory=list)        # list[dict] path + reason
    directories_scanned: int = 0
    empty_directories: list = field(default_factory=list)

    @property
    def total_files(self) -> int:
        return len(self.files)

    @property
    def total_bytes(self) -> int:
        return sum(f.size_bytes for f in self.files)


@dataclass
class PlannedMove:
    """One proposed source -> destination move, produced by the preview step."""

    source: str
    destination: str
    category: str
    size_bytes: int
    status: str             # "ready" | "renamed" | "skipped"
    note: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class OrganizePreview:
    """The full plan shown to the user before any file is touched."""

    root: str
    moves: list = field(default_factory=list)          # list[PlannedMove]
    warnings: list = field(default_factory=list)       # list[str]

    @property
    def ready(self) -> list:
        return [m for m in self.moves if m.status in ("ready", "renamed")]

    @property
    def skipped(self) -> list:
        return [m for m in self.moves if m.status == "skipped"]

    @property
    def conflicts(self) -> list:
        return [m for m in self.moves if m.status == "renamed"]

    def counts_by_category(self) -> dict:
        counts: dict = {}
        for move in self.ready:
            counts[move.category] = counts.get(move.category, 0) + 1
        return counts


@dataclass
class DuplicateGroup:
    """A set of files whose SHA-256 content hashes are identical."""

    file_hash: str
    size_bytes: int
    files: list = field(default_factory=list)          # list[FileRecord]

    @property
    def count(self) -> int:
        return len(self.files)

    @property
    def wasted_bytes(self) -> int:
        """Space recoverable if only one copy of the content were kept."""
        return self.size_bytes * (self.count - 1)


@dataclass
class OperationResult:
    """Outcome of an organize or undo run."""

    moved: int = 0
    failed: int = 0
    skipped: int = 0
    errors: list = field(default_factory=list)         # list[str]
    operation_id: Optional[str] = None
