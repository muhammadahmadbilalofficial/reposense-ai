"""
analyzer.py
===========
RepoSense AI — repository analysis module.

Public API
----------
scan_directory(root: str | Path) -> list[Path]
    Recursively collect every file under *root*, skipping ignored directories.

language_breakdown(files: list[Path]) -> dict
    Return a structured dict AND a pandas DataFrame describing language
    distribution (file count + total lines).

check_onboarding_files(root: str | Path) -> dict
    Detect the presence/absence of essential onboarding artefacts.

security_quality_scan(files: list[Path]) -> dict
    Run lightweight static checks on Python files and return a structured
    report dict + a pandas DataFrame of individual findings.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Directories that are never descended into.
IGNORED_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "venv",
        ".venv",
        "env",
        ".env",
        "node_modules",
        ".tox",
        "dist",
        "build",
        ".eggs",
        "*.egg-info",
        ".idea",
        ".vscode",
    }
)

#: Maps a human-readable language label to the file extensions it owns.
LANGUAGE_EXTENSIONS: dict[str, tuple[str, ...]] = {
    "Python":       (".py",),
    "JavaScript":   (".js", ".mjs", ".cjs"),
    "TypeScript":   (".ts", ".tsx"),
    "HTML":         (".html", ".htm"),
    "CSS":          (".css", ".scss", ".sass", ".less"),
    "Java":         (".java",),
    "C/C++":        (".c", ".cpp", ".cc", ".cxx", ".h", ".hpp"),
    "C#":           (".cs",),
    "Go":           (".go",),
    "Rust":         (".rs",),
    "Ruby":         (".rb",),
    "PHP":          (".php",),
    "Swift":        (".swift",),
    "Kotlin":       (".kt", ".kts"),
    "Shell":        (".sh", ".bash", ".zsh", ".fish"),
    "YAML":         (".yml", ".yaml"),
    "JSON":         (".json",),
    "TOML":         (".toml",),
    "Markdown":     (".md", ".markdown"),
    "SQL":          (".sql",),
    "Dockerfile":   (),   # matched by filename — see _classify_file()
    "Other":        (),   # catch-all
}

#: Onboarding files to look for — maps a canonical label to candidate
#: filenames / relative-path fragments (all lowercase).
ONBOARDING_FILES: dict[str, tuple[str, ...]] = {
    "README":           ("readme.md", "readme.rst", "readme.txt", "readme"),
    "requirements.txt": ("requirements.txt",),
    "Pipfile":          ("pipfile",),
    "pyproject.toml":   ("pyproject.toml",),
    "setup.py":         ("setup.py",),
    "setup.cfg":        ("setup.cfg",),
    "Dockerfile":       ("dockerfile",),
    "docker-compose":   ("docker-compose.yml", "docker-compose.yaml"),
    ".env.example":     (".env.example", ".env.sample"),
    "LICENCE":          (
        "licence", "license",
        "licence.md", "license.md",
        "licence.txt", "license.txt",
    ),
    "CONTRIBUTING":     ("contributing.md", "contributing.rst", "contributing"),
    "CHANGELOG":        (
        "changelog.md", "changelog.rst",
        "changelog.txt", "changelog",
    ),
    ".gitignore":       (".gitignore",),
    "CI config":        (
        ".travis.yml",
        "circle.yml",
        ".circleci/config.yml",
        "jenkinsfile",
        ".github/workflows",
        "azure-pipelines.yml",
        "bitbucket-pipelines.yml",
    ),
}


# ---------------------------------------------------------------------------
# Security / quality check patterns  (Python-only)
# ---------------------------------------------------------------------------

class _CheckPattern(NamedTuple):
    category: str        # "security" | "quality"
    label:    str        # short human-readable tag
    pattern:  re.Pattern[str]
    severity: str        # "high" | "medium" | "low" | "info"


_CHECKS: list[_CheckPattern] = [
    # ── Security ────────────────────────────────────────────────────────────
    _CheckPattern(
        "security", "Hardcoded secret (assignment)",
        re.compile(
            r'(?i)(password|passwd|secret|api_key|apikey|token|auth_token'
            r'|access_key|private_key)\s*=\s*["\'][^"\']{4,}["\']'
        ),
        "high",
    ),
    _CheckPattern(
        "security", "Hardcoded secret (dict / kwarg)",
        re.compile(
            r'(?i)["\']?(password|passwd|secret|api_key|apikey|token'
            r'|auth_token|access_key)["\']?\s*:\s*["\'][^"\']{4,}["\']'
        ),
        "high",
    ),
    _CheckPattern(
        "security", "eval() usage",
        re.compile(r'\beval\s*\('),
        "high",
    ),
    _CheckPattern(
        "security", "exec() usage",
        re.compile(r'\bexec\s*\('),
        "medium",
    ),
    _CheckPattern(
        "security", "Shell injection risk (os.system / shell=True)",
        re.compile(
            r'(os\.system\s*\('
            r'|subprocess\.[a-z_]+\([^)]*shell\s*=\s*True)'
        ),
        "high",
    ),
    _CheckPattern(
        "security", "SQL string-formatting (potential injection)",
        re.compile(
            r'(?i)(execute|cursor\.execute)\s*\(\s*[fF]?["\'].*%[sd]'
        ),
        "high",
    ),
    _CheckPattern(
        "security", "Insecure deserialisation (pickle)",
        re.compile(r'\bpickle\.loads?\s*\('),
        "medium",
    ),
    _CheckPattern(
        "security", "Hardcoded IP address",
        re.compile(r'["\'](\d{1,3}\.){3}\d{1,3}["\']'),
        "low",
    ),
    _CheckPattern(
        "security", "Insecure hash algorithm (MD5 / SHA-1)",
        re.compile(r'hashlib\.(md5|sha1)\s*\('),
        "medium",
    ),
    # ── Quality ─────────────────────────────────────────────────────────────
    _CheckPattern(
        "quality", "TODO comment",
        re.compile(r'#.*\bTODO\b', re.IGNORECASE),
        "info",
    ),
    _CheckPattern(
        "quality", "FIXME comment",
        re.compile(r'#.*\bFIXME\b', re.IGNORECASE),
        "info",
    ),
    _CheckPattern(
        "quality", "HACK comment",
        re.compile(r'#.*\bHACK\b', re.IGNORECASE),
        "info",
    ),
    _CheckPattern(
        "quality", "Bare except block",
        re.compile(r'^\s*except\s*:'),
        "medium",
    ),
    _CheckPattern(
        "quality", "Broad Exception catch",
        re.compile(r'except\s+Exception\s*:'),
        "low",
    ),
    _CheckPattern(
        "quality", "print() statement (debug artifact)",
        re.compile(r'\bprint\s*\('),
        "info",
    ),
    _CheckPattern(
        "quality", "Mutable default argument",
        re.compile(r'def\s+\w+\s*\([^)]*=\s*(\[\s*\]|\{\s*\})'),
        "medium",
    ),
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_ignored(path: Path) -> bool:
    """Return ``True`` if *path* is a directory whose name is in :data:`IGNORED_DIRS`."""
    return path.is_dir() and path.name in IGNORED_DIRS


def _classify_file(file: Path) -> str:
    """Return the language label for *file*."""
    name_lower = file.name.lower()

    # Dockerfile matched by name, not extension
    if name_lower == "dockerfile" or name_lower.startswith("dockerfile."):
        return "Dockerfile"

    suffix = file.suffix.lower()
    for language, extensions in LANGUAGE_EXTENSIONS.items():
        if suffix in extensions:
            return language

    return "Other"


def _count_lines(file: Path) -> int:
    """Return the number of lines in *file*; ``0`` on any read error."""
    try:
        return sum(1 for _ in file.open("rb"))
    except OSError:
        return 0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan_directory(root: str | Path) -> list[Path]:
    """
    Recursively collect every *file* under *root*, skipping :data:`IGNORED_DIRS`.

    Parameters
    ----------
    root:
        The repository root directory.

    Returns
    -------
    list[Path]
        Sorted list of absolute :class:`~pathlib.Path` objects for every
        discovered file.

    Raises
    ------
    NotADirectoryError
        If *root* does not point to an existing directory.
    """
    root = Path(root).resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    collected: list[Path] = []

    def _recurse(current: Path) -> None:
        try:
            entries = sorted(current.iterdir())
        except PermissionError:
            return

        for entry in entries:
            if _is_ignored(entry):
                continue
            if entry.is_symlink():
                continue
            if entry.is_dir():
                _recurse(entry)
            elif entry.is_file():
                collected.append(entry)

    _recurse(root)
    return collected


# ---------------------------------------------------------------------------

def language_breakdown(files: list[Path]) -> dict:
    """
    Calculate language distribution across *files*.

    Parameters
    ----------
    files:
        A list of :class:`~pathlib.Path` objects as returned by
        :func:`scan_directory`.

    Returns
    -------
    dict
        ``"summary"``  — :class:`pandas.DataFrame` with columns
        ``language``, ``file_count``, ``total_lines``, ``pct_files``,
        ``pct_lines``.

        ``"totals"``  — ``{"total_files": int, "total_lines": int}``

        ``"per_language"``  — dict keyed by language label, each value
        ``{"file_count": int, "total_lines": int, "files": list[str]}``.
    """
    per_language: dict[str, dict] = {}

    for file in files:
        lang = _classify_file(file)
        lines = _count_lines(file)

        if lang not in per_language:
            per_language[lang] = {"file_count": 0, "total_lines": 0, "files": []}

        per_language[lang]["file_count"] += 1
        per_language[lang]["total_lines"] += lines
        per_language[lang]["files"].append(str(file))

    total_files = sum(v["file_count"] for v in per_language.values())
    total_lines = sum(v["total_lines"] for v in per_language.values())

    rows = []
    for lang, data in sorted(
        per_language.items(), key=lambda kv: kv[1]["file_count"], reverse=True
    ):
        rows.append(
            {
                "language":    lang,
                "file_count":  data["file_count"],
                "total_lines": data["total_lines"],
                "pct_files":   round(data["file_count"] / total_files * 100, 2)
                               if total_files else 0.0,
                "pct_lines":   round(data["total_lines"] / total_lines * 100, 2)
                               if total_lines else 0.0,
            }
        )

    summary_df = pd.DataFrame(
        rows,
        columns=["language", "file_count", "total_lines", "pct_files", "pct_lines"],
    )

    return {
        "summary":      summary_df,
        "totals":       {"total_files": total_files, "total_lines": total_lines},
        "per_language": per_language,
    }


# ---------------------------------------------------------------------------

def check_onboarding_files(root: str | Path) -> dict:
    """
    Check for the presence of common onboarding and project-health files.

    Parameters
    ----------
    root:
        The repository root directory.

    Returns
    -------
    dict
        ``"present"``  — list of label strings that were found.

        ``"missing"``  — list of label strings that were *not* found.

        ``"details"``  — dict mapping every label to
        ``{"found": bool, "path": str | None}``.

        ``"score"``  — ``{"found": int, "total": int, "pct": float}``.
    """
    root = Path(root).resolve()

    # Build a flat set of all lowercased relative-path fragments that exist
    existing_lower: set[str] = set()
    try:
        for entry in root.rglob("*"):
            existing_lower.add(entry.name.lower())
            try:
                rel = str(entry.relative_to(root)).lower().replace("\\", "/")
                existing_lower.add(rel)
            except ValueError:
                pass
    except PermissionError:
        pass

    details: dict[str, dict] = {}

    for label, candidates in ONBOARDING_FILES.items():
        found_path: str | None = None

        for candidate in candidates:
            c = candidate.lower()
            if any(
                existing == c or existing.endswith("/" + c)
                for existing in existing_lower
            ):
                # Retrieve the actual (non-lowered) relative path
                for entry in root.rglob("*"):
                    try:
                        rel = str(entry.relative_to(root)).lower().replace("\\", "/")
                    except ValueError:
                        continue
                    if rel == c or rel.endswith("/" + c):
                        found_path = str(entry.relative_to(root))
                        break
                if found_path:
                    break

        details[label] = {"found": found_path is not None, "path": found_path}

    present = [lbl for lbl, v in details.items() if v["found"]]
    missing = [lbl for lbl, v in details.items() if not v["found"]]
    total   = len(details)

    return {
        "present": present,
        "missing": missing,
        "details": details,
        "score":   {
            "found": len(present),
            "total": total,
            "pct":   round(len(present) / total * 100, 1) if total else 0.0,
        },
    }


# ---------------------------------------------------------------------------

def security_quality_scan(files: list[Path]) -> dict:
    """
    Run lightweight static checks on every Python file in *files*.

    Checks performed
    ----------------
    * Hardcoded secrets / credentials (high)
    * ``eval()`` / ``exec()`` usage (high / medium)
    * Shell-injection risks — ``os.system``, ``shell=True`` (high)
    * SQL string-formatting injection (high)
    * Insecure deserialisation — ``pickle.load[s]`` (medium)
    * Insecure hash algorithms — MD5 / SHA-1 (medium)
    * Bare ``except:`` blocks (medium)
    * Mutable default arguments (medium)
    * Broad ``Exception`` catches (low)
    * TODO / FIXME / HACK comments (info)
    * ``print()`` debug statements (info)

    Parameters
    ----------
    files:
        A list of :class:`~pathlib.Path` objects.
        Non-Python files are silently skipped.

    Returns
    -------
    dict
        ``"findings"``  — :class:`pandas.DataFrame` with columns
        ``file``, ``line``, ``category``, ``label``, ``severity``,
        ``snippet``.

        ``"summary"``  — :class:`pandas.DataFrame` with columns
        ``label``, ``category``, ``severity``, ``count``
        (one row per check type that triggered at least once).

        ``"stats"``  — ``{"files_scanned": int, "total_findings": int,
        "high": int, "medium": int, "low": int, "info": int}``.

        ``"by_file"``  — dict mapping each scanned file path (str)
        to its total finding count.
    """
    python_files = [f for f in files if f.suffix == ".py"]

    rows: list[dict] = []
    by_file: dict[str, int] = {}

    for file in python_files:
        try:
            source_lines = file.read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()
        except OSError:
            continue

        file_str = str(file)
        by_file[file_str] = 0

        for check in _CHECKS:
            for lineno, line in enumerate(source_lines, start=1):
                if check.pattern.search(line):
                    rows.append(
                        {
                            "file":     file_str,
                            "line":     lineno,
                            "category": check.category,
                            "label":    check.label,
                            "severity": check.severity,
                            "snippet":  line.strip()[:120],
                        }
                    )
                    by_file[file_str] += 1

    findings_df = pd.DataFrame(
        rows,
        columns=["file", "line", "category", "label", "severity", "snippet"],
    )

    # ── Per-check-type summary ───────────────────────────────────────────────
    if not findings_df.empty:
        summary_df = (
            findings_df
            .groupby(["label", "category", "severity"], sort=False)
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
            .reset_index(drop=True)
        )
    else:
        summary_df = pd.DataFrame(
            columns=["label", "category", "severity", "count"]
        )

    # ── Severity totals ──────────────────────────────────────────────────────
    sev_counts: dict[str, int] = (
        findings_df["severity"].value_counts().to_dict()
        if not findings_df.empty
        else {}
    )

    stats: dict = {
        "files_scanned":  len(python_files),
        "total_findings": len(findings_df),
        "high":           sev_counts.get("high",   0),
        "medium":         sev_counts.get("medium", 0),
        "low":            sev_counts.get("low",    0),
        "info":           sev_counts.get("info",   0),
    }

    return {
        "findings": findings_df,
        "summary":  summary_df,
        "stats":    stats,
        "by_file":  by_file,
    }




