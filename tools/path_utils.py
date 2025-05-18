from pathlib import Path, PureWindowsPath


def to_posix_path(path: Path | str) -> str:
    """Convert a ``Path`` or path-like object to POSIX style.

    This function accepts both strings and ``Path`` objects, normalizing them
    to a POSIX-style path representation.
    """
    return PureWindowsPath(str(path)).as_posix()


def convert_to_posix_path(path_val: str) -> str:
    """Return ``path_val`` normalized to POSIX style.

    This wrapper is kept for backward compatibility and simply calls
    :func:`to_posix_path`.
    """

    return to_posix_path(path_val)


def normalize_path(path: Path | str) -> str:
    """Normalize a ``Path`` or path-like object to POSIX style.

    This wrapper is kept for backward compatibility and simply calls
    :func:`to_posix_path`.
    """

    return to_posix_path(path)
