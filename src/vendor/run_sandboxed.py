#!/usr/bin/env python3
"""
Minimal local sandbox runner for generated implementations: subprocess
isolation, CPU/memory rlimits, wall-clock timeout, network disabled by
a socket-killing preamble. Suitable for local dev and the hub-50 pilot;
SCALE runs belong on ephemeral Lambda instances with OS-level egress
blocking (the DAPT scp-up/pull/terminate workflow), not on this.

This is deliberately not a security boundary against adversarial code
-- inputs here are our own generated files. It exists to make runs
deterministic, bounded, and offline so verification results are
reproducible artifacts.

Usage:
    ./venv/bin/python <REFIMPL>/run_sandboxed.py \
        impl.py --entry forward --inputs-json inputs.json --timeout 30
"""
import argparse
import json
import resource
import subprocess
import sys
import tempfile
from pathlib import Path

PREAMBLE = """\
import socket as _s
def _blocked(*a, **k):
    raise RuntimeError("network disabled in verification sandbox")
_s.socket = _blocked
_s.create_connection = _blocked
import random as _r; _r.seed(0)
try:
    import numpy as _np; _np.random.seed(0)
except ImportError:
    pass
"""

RUNNER = """\
import json, sys, importlib.util
spec = importlib.util.spec_from_file_location("impl", sys.argv[1])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
fn = getattr(mod, sys.argv[2])
inputs = json.loads(open(sys.argv[3]).read())

def sanitize(v):
    # Recursive: numpy scalars/arrays at ANY nesting depth become plain
    # JSON values -- a top-level-only conversion made identical tuple
    # results compare as str vs int (real false-divergence, SpecDec).
    try:
        import numpy as np
        if isinstance(v, np.ndarray):
            return {"__ndarray__": v.tolist(), "shape": list(v.shape)}
        if isinstance(v, np.generic):
            return v.item()
    except ImportError:
        pass
    if isinstance(v, (list, tuple)):
        return [sanitize(x) for x in v]
    if isinstance(v, dict):
        return {k: sanitize(x) for k, x in v.items()}
    return v

outs = [sanitize(fn(**case)) for case in inputs]
print(json.dumps({"ok": True, "outputs": outs}, default=str))
"""


def set_limits(cpu_seconds: int, mem_mb: int):
    def fn():
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
        # RLIMIT_AS is unreliable on macOS; best-effort, real limit on Linux runners
        try:
            resource.setrlimit(resource.RLIMIT_AS, (mem_mb << 20, mem_mb << 20))
        except (ValueError, OSError):
            pass
    return fn


