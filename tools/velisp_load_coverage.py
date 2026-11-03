"""Load every file of a library in VeLisp, one process per file, and classify the outcome.

  loaded         the file loads (its definitions run) without error
  parse_error    VeLisp's grammar rejects the file (valid AutoLISP that VeLisp cannot read, or a real syntax error)
  runtime_error  the file parses but a top-level form fails while loading

The library's `include` loader is provided by the same shim as tools/velisp_examples.py, so files that
include others load them first. Same safety rules: temporary copy, timeout, definitions-only libraries.

Usage:
    python tools/velisp_load_coverage.py <library_dir> <velisp_main.js> <out.json> [--skip <name> ...]
"""
import json, os, re, shutil, subprocess, sys, tempfile, collections
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from velisp_examples import SHIM, apply_workarounds


def classify(out):
    err = re.search(r"Error: (.*)", out)
    if not err:
        return "loaded", None
    msg = err.group(1)
    if any(k in msg for k in ("no viable alternative", "mismatched input", "token recognition", "extraneous input", "missing")):
        return "parse_error", msg[:200]
    return "runtime_error", msg[:200]


def main():
    args = sys.argv[1:]
    skip = []
    while "--skip" in args:
        i = args.index("--skip"); skip.append(args[i + 1]); del args[i:i + 2]
    lib, velisp, out = args
    velisp = os.path.abspath(velisp)
    work = tempfile.mkdtemp(prefix="llco-load-")
    root = os.path.join(work, "lib")
    shutil.copytree(lib, root, ignore=shutil.ignore_patterns(".git", *skip))
    workarounds = apply_workarounds(root)
    files = sorted(os.path.relpath(os.path.join(dp, f), root) for dp, dn, fn in os.walk(root) for f in fn
                   if f.lower().endswith((".lsp", ".lisp")))

    def one(rel):
        fd, path = tempfile.mkstemp(suffix=".lsp", dir=root)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(SHIM + f'(load "{rel}")(princ "\\nLLCO-LOADED")\n')
        try:
            p = subprocess.run(["node", velisp, "--no-dcl", path], cwd=root, capture_output=True, text=True, timeout=60)
            status, msg = classify(p.stdout + p.stderr)
        except subprocess.TimeoutExpired:
            status, msg = "timeout", None
        finally:
            os.remove(path)
        return {"file": rel, "status": status, "error": msg}

    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(one, files))
    shutil.rmtree(work, ignore_errors=True)
    summary = {"files": len(results), "workarounds": workarounds,
               "status": dict(collections.Counter(r["status"] for r in results))}
    json.dump({"summary": summary, "results": results}, open(out, "w", encoding="utf-8"), indent=1)
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
