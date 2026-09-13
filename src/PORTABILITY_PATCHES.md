# Portability patches

`tools/assemble.py` applies the rules below to `src/*.py` on the way
out of the working repo. They exist for one reason: the harness was
written to run from inside that repo, and without them the `none`
arm -- the one arm needing no credentials at all -- dies at import
for every reader of this repository.

**None of them changes what any arm does.** Each either resolves a
path for the published layout or reads an environment variable whose
default reproduces the internal behaviour. Everything else in `src/`
is byte-identical to the code that produced the numbers; `MANIFEST.json`
marks a patched file `portability-patched` and an untouched one
`verbatim`.

## Rules

- **the shared modules the harness imports from the working repo's root are vendored into src/vendor/ here, so that directory goes on the path**

  ```diff
  - sys.path.insert(0, str(REPO))
  + sys.path.insert(0, str(REPO))
  + sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))
  ```

- **run_sandboxed.py (the referee's executor) is vendored into src/vendor/, which the rule above already put on the path, so this line is dropped**

  ```diff
  - sys.path.insert(0, str(REPO / "<REFIMPL>"))
  ```

- **the repo root is one level above src/ here, two levels above the benchmark directory internally; BENCH_REPO_ROOT overrides either way**

  ```diff
  - REPO = HERE.parents[1]
  + REPO = Path(os.environ.get("BENCH_REPO_ROOT", HERE.parent))
  ```

- **same, for the two arm modules that resolve the root inline**

  ```diff
  - REPO = Path(__file__).resolve().parents[2]
  + REPO = Path(os.environ.get("BENCH_REPO_ROOT",
  +                            Path(__file__).resolve().parents[1]))
  ```

- **corpus_files.py is vendored; the original inserted a directory ABOVE the repo root onto sys.path, which is worth not shipping**

  ```diff
  - _sys.path.insert(0, str(_P(__file__).resolve().parents[2]))
  + _sys.path.insert(0, str(_P(__file__).resolve().parent / "vendor"))
  ```

- **the subject's run_python tool must use the reader's interpreter; BENCH_PYTHON pins a different one**

  ```diff
  - [str(REPO / "venv" / "bin" / "python3"), "-I", str(script)],
  + [os.environ.get("BENCH_PYTHON", sys.executable), "-I", str(script)],
  ```

- **compare_runs.py resolves a relative --a/--b against the directory it lives in, which internally held the result files and here is src/**

  ```diff
  - HERE / args.a
  + REPO / args.a
  ```

- **same for --b**

  ```diff
  - HERE / args.b
  + REPO / args.b
  ```

- **task sets live at <repo>/tasks/ in the published layout**

  ```diff
  - default=str(HERE / "tasks"
  + default=str(REPO / "tasks"
  ```

- **a fresh run tree belongs at the repo root, beside data/runs/ rather than inside src/**

  ```diff
  - default=str(HERE / "runs")
  + default=str(REPO / "runs")
  ```

- **the published run metadata lives under data/runs/**

  ```diff
  - default=str(HERE / "runs_v15")
  + default=str(REPO / "data" / "runs" / "runs_v15")
  ```

- **the arm-purity gate reads the arm module and the index from src/**

  ```diff
  - REPO = Path(__file__).resolve().parent
  - GW = REPO / "<BENCH>"
  + REPO = Path(__file__).resolve().parents[1]
  + GW = REPO
  ```

- **the gate's tokenizer-parity check needs the vendored modules on the path**

  ```diff
  -     sys.path.insert(0, str(GW))
  +     sys.path.insert(0, str(GW))
  +     sys.path.insert(0, str(GW / "vendor"))
  ```

- **the gate's tokenizer-parity check loads the index builder from src/**

  ```diff
  - "_bci", REPO / "<BENCH>/build_code_index.py")
  + "_bci", GW / "build_code_index.py")
  ```

- **the gate looks for the index where the arm does, not beside the arm**

  ```diff
  - INDEX = GW / "code_index"
  + INDEX = Path(os.environ.get("CODE_ONLY_INDEX", REPO.parent / "code_index"))
  ```

- **the flat index is not shipped; the default points where you would build one, and CODE_ONLY_INDEX overrides it**

  ```diff
  - INDEX_DIR = Path(os.environ.get("CODE_ONLY_INDEX", HERE / "code_index"))
  + INDEX_DIR = Path(os.environ.get("CODE_ONLY_INDEX", REPO / "code_index"))
  ```

- **a missing index reports as a partial, not as a finding**

  ```diff
  - findings.append(f"[C] alignment: {lex_p} missing -- run build_code_index.py")
  + findings.append(f"[PARTIAL] alignment: {lex_p} missing -- run "
  +                         f"build_code_index.py, or set CODE_ONLY_INDEX")
  ```

- **and the exit code follows the contract: 1 only when a check actually failed, 4 when one could not run**

  ```diff
  -     if findings:
  -         print("qc_code_only_arm: FINDINGS")
  -         for f in findings:
  -             print("  " + f)
  -         return 1
  +     real = [f for f in findings if not f.startswith("[PARTIAL]")]
  +     if findings:
  +         print("qc_code_only_arm: "
  +               + ("FINDINGS" if real else "UNVERIFIED (exit 4) -- not a pass"))
  +         for f in findings:
  +             print("  " + f)
  +         return 1 if real else 4
  ```

- **result/probe/analysis output defaults point at `data/`**

  ```diff
  - default=str(HERE / "<name>.json")
  + default=str(REPO / "data" / "<name>.json")
  ```

- **`import os` added** where a rule above introduced its first use.

## Where each rule landed

- `src/agent_harness.py`
  - the shared modules the harness imports from the working repo's root are vendored into src/vendor/ here, so that directory goes on the path
  - run_sandboxed.py (the referee's executor) is vendored into src/vendor/, which the rule above already put on the path, so this line is dropped
  - the repo root is one level above src/ here, two levels above the benchmark directory internally; BENCH_REPO_ROOT overrides either way
  - the subject's run_python tool must use the reader's interpreter; BENCH_PYTHON pins a different one
  - task sets live at <repo>/tasks/ in the published layout
  - a fresh run tree belongs at the repo root, beside data/runs/ rather than inside src/
- `src/analyze.py`
  - the shared modules the harness imports from the working repo's root are vendored into src/vendor/ here, so that directory goes on the path
  - the repo root is one level above src/ here, two levels above the benchmark directory internally; BENCH_REPO_ROOT overrides either way
  - a fresh run tree belongs at the repo root, beside data/runs/ rather than inside src/
  - result/probe/analysis defaults point at data/
  - added `import os` for the env-var default above
- `src/analyze_code_only_mechanism.py`
  - the shared modules the harness imports from the working repo's root are vendored into src/vendor/ here, so that directory goes on the path
  - the repo root is one level above src/ here, two levels above the benchmark directory internally; BENCH_REPO_ROOT overrides either way
  - task sets live at <repo>/tasks/ in the published layout
  - the published run metadata lives under data/runs/
  - result/probe/analysis defaults point at data/
  - added `import os` for the env-var default above
- `src/analyze_substitution.py`
  - the shared modules the harness imports from the working repo's root are vendored into src/vendor/ here, so that directory goes on the path
  - the repo root is one level above src/ here, two levels above the benchmark directory internally; BENCH_REPO_ROOT overrides either way
  - result/probe/analysis defaults point at data/
- `src/build_code_index.py`
  - the shared modules the harness imports from the working repo's root are vendored into src/vendor/ here, so that directory goes on the path
  - the repo root is one level above src/ here, two levels above the benchmark directory internally; BENCH_REPO_ROOT overrides either way
- `src/build_code_vectors.py`
  - the shared modules the harness imports from the working repo's root are vendored into src/vendor/ here, so that directory goes on the path
  - the repo root is one level above src/ here, two levels above the benchmark directory internally; BENCH_REPO_ROOT overrides either way
- `src/build_holdout_sets.py`
  - the shared modules the harness imports from the working repo's root are vendored into src/vendor/ here, so that directory goes on the path
  - the repo root is one level above src/ here, two levels above the benchmark directory internally; BENCH_REPO_ROOT overrides either way
- `src/build_task_set.py`
  - the shared modules the harness imports from the working repo's root are vendored into src/vendor/ here, so that directory goes on the path
  - run_sandboxed.py (the referee's executor) is vendored into src/vendor/, which the rule above already put on the path, so this line is dropped
  - the repo root is one level above src/ here, two levels above the benchmark directory internally; BENCH_REPO_ROOT overrides either way
  - task sets live at <repo>/tasks/ in the published layout
- `src/build_task_set_substitution.py`
  - the shared modules the harness imports from the working repo's root are vendored into src/vendor/ here, so that directory goes on the path
  - the repo root is one level above src/ here, two levels above the benchmark directory internally; BENCH_REPO_ROOT overrides either way
  - task sets live at <repo>/tasks/ in the published layout
- `src/code_only_arm_tools.py`
  - the shared modules the harness imports from the working repo's root are vendored into src/vendor/ here, so that directory goes on the path
  - the repo root is one level above src/ here, two levels above the benchmark directory internally; BENCH_REPO_ROOT overrides either way
  - the flat index is not shipped; the default points where you would build one, and CODE_ONLY_INDEX overrides it
- `src/compare_runs.py`
  - the shared modules the harness imports from the working repo's root are vendored into src/vendor/ here, so that directory goes on the path
  - the repo root is one level above src/ here, two levels above the benchmark directory internally; BENCH_REPO_ROOT overrides either way
  - corpus_files.py is vendored; the original inserted a directory ABOVE the repo root onto sys.path, which is worth not shipping
  - compare_runs.py resolves a relative --a/--b against the directory it lives in, which internally held the result files and here is src/
  - same for --b
  - task sets live at <repo>/tasks/ in the published layout
  - added `import os` for the env-var default above
- `src/probe_code_only_retrieval.py`
  - the shared modules the harness imports from the working repo's root are vendored into src/vendor/ here, so that directory goes on the path
  - the repo root is one level above src/ here, two levels above the benchmark directory internally; BENCH_REPO_ROOT overrides either way
  - task sets live at <repo>/tasks/ in the published layout
  - result/probe/analysis defaults point at data/
- `src/probe_substitution.py`
  - the shared modules the harness imports from the working repo's root are vendored into src/vendor/ here, so that directory goes on the path
  - the repo root is one level above src/ here, two levels above the benchmark directory internally; BENCH_REPO_ROOT overrides either way
  - result/probe/analysis defaults point at data/
  - added `import os` for the env-var default above
- `src/qc/qc_code_only_arm.py`
  - the arm-purity gate reads the arm module and the index from src/
  - the gate's tokenizer-parity check needs the vendored modules on the path
  - the gate's tokenizer-parity check loads the index builder from src/
  - the gate looks for the index where the arm does, not beside the arm
  - a missing index reports as a partial, not as a finding
  - and the exit code follows the contract: 1 only when a check actually failed, 4 when one could not run
  - added `import os` for the env-var default above
- `src/search_arm_tools.py`
  - the shared modules the harness imports from the working repo's root are vendored into src/vendor/ here, so that directory goes on the path
  - same, for the two arm modules that resolve the root inline
- `src/syntology_arm_tools.py`
  - the shared modules the harness imports from the working repo's root are vendored into src/vendor/ here, so that directory goes on the path
  - same, for the two arm modules that resolve the root inline
- `src/verify_holdout.py`
  - the shared modules the harness imports from the working repo's root are vendored into src/vendor/ here, so that directory goes on the path
  - the repo root is one level above src/ here, two levels above the benchmark directory internally; BENCH_REPO_ROOT overrides either way
  - result/probe/analysis defaults point at data/
- `src/verify_solutions.py`
  - the shared modules the harness imports from the working repo's root are vendored into src/vendor/ here, so that directory goes on the path
  - run_sandboxed.py (the referee's executor) is vendored into src/vendor/, which the rule above already put on the path, so this line is dropped
  - the repo root is one level above src/ here, two levels above the benchmark directory internally; BENCH_REPO_ROOT overrides either way
  - corpus_files.py is vendored; the original inserted a directory ABOVE the repo root onto sys.path, which is worth not shipping
  - task sets live at <repo>/tasks/ in the published layout
  - a fresh run tree belongs at the repo root, beside data/runs/ rather than inside src/
  - added `import os` for the env-var default above

## Not patched, and therefore still true of this tree

- `tasks/*.json` had `property_tests` / `impl_for_validation` repointed at `referees/<task_id>/` (marked `path-rewritten`). The internal path of every referee file is preserved in `referees/INDEX.json` under `internal_source`.
- `src/vendor/query_engine/` is a **stand-in**, not the real package. See its docstring.
- `src/sweeps/*.sh` are copied verbatim and will NOT run here: they `cd` to a working-repo layout, `source .env`, and call `joblog.sh`. They are shipped as the record of how each sweep was actually launched, not as an entry point.
