"""Replay a library's own console transcripts in VeLisp and compare with the recorded AutoCAD output.

Some AutoLISP libraries document functions with Visual LISP console transcripts:
    ;;;_$ (prioritize '(0 1 2) 1 1)
    ;;;(0 2 1)
The first line is the call, the next the result AutoCAD printed. Those are recorded runs in the
original environment, made by the library's author (evidence: source-reported). This tool runs each
call in VeLisp and compares.

Safety: the library is copied to a temporary folder and each call runs there in its own VeLisp
process with a timeout. Only libraries whose top-level forms are definitions should be used
(checked by the caller; see docs/findings). Files listed with --skip are not copied.

Usage:
    python tools/velisp_examples.py <library_dir> <velisp_main.js> <out.json> [--skip <relpath> ...] [--workers N]
"""
import json, os, re, shutil, subprocess, sys, tempfile, collections
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lisp_reader import read, Str, Quote

EXAMPLE = re.compile(r";;;_\$ ?(.*)")
INCLUDE = re.compile(r";;;\(include '([^\s]+) \"([^\"]+)\"\)")

# `include` as the library defines it (load once, by name), resolved against the copy's root.
SHIM = r'''
(setq *llco-loaded* nil)
(defun include (sym res / done)
  (if (and (not (boundp sym)) (not (member res *llco-loaded*)))
    (progn
      (setq *llco-loaded* (cons res *llco-loaded*))
      (if (= (load (strcat res ".LSP") 'llco-nf) 'llco-nf)
        (if (= (load (strcat res ".lsp") 'llco-nf) 'llco-nf)
          (princ (strcat "\nLLCO-INCLUDE-MISSING " res)))))))
'''


def decode(raw):
    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return raw.decode("cp932", errors="replace"), "cp932"


def collect(lib):
    out = []
    for dp, dn, fn in os.walk(lib):
        dn[:] = [d for d in dn if d != ".git"]
        for f in sorted(fn):
            if not f.lower().endswith((".lsp", ".lisp")):
                continue
            path = os.path.join(dp, f)
            text, enc = decode(open(path, "rb").read())
            lines = text.splitlines()
            inc = next((INCLUDE.match(l) for l in lines[:3] if INCLUDE.match(l)), None)
            for i, l in enumerate(lines):
                m = EXAMPLE.match(l)
                if m and i + 1 < len(lines) and lines[i + 1].startswith(";;;") and not lines[i + 1].startswith(";;;_$"):
                    expr, expected = m.group(1).strip(), lines[i + 1][3:].strip()
                    out.append({"file": os.path.relpath(path, lib), "line": i + 1, "encoding": enc,
                                "include": [inc.group(1), inc.group(2)] if inc else None,
                                "expr": expr, "expected": expected,
                                "non_ascii": any(ord(c) > 127 for c in expr + expected)})
    return out


# Runtime workarounds applied to the temporary copy only. Each must keep AutoLISP semantics unchanged.
#   W1  VeLisp 0.8.0 misreads a parameter list that starts with "/" directly after "(" -- "(defun f (/ a) ...)"
#       raises "too few arguments". Inserting a space -- "(defun f ( / a) ...)" -- is the same AutoLISP.
W1 = re.compile(r"(\(defun(?:-q)?\s+[^\s()]+\s*\()/", re.I)


def apply_workarounds(root):
    changed = 0
    for dp, dn, fn in os.walk(root):
        for f in fn:
            if f.lower().endswith((".lsp", ".lisp")):
                p = os.path.join(dp, f)
                raw = open(p, "rb").read()
                text, enc = decode(raw)
                new, n = W1.subn(r"\1 /", text)
                if n:
                    open(p, "w", encoding="utf-8").write(new)
                    changed += n
    return {"W1_param_list_slash": changed}


def norm(s):
    return re.sub(r"\s+", " ", s.strip())


def data_equal(a, b, tol=1e-6):
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(data_equal(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, Str) and isinstance(b, Str):
        return a.value == b.value
    if isinstance(a, Quote) or isinstance(b, Quote):
        return repr(a) == repr(b)
    try:
        return abs(float(a) - float(b)) <= tol * max(1.0, abs(float(b)))
    except (TypeError, ValueError):
        return a == b


def compare(got, expected):
    if norm(got) == norm(expected):
        return "pass"
    try:
        ga, _ = read(got); ea, _ = read(expected)
        if ga and ea and data_equal(ga[0], ea[0]):
            return "pass_numeric"
    except Exception:
        pass
    return "mismatch"


def run_one(ex, work, velisp):
    prog = SHIM
    if ex["include"]:
        prog += f'(include \'{ex["include"][0]} "{ex["include"][1]}")\n'
    prog += f'(princ "\\nLLCO-RESULT ")(prin1 {ex["expr"]})(princ "\\n")\n'
    fd, path = tempfile.mkstemp(suffix=".lsp", dir=work)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(prog)
    try:
        p = subprocess.run(["node", velisp, "--no-dcl", path], cwd=work, capture_output=True, text=True, timeout=30)
        outtxt = p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        return {**ex, "status": "timeout", "got": None, "missing": None}
    finally:
        os.remove(path)
    m = re.search(r"LLCO-RESULT (.*)", outtxt)
    err = re.search(r"Error: (.*)", outtxt)
    if m and not err:
        got = m.group(1).strip()
        return {**ex, "status": compare(got, ex["expected"]), "got": got, "missing": None}
    msg = err.group(1).strip() if err else outtxt.strip()[-160:]
    miss = re.match(r"([^\s:]+): function not defined", msg)
    arity = re.match(r"([^\s:]+): too (many|few) arguments", msg)
    status = "missing_function" if miss else "arity_error" if arity else "parse_error" if ("token recognition" in msg or "no viable alternative" in msg) else "error"
    return {**ex, "status": status, "got": None, "missing": miss.group(1) if miss else (arity.group(1) + " (" + arity.group(2) + ")" if arity else None),
            "error": msg[:160]}


def main():
    args = sys.argv[1:]
    skip, workers = [], 8
    while "--skip" in args:
        i = args.index("--skip"); skip.append(args[i + 1]); del args[i:i + 2]
    if "--workers" in args:
        i = args.index("--workers"); workers = int(args[i + 1]); del args[i:i + 2]
    lib, velisp, out = args
    velisp = os.path.abspath(velisp)
    examples = collect(lib)
    work = tempfile.mkdtemp(prefix="llco-velisp-")
    shutil.copytree(lib, os.path.join(work, "lib"), ignore=shutil.ignore_patterns(".git", *[os.path.basename(s) for s in skip]))
    root = os.path.join(work, "lib")
    workarounds = apply_workarounds(root)
    with ThreadPoolExecutor(workers) as pool:
        results = list(pool.map(lambda e: run_one(e, root, velisp), examples))
    shutil.rmtree(work, ignore_errors=True)
    by = collections.Counter(r["status"] for r in results)
    missing = collections.Counter(r["missing"] for r in results if r["missing"])
    errors = collections.Counter(r.get("error", "")[:60] for r in results if r["status"] == "error")
    ascii_only = [r for r in results if not r["non_ascii"]]
    summary = {"examples": len(results), "files": len({r["file"] for r in results}), "workarounds": workarounds,
               "status": dict(by), "status_ascii_only": dict(collections.Counter(r["status"] for r in ascii_only)),
               "missing_or_arity": missing.most_common(), "other_errors": errors.most_common(10)}
    json.dump({"summary": summary, "results": results}, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(summary, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
