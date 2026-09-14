#!/usr/bin/env python3
"""
corpus_files.py -- the ONE way this codebase enumerates corpus paper files.

WHY THIS EXISTS (2026-08-29): `canebrake_corpus/` is a symlink to
<ARCHIVE_VOLUME>/canebrake_corpus (RETIRED 2026-09-01 -- the
symlink now points at local APFS; the rule below still matters for S3
restores and any non-native volume). That volume was not a native
macOS filesystem, so macOS writes an AppleDouble sidecar ("._2001.07676.json")
next to EVERY file written there to carry extended attributes. There are
285,231 of them under the corpus right now, and they are not historical junk
to be swept once: they are recreated on every corpus write. A 04c run this
morning produced a fresh set within seconds.

They break two specific, recurring ways:

  1. `glob("*.json")` matches them -- "._x.json" really does end in .json --
     and they are BINARY, so json.loads(f.read_text()) dies with
     UnicodeDecodeError mid-run. Hit live in 06_process_new_papers.py's
     residue scan on 2026-08-29.
  2. The usual sidecar guard in this repo is name.startswith("_"), which
     does NOT catch them -- the dot comes first. Code that looks correctly
     defended often isn't.

Deleting them is a treadmill (they come back on the next write) and on a
non-native volume it can strip real xattrs. Filtering at read time is the
durable fix, so this module is the one place that knows the rule.

Usage:
    import corpus_files
    for path in corpus_files.iter_paper_files(some_dir):
        paper = corpus_files.load_paper(path)   # None if unreadable
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator


def is_appledouble(path: str | Path) -> bool:
    """macOS AppleDouble resource-fork sidecar ("._name.json"). Binary,
    never a paper. Not caught by a startswith("_") test."""
    return Path(path).name.startswith("._")


def is_sidecar(path: str | Path) -> bool:
    """Anything in a corpus directory that is not a paper: this pipeline's
    own metadata files (_needs_review.json, _title_match_cache.json, ...),
    dotfiles, and AppleDouble junk."""
    name = Path(path).name
    return name.startswith("_") or name.startswith(".")


def iter_paper_files(directory: str | Path, pattern: str = "*.json") -> Iterator[Path]:
    """Every real paper file in `directory`, sidecars and AppleDouble
    junk excluded. Sorted, so runs over the same directory are ordered
    the same way twice."""
    for path in sorted(Path(directory).glob(pattern)):
        if path.is_file() and not is_sidecar(path):
            yield path


def load_paper(path: str | Path) -> dict | None:
    """Read one paper. Returns None rather than raising when the file is
    unreadable or is not a JSON object -- callers sweeping a corpus
    directory should skip a bad file, not abort the sweep. A caller that
    genuinely needs the failure to be loud should read it itself."""
    try:
        data = json.loads(Path(path).read_text())
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None
