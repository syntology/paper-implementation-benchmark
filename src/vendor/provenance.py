#!/usr/bin/env python3
"""
provenance.py -- STANDARDS.md R1 and R3, executable. Stdlib only.

R1: every derived FILE records what it was derived from. Graph writes
already have WriteLedger (<INTERNAL>) and
embeddings carry embedding_source_sha; this module is the same
discipline for every script that writes a JSON/JSONL/report/figure:

    import provenance
    provenance.write_json(out_path, payload, inputs=[in1, in2], params=vars(args))

embeds a `_provenance` block (generator script + git commit, each
input's path + sha256 + mtime, params, timestamp) and writes
atomically. For non-JSON outputs, `write_sidecar(path, inputs=...)`
puts the same block in `<path>.prov.json`.

    python3 provenance.py verify <file...>

recomputes every input hash and reports drift -- the mechanical answer
to "figures are outdated" and "a vector silently stops matching its
source". Exit 0 clean, 1 missing provenance, 2 inputs drifted.

R3: filters account for what they exclude.

    ledger = provenance.ExclusionLedger()
    ledger.process()               # kept one record
    ledger.exclude("no_text")      # dropped one, with a named reason
    ledger.enforce(accept=("no_text",))   # SystemExit(3) on any
                                          # exclusion reason NOT accepted

A source that did not ANSWER is not an exclusion -- it is an open
question, and it gets its own channel so the two can never merge:

    except SourceUnavailable as e:        # source_availability.py
        ledger.unanswered("s2_did_not_answer", note=str(e))

`summary()` then prints asked= and answered= separately, and `enforce()`
exits 4 (unresolved partials), which no accept= can clear. See the
ExclusionLedger docstring for the five defects that bought this rule.

Pass the ledger to write_json/write_sidecar/stamp and the exclusion
counts become part of the derivation record itself -- what was left
OUT of an artifact is provenance just as much as what went in.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "syntology-provenance/1"
PROV_KEY = "_provenance"


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _utc(ts: float | None = None) -> str:
    dt = datetime.fromtimestamp(ts, timezone.utc) if ts else datetime.now(timezone.utc)
    return dt.isoformat(timespec="seconds")


_GIT_IDENTITY_CACHE: dict = {}


def _git_identity(script_dir: Path) -> dict:
    # Recorded, not required: a script run outside any git checkout still
    # gets a stamp, it just says so instead of carrying a commit.
    # Cached per directory: per-record stampers (one stamp per output file
    # in a 10k-file corpus pass) must not fork git twice per record.
    cached = _GIT_IDENTITY_CACHE.get(script_dir)
    if cached is not None:
        return cached
    try:
        commit = subprocess.run(["git", "-C", str(script_dir), "rev-parse", "HEAD"],
                                capture_output=True, text=True, timeout=10)
        if commit.returncode != 0:
            out = {"git_commit": None, "git_dirty": None, "note": "not a git checkout"}
            _GIT_IDENTITY_CACHE[script_dir] = out
            return out
        dirty = subprocess.run(["git", "-C", str(script_dir), "status", "--porcelain"],
                               capture_output=True, text=True, timeout=10)
        out = {"git_commit": commit.stdout.strip(),
               "git_dirty": bool(dirty.stdout.strip())}
    except Exception as ex:  # git missing/hung must never break the pipeline write
        out = {"git_commit": None, "git_dirty": None, "note": f"git unavailable: {ex}"}
    _GIT_IDENTITY_CACHE[script_dir] = out
    return out


class ExclusionLedger:
    """R3 accounting: every skip has a named reason, and reasons must be
    explicitly accepted or the run fails. `examined` is derived, never
    self-reported, so processed + excluded + unanswered always reconciles.

    TWO CHANNELS, and they do not merge (2026-09-09, SILENT_ABSENCE_BRIEF.md):

      exclude()    we asked, we got an answer, and we decided to drop it.
                   Clearing it is a judgement the caller makes once, by
                   naming the reason in accept=().

      unanswered() we asked and no answer came back. Nobody decided
                   anything; the question is still open.

    The test is NOT "was a network involved" -- it is "can anyone say WHICH
    answer this was". Booking something as an exclusion claims we know. The
    first adopter outside the original five made this sharper than the
    network framing did: a GROBID header carrying no
    orgName[type=institution] can mean the parser found none OR the paper
    lists none, and nothing in the output separates them (318 of 900 papers
    in a smoke test -- far too large a share to call a decision). No socket
    failed there; the question still went unanswered. Meanwhile "this paper
    is not live in the graph" IS a decision, and stays an exclusion.

    Folding the second into the first is the defect this class now exists to
    prevent. `detect_duplicate_works` reported "checked 551 of 551, 0
    duplicates" when every call had 400'd; `fetch_arxiv_authors_batch` turned
    an HTTP 429 into "arXiv has no record of these 1,559 papers". Both read
    as clean runs, because a skip and a silence looked identical by the time
    they reached the counter.

    So `unanswered` is a separate counter, it is reported as its own line,
    and it exits 4 (unresolved partials) rather than 3 (unaccepted
    exclusions) -- deliberately NOT reachable through accept=(), because
    accepting "s2_did_not_answer" as a category is accepting a permanent
    hole. A run with unanswered sources is not finished; it is resumable.
    """

    def __init__(self):
        self.processed = 0
        self.excluded: Counter = Counter()
        self.unanswered_: Counter = Counter()
        self.unanswered_notes: dict[str, str] = {}

    def process(self, n: int = 1):
        self.processed += n

    def exclude(self, reason: str, n: int = 1):
        self.excluded[reason] += n

    def unanswered(self, reason: str, n: int = 1, note: str | None = None):
        """Record items we asked about and got no answer for. Call this from
        the `except SourceUnavailable` handler -- never exclude()."""
        self.unanswered_[reason] += n
        if note and reason not in self.unanswered_notes:
            self.unanswered_notes[reason] = str(note)[:300]

    @property
    def asked(self) -> int:
        """Everything we put a question to. The M in "checked N of M"."""
        return self.examined

    @property
    def answered(self) -> int:
        """Everything that came back, kept or dropped. The honest N: a job
        may only claim coverage over this, never over `asked`."""
        return self.processed + sum(self.excluded.values())

    @property
    def examined(self) -> int:
        return self.processed + sum(self.excluded.values()) + sum(self.unanswered_.values())

    def as_dict(self) -> dict:
        d = {"examined": self.examined, "processed": self.processed,
             "excluded": dict(self.excluded)}
        # Additive: absent when nothing went unanswered, so a clean run's
        # stamp is byte-identical to the ones written before this channel
        # existed, and a stamp that DOES carry it is unmissable.
        if self.unanswered_:
            d["asked"] = self.asked
            d["answered"] = self.answered
            d["unanswered"] = dict(self.unanswered_)
            if self.unanswered_notes:
                d["unanswered_notes"] = dict(self.unanswered_notes)
        return d

    def summary(self) -> str:
        parts = [f"examined={self.examined}", f"processed={self.processed}"]
        parts += [f"excluded[{r}]={n}" for r, n in sorted(self.excluded.items())]
        if self.unanswered_:
            # asked/answered printed SEPARATELY. All five instances in the
            # brief become visible the moment these two numbers differ.
            parts += [f"asked={self.asked}", f"answered={self.answered}"]
            parts += [f"unanswered[{r}]={n}" for r, n in sorted(self.unanswered_.items())]
        return " ".join(parts)

    def enforce(self, accept: tuple[str, ...] = (), log=print):
        """Fail loudly on any exclusion the caller did not name upfront.
        This is what makes a resume key that skips non-arXiv papers a
        crash instead of a silent permanent hole.

        Unanswered sources fail too, at exit 4, and cannot be accepted --
        see the class docstring. Exit 4 first: a partial run's exclusion
        list is itself incomplete, so reporting it as the headline would
        point at the wrong problem."""
        log(self.summary())
        if self.unanswered_:
            log(f"REFUSED (R3/silence-is-not-absence): {sum(self.unanswered_.values())} "
                f"item(s) were asked about and never answered: {dict(self.unanswered_)}. "
                f"This run covered {self.answered} of {self.asked} and must not be "
                f"reported as covering {self.asked}. Re-run the unanswered slice; "
                f"there is no accept= for a source that did not speak.")
            for r, note in sorted(self.unanswered_notes.items()):
                log(f"    {r}: {note}")
            raise SystemExit(4)
        unaccepted = {r: n for r, n in self.excluded.items() if r not in accept}
        if unaccepted:
            log(f"REFUSED (R3): exclusions occurred that were not explicitly "
                f"accepted: {unaccepted}. Pass their reasons in accept=() only "
                f"after deciding they are correct to drop.")
            raise SystemExit(3)


def stamp(inputs, params: dict | None = None,
          exclusions: ExclusionLedger | None = None) -> dict:
    """Build the derivation record. `inputs` are the actual files read --
    hashed NOW, at derivation time, which is the only honest time."""
    main = sys.argv[0] or "?"
    recs = []
    for p in inputs:
        p = Path(p)
        st = p.stat()  # a claimed input that doesn't exist is a caller bug: raise
        recs.append({"path": str(p), "sha256": sha256_file(p),
                     "bytes": st.st_size, "mtime": _utc(st.st_mtime)})
    out = {
        "schema": SCHEMA,
        "created_at": _utc(),
        "generator": {"script": main, "argv": sys.argv[1:],
                      **_git_identity(Path(main).resolve().parent)},
        "inputs": recs,
    }
    if params is not None:
        out["params"] = {k: v for k, v in params.items()}
    if exclusions is not None:
        out["exclusions"] = exclusions.as_dict()
    return out


def _atomic_write_text(path: Path, text: str):
    # mkstemp does NOT create the directory it is handed, and its failure names
    # the temp file rather than the missing parent -- so a first write into a new
    # directory dies with
    #   FileNotFoundError: .../<INTERNAL>/.load_bolt_ramp.json.6011.tmp
    # about a file that was never created. That crashed `loadtest-bolt-ramp`
    # on 2026-09-13, 21s in, and reads as a mystery rather than as "mkdir first".
    # Every derived artifact in this project comes through here and every lane
    # opens a new <INTERNAL>/ directory, so this is the first-write-in-a-new-lane
    # defect. Creating the parent is what the caller always meant.
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        try: os.unlink(tmp)
        except OSError: pass
        raise


def write_json(path, payload: dict, inputs, params: dict | None = None,
               exclusions: ExclusionLedger | None = None, indent=None):
    """Embed provenance in a dict payload and write atomically. Top-level
    dicts only -- a bare list has nowhere to carry its stamp; wrap it."""
    if not isinstance(payload, dict):
        raise TypeError("write_json needs a dict payload (wrap lists: "
                        "{'results': [...]}); use write_sidecar otherwise")
    path = Path(path)
    payload = {**payload, PROV_KEY: stamp(inputs, params, exclusions)}
    _atomic_write_text(path, json.dumps(payload, indent=indent))
    return path


def write_sidecar(path, inputs, params: dict | None = None,
                  exclusions: ExclusionLedger | None = None):
    """Provenance for outputs that can't embed it (jsonl, parquet, png,
    csv, logs): `<path>.prov.json`, hashing the output itself too so the
    pair is tamper-evident in both directions."""
    path = Path(path)
    s = stamp(inputs, params, exclusions)
    s["output"] = {"path": str(path), "sha256": sha256_file(path),
                   "bytes": path.stat().st_size}
    side = path.with_name(path.name + ".prov.json")
    _atomic_write_text(side, json.dumps(s, indent=1))
    return side


def load(path) -> dict | None:
    """Find a file's provenance: embedded block, else sidecar, else None."""
    path = Path(path)
    if path.suffix == ".json" and not path.name.endswith(".prov.json"):
        try:
            obj = json.load(open(path))
            if isinstance(obj, dict) and PROV_KEY in obj:
                return obj[PROV_KEY]
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
    side = path.with_name(path.name + ".prov.json")
    if side.exists():
        return json.load(open(side))
    return None


