"""File-format detection. Extension-based for now - magic-byte sniffing
(for mislabeled/extensionless files) is a reasonable later addition, not
needed for the first slice."""

from __future__ import annotations

from pathlib import Path

_EXTENSION_MAP: dict[str, str] = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".xlsx": "xlsx",
    ".eml": "email",
}


class UnsupportedFormatError(ValueError):
    """Raised when a file's format can't be determined or isn't supported."""


def detect_format(path: Path) -> str:
    suffix = path.suffix.lower()
    try:
        return _EXTENSION_MAP[suffix]
    except KeyError:
        raise UnsupportedFormatError(
            f"Can't determine format for {path.name!r} (unrecognized extension {suffix!r})"
        ) from None
