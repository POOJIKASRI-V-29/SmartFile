"""Extension-based file classification.

The mapping below is intentionally simple and easy to extend: add the extension
to the right list and the whole application (scanner, organizer, analytics)
picks it up automatically.
"""

from __future__ import annotations

from pathlib import Path

CATEGORY_EXTENSIONS: dict[str, list[str]] = {
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".csv", ".xlsx", ".xls",
                  ".ppt", ".pptx", ".odt", ".rtf", ".md"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".bmp",
               ".tiff", ".ico", ".heic"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv", ".m4v"],
    "Audio": [".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso"],
    "Code": [".py", ".java", ".cpp", ".c", ".h", ".js", ".ts", ".jsx", ".tsx",
             ".html", ".css", ".dart", ".sql", ".go", ".rb", ".php", ".sh",
             ".json", ".xml", ".yaml", ".yml", ".rs", ".kt", ".swift"],
    "Executables": [".exe", ".dmg", ".pkg", ".deb", ".appimage", ".msi",
                    ".app", ".rpm", ".bin"],
}

DEFAULT_CATEGORY = "Others"

# Reverse lookup built once: ".pdf" -> "Documents". Dictionary lookup keeps
# classification O(1) per file instead of scanning every category list.
_EXTENSION_TO_CATEGORY: dict[str, str] = {
    ext: category
    for category, extensions in CATEGORY_EXTENSIONS.items()
    for ext in extensions
}

# Order used for display so charts and tables stay consistent.
CATEGORY_ORDER = list(CATEGORY_EXTENSIONS.keys()) + [DEFAULT_CATEGORY]


def get_extension(filename: str | Path) -> str:
    """Return the lowercase extension including the dot, or '' if there is none.

    Dotfiles such as '.gitignore' are treated as having no extension, which is
    how the file system itself treats them (name, not type).
    """
    name = Path(filename).name
    if name.startswith(".") and name.count(".") == 1:
        return ""
    return Path(name).suffix.lower()


def classify(filename: str | Path) -> str:
    """Classify a file by its extension. Unknown extensions become 'Others'."""
    return _EXTENSION_TO_CATEGORY.get(get_extension(filename), DEFAULT_CATEGORY)


def classify_extension(extension: str) -> str:
    """Classify a bare extension string such as '.PNG' or 'png'."""
    ext = extension.lower().strip()
    if ext and not ext.startswith("."):
        ext = "." + ext
    return _EXTENSION_TO_CATEGORY.get(ext, DEFAULT_CATEGORY)


def all_categories() -> list[str]:
    """Every category name, in display order."""
    return list(CATEGORY_ORDER)