def verify(path, log=print) -> int:
    """0 = provenance present, all inputs (and sidecar'd output) still
    hash-match. 1 = no provenance. 2 = drift."""
    path = Path(path)
    prov = load(path)
    if prov is None:
        log(f"{path}: NO PROVENANCE (R1: derived artifacts record their derivation)")
        return 1
    bad = 0
    for rec in prov.get("inputs", []):
        p = Path(rec["path"])
        if not p.exists():
            log(f"{path}: input GONE: {p}")
            bad += 1
        elif sha256_file(p) != rec["sha256"]:
            log(f"{path}: input DRIFTED since derivation: {p}")
            bad += 1
    out = prov.get("output")
    if out and Path(out["path"]).exists() and sha256_file(out["path"]) != out["sha256"]:
        log(f"{path}: OUTPUT no longer matches its sidecar hash")
        bad += 1
    if not bad:
        g = prov.get("generator", {})
        log(f"{path}: ok (generated {prov.get('created_at')} by {g.get('script')}"
            f" @ {str(g.get('git_commit'))[:12]}, {len(prov.get('inputs', []))} inputs current)")
    return 2 if bad else 0


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "verify":
        codes = [verify(p) for p in sys.argv[2:]]
        sys.exit(max(codes))
    print(__doc__)
    sys.exit(64)


if __name__ == "__main__":
    main()