def run(impl: Path, entry: str, inputs_json: Path,
        timeout: int = 30, cpu: int = 25, mem_mb: int = 2048) -> dict:
    with tempfile.TemporaryDirectory() as td:
        runner = Path(td) / "_runner.py"
        runner.write_text(PREAMBLE + RUNNER)
        # cwd is the temp dir, so caller-relative paths MUST be resolved
        # first (real bug: relative impl path + cwd=td -> FileNotFoundError)
        impl, inputs_json = Path(impl).resolve(), Path(inputs_json).resolve()
        try:
            p = subprocess.run(
                [sys.executable, "-I", str(runner), str(impl), entry, str(inputs_json)],
                capture_output=True, text=True, timeout=timeout,
                preexec_fn=set_limits(cpu, mem_mb), cwd=td,
                env={"PYTHONHASHSEED": "0", "OMP_NUM_THREADS": "1",
                     "MKL_NUM_THREADS": "1", "PATH": "/usr/bin:/bin"},
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "timeout"}
    if p.returncode != 0:
        return {"ok": False, "error": "crash", "stderr": p.stderr[-2000:]}
    try:
        return json.loads(p.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return {"ok": False, "error": "bad_output", "stdout": p.stdout[-2000:]}


IMPORT_RUNNER = """\
import sys, importlib.util
spec = importlib.util.spec_from_file_location("impl", sys.argv[1])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print("IMPORT_OK")
"""


# The shared PREAMBLE blocks the network by REPLACING socket.socket with a
# function. That is fine for the generated lane, which is pure numpy by
# contract and never imports ssl. It is fatal for the harvest lane: real
# repository code imports torch, torch imports torch.hub -> urllib -> http.client
# -> ssl, and ssl.py does `class SSLSocket(socket)` -- subclassing a function
# raises "TypeError: function() argument 'code' must be code, not str", which
# looks nothing like a network guard and cost an afternoon to read.
#
# Blocking the CONNECT METHODS instead leaves socket a class, so the import
# chain resolves, and still refuses every outbound connection. Left as a
# separate constant rather than changing the shared one, because the JSON lane
# is working and this is not the commit to re-verify it in.
FIXTURE_PREAMBLE = """\
import socket as _s
def _blocked(*a, **k):
    raise RuntimeError("network disabled in verification sandbox")
_s.socket.connect = _blocked
_s.socket.connect_ex = _blocked
_s.create_connection = _blocked
_s.socket.sendto = _blocked
import random as _r; _r.seed(0)
try:
    import numpy as _np; _np.random.seed(0)
except ImportError:
    pass
"""

FIXTURE_RUNNER = """\
import json, sys, importlib.util

# The fixture is PYTHON, not JSON, because real repository code takes objects a
# JSON document cannot express -- an nn.Module, a DataLoader, a tokenizer. It
# runs in this same sandbox (no network, seeded) and must end by defining ARGS,
# a dict of keyword arguments; ARGS_LIST, a list of such dicts, is the
# multi-input form and is preferred when present.
ns = {}
exec(compile(open(sys.argv[3]).read(), "fixture", "exec"), ns)
cases = ns.get("ARGS_LIST")
if cases is None:
    if "ARGS" not in ns:
        print(json.dumps({"ok": False, "error": "fixture_no_ARGS"})); raise SystemExit(0)
    cases = [ns["ARGS"]]

spec = importlib.util.spec_from_file_location("impl", sys.argv[1])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
fn = getattr(mod, sys.argv[2])

def sanitize(v):
    try:
        import numpy as np
        if isinstance(v, np.ndarray):
            return {"__ndarray__": v.tolist(), "shape": list(v.shape)}
        if isinstance(v, np.generic):
            return v.item()
    except ImportError:
        pass
    try:
        import torch
        if isinstance(v, torch.Tensor):
            a = v.detach().cpu().numpy()
            return {"__ndarray__": a.tolist(), "shape": list(a.shape)}
    except ImportError:
        pass
    if isinstance(v, (list, tuple)):
        return [sanitize(x) for x in v]
    if isinstance(v, dict):
        return {k: sanitize(x) for k, x in v.items()}
    return v

# Per-case, not all-or-nothing. A widened fixture that produces five argument
# sets of which four are valid used to fail entirely on the fifth, and the
# sample was lost -- 15% of attempts died this way. Which cases the ORIGINAL
# accepts defines the valid input set; a case it rejects was never a valid
# input and dropping it is correct. A peer failing one of the surviving cases
# is a different matter and is the caller's to judge.
outs, ok_index, case_errors = [], [], {}
for _i, case in enumerate(cases):
    try:
        outs.append(sanitize(fn(**case)))
        ok_index.append(_i)
    except Exception as _e:
        outs.append(None)
        case_errors[_i] = type(_e).__name__ + ": " + str(_e)[:120]
if not ok_index:
    print(json.dumps({"ok": False, "error": "no_case_ran",
                      "case_errors": case_errors, "n_inputs": len(cases)}))
    raise SystemExit(0)

# A function that RETURNS AN OBJECT -- an nn.Module, an optimizer, a Dataset,
# a Namespace -- is not verifiable by comparing outputs, because two
# independently built Sequentials are never "equal" in any useful sense. That
# is a category, not a crash, and calling it one lets the caller refuse V2 for
# the right reason instead of recording "unserializable" and moving on.
opaque = set()
def _scan(v):
    try:
        json.dumps(v)
    except TypeError:
        if isinstance(v, dict):
            for x in v.values(): _scan(x)
        elif isinstance(v, (list, tuple)):
            for x in v: _scan(x)
        else:
            opaque.add(type(v).__module__ + "." + type(v).__name__)
for _i in ok_index: _scan(outs[_i])

# What the caller will actually pass. A peer told only `def f(x, mask)` guesses
# the types, and a peer that guesses numpy where the fixture builds a torch
# tensor dies on the first call -- which is a calling-convention failure
# recorded as a modelling failure. Types are free to report here and reveal
# nothing about the implementation.
def _describe(v):
    t = type(v).__module__ + "." + type(v).__name__ if type(v).__module__ != "builtins" \
        else type(v).__name__
    try:
        import numpy as np
        if isinstance(v, np.ndarray):
            return f"numpy.ndarray {v.dtype} shape={list(v.shape)}"
    except ImportError:
        pass
    try:
        import torch
        if isinstance(v, torch.Tensor):
            return f"torch.Tensor {v.dtype} shape={list(v.shape)}"
    except ImportError:
        pass
    if isinstance(v, (int, float, str, bool)) or v is None:
        return f"{t}={v!r}"[:60]
    if isinstance(v, (list, tuple)):
        return f"{t} len={len(v)}"
    return t
arg_types = {k: _describe(v) for k, v in cases[ok_index[0]].items()}

if opaque:
    print(json.dumps({"ok": False, "error": "object_return",
                      "types": sorted(opaque), "n_inputs": len(cases)}))
else:
    print(json.dumps({"ok": True, "outputs": outs, "n_inputs": len(ok_index),
                      "ok_index": ok_index, "case_errors": case_errors,
                      "arg_types": arg_types}))
"""


def run_fixture(impl: Path, entry: str, fixture_py: Path,
                timeout: int = 60, cpu: int = 45, mem_mb: int = 3072) -> dict:
    """`run()`, but the inputs come from a Python fixture instead of JSON.

    Same sandbox, same limits, wider budget: a fixture may construct torch
    modules, which is slower and heavier than deserialising a JSON list. Torch
    tensors are sanitised alongside numpy arrays -- the JSON runner never had to
    because the generated lane is pure-numpy by contract, and the harvest lane
    is not."""
    with tempfile.TemporaryDirectory() as td:
        runner = Path(td) / "_runner.py"
        runner.write_text(FIXTURE_PREAMBLE + FIXTURE_RUNNER)
        impl, fixture_py = Path(impl).resolve(), Path(fixture_py).resolve()
        try:
            p = subprocess.run(
                [sys.executable, "-I", str(runner), str(impl), entry, str(fixture_py)],
                capture_output=True, text=True, timeout=timeout,
                preexec_fn=set_limits(cpu, mem_mb), cwd=td,
                # MPLBACKEND=Agg because matplotlib is now in the verification
                # environment (harvest-lane repo code imports it at module
                # scope even when the function under test never plots). Without
                # a headless backend it reaches for a display and either fails
                # or blocks -- a hang is worse than the ImportError it replaces.
                env={"PYTHONHASHSEED": "0", "OMP_NUM_THREADS": "1",
                     "MKL_NUM_THREADS": "1", "PATH": "/usr/bin:/bin",
                     "MPLBACKEND": "Agg", "HOME": td},
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "timeout"}
    if p.returncode != 0:
        return {"ok": False, "error": "crash", "stderr": p.stderr[-2000:]}
    try:
        return json.loads(p.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return {"ok": False, "error": "unparseable_output", "stdout": p.stdout[-500:]}


def check_import(impl: Path, timeout: int = 20) -> dict:
    """V0 primitive: does the file import cleanly under the same
    isolation posture (no network, rlimits, -I)?"""
    with tempfile.TemporaryDirectory() as td:
        runner = Path(td) / "_import_runner.py"
        runner.write_text(PREAMBLE + IMPORT_RUNNER)
        impl = Path(impl).resolve()
        try:
            p = subprocess.run(
                [sys.executable, "-I", str(runner), str(impl)],
                capture_output=True, text=True, timeout=timeout,
                preexec_fn=set_limits(15, 1024), cwd=td,
                env={"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin"},
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "timeout"}
    if p.returncode == 0 and "IMPORT_OK" in p.stdout:
        return {"ok": True}
    return {"ok": False, "error": "import_fail", "stderr": p.stderr[-1000:]}



CHECK_RUNNER = """\
import json, sys, importlib.util
def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
impl = load(sys.argv[1], "impl")
fn = getattr(impl, sys.argv[2])
checker = load(sys.argv[3], "checker")
results = checker.check(fn)
# Coerce passed to a NATIVE bool before serialization. np.bool_ is not
# JSON-serializable, so default=str was turning both np.True_ and
# np.False_ into the STRINGS "True"/"False" -- and every downstream
# consumer that truth-tested or bool()-ed the field read BOTH as
# passing. Found 2026-08-31 by the referee audit's mutation probe
# (a sign-flipped mutant "survived" five closed-form tests); reached
# the V3 grant counter (bool("False") is True), the benchmark referee,
# and task revalidation. bool() here is correct for np.bool_ and a
# no-op for native bools; anything unconvertible fails closed.
for _r in results:
    try:
        _r["passed"] = bool(_r["passed"])
    except Exception:
        _r["passed"] = False
print(json.dumps({"ok": True, "results": results}, default=str))
"""


def run_check(impl: Path, entry: str, check_file: Path,
              timeout: int = 45, cpu: int = 35, mem_mb: int = 2048) -> dict:
    """Property-test mode: loads the impl AND a drafted checker file
    (def check(fn) -> list[{name, passed, detail}]) in the same
    sandbox, runs the checks against the entry function."""
    impl, check_file = Path(impl).resolve(), Path(check_file).resolve()
    with tempfile.TemporaryDirectory() as td:
        runner = Path(td) / "_check_runner.py"
        runner.write_text(PREAMBLE + CHECK_RUNNER)
        try:
            p = subprocess.run(
                [sys.executable, "-I", str(runner), str(impl), entry, str(check_file)],
                capture_output=True, text=True, timeout=timeout,
                preexec_fn=set_limits(cpu, mem_mb), cwd=td,
                env={"PYTHONHASHSEED": "0", "OMP_NUM_THREADS": "1",
                     "MKL_NUM_THREADS": "1", "PATH": "/usr/bin:/bin"},
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "timeout"}
    if p.returncode != 0:
        return {"ok": False, "error": "crash", "stderr": p.stderr[-2000:]}
    try:
        return json.loads(p.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return {"ok": False, "error": "bad_output", "stdout": p.stdout[-2000:]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("impl")
    ap.add_argument("--entry", required=True)
    ap.add_argument("--inputs-json", required=True)
    ap.add_argument("--timeout", type=int, default=30)
    args = ap.parse_args()
    result = run(Path(args.impl), args.entry, Path(args.inputs_json), args.timeout)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
