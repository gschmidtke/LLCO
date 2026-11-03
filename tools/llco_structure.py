"""LLCO step 2a: structure of an AutoLISP estate. Reads text only; executes nothing.

For one source folder it reports
  - every defun (file, line, kind: command or function, parameters, locals);
  - calls between them (direct calls, and functions passed by name: 'fn, (function fn));
  - load calls;
  - which called symbols are internal (defined in the estate), built-in AutoLISP
    (AutoLispExt help index), or unresolved (neither: external library or missing);
  - functions defined more than once (behaviour then depends on load order);
  - for every command, the internal functions it reaches and the files they live in.

Usage:
    python tools/llco_structure.py <source_dir> <builtins_json> <out.json> [--exclude <subdir> ...]
builtins_json: AutoLispExt extension/src/help/webHelpAbstraction.json (fetched by tools/fetch_tools.py).
"""
import json, os, sys, collections, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lisp_reader import read, Form, Str, Quote

# AutoLISP functions that exist but are missing from the AutoLispExt help index (2021):
# the car/cdr family beyond two levels and a few undocumented Visual LISP functions.
SUPPLEMENT = {"caaar", "caadr", "cadar", "caddr", "cdaar", "cdadr", "cddar", "cdddr", "caar", "cadr", "cdar", "cddr",
              "cadddr", "caaddr", "cddddr", "vlax-invoke", "vlax-get", "vlax-put", "vl-bt", "vl-exit-with-error",
              "vl-exit-with-value", "*error*"}
SPECIAL = {"defun", "defun-q", "lambda", "setq", "if", "cond", "progn", "while", "repeat", "foreach",
           "and", "or", "not", "quote", "function", "vl-catch-all-apply", "apply", "mapcar", "eval"}


def walk(form, on_call, on_ref, quoted=False):
    if isinstance(form, Quote):
        inner = form.form
        if isinstance(inner, str):
            on_ref(inner)
        # quoted lists are data (e.g. DXF filters); do not treat as calls
        return
    if not isinstance(form, list) or not form:
        return
    head = form[0]
    if head in ("defun", "defun-q") and len(form) > 2:   # nested definition: skip name and parameter list
        for x in form[3:]:
            walk(x, on_call, on_ref)
        return
    if head == "lambda" and len(form) > 1:                # skip parameter list
        for x in form[2:]:
            walk(x, on_call, on_ref)
        return
    if isinstance(head, str):
        on_call(head, getattr(form, "line", None))
        if head == "function" and len(form) > 1 and isinstance(form[1], str):
            on_ref(form[1])
        if head == "cond":  # clauses are lists whose head is a test, not a call
            for clause in form[1:]:
                if isinstance(clause, list):
                    for x in clause:
                        walk(x, on_call, on_ref)
            return
    elif isinstance(head, list):
        walk(head, on_call, on_ref)
    for x in form[1:]:
        walk(x, on_call, on_ref)


def params_of(arglist):
    if not isinstance(arglist, list):
        return [], []
    ps, ls, seen_slash = [], [], False
    for a in arglist:
        if a == "/":
            seen_slash = True
        elif isinstance(a, str):
            (ls if seen_slash else ps).append(a)
    return ps, ls


def analyse(src, builtins, exclude):
    defs = collections.defaultdict(list)       # name -> [ {file,line,kind,params,locals} ]
    calls = collections.defaultdict(set)       # caller -> callees (symbols in call position)
    refs = collections.defaultdict(set)        # caller -> symbols referenced by name
    loads = collections.defaultdict(list)      # file -> [loaded names]
    toplevel_calls = collections.defaultdict(set)
    problems = {}
    files = []
    for dp, dn, fn in os.walk(src):
        dn[:] = [d for d in dn if d != ".git" and os.path.relpath(os.path.join(dp, d), src) not in exclude]
        for f in sorted(fn):
            if not f.lower().endswith(".lsp"):
                continue
            path = os.path.join(dp, f)
            rel = os.path.relpath(path, src)
            files.append(rel)
            forms, probs = read(open(path, encoding="utf-8", errors="replace").read())
            if probs:
                problems[rel] = probs[:5]
            for form in forms:
                if isinstance(form, list) and form and form[0] in ("defun", "defun-q") and len(form) > 2 and isinstance(form[1], str):
                    name = form[1]
                    ps, ls = params_of(form[2])
                    defs[name].append({"file": rel, "line": getattr(form, "line", None),
                                       "kind": "command" if name.startswith("c:") else "function",
                                       "params": ps, "locals": ls,
                                       "body_hash": hashlib.sha1(repr(form[2:]).encode()).hexdigest()[:12]})
                    local = set(ps) | set(ls)
                    for body in form[3:]:
                        walk(body,
                             lambda s, line, n=name: calls[n].add(s),
                             lambda s, n=name: refs[n].add(s))
                    calls[name] -= local
                    continue
                walk(form, lambda s, line, r=rel: toplevel_calls[r].add(s), lambda s: None)
                if isinstance(form, list) and form and form[0] == "load" and len(form) > 1 and isinstance(form[1], Str):
                    loads[rel].append(form[1].value)

    internal = set(defs)
    def classify(sym):
        if sym in internal:
            return "internal"
        if sym in builtins or sym in SPECIAL or sym in SUPPLEMENT:
            return "builtin"
        return "unresolved"

    edges = {n: sorted(s for s in (calls[n] | (refs[n] & internal)) if classify(s) == "internal") for n in defs}
    unresolved = collections.Counter()
    unresolved_by = collections.defaultdict(set)
    for n in defs:
        for s in calls[n]:
            if classify(s) == "unresolved":
                unresolved[s] += 1
                unresolved_by[s].add(n)
    for r, syms in toplevel_calls.items():
        for s in syms:
            if classify(s) == "unresolved":
                unresolved[s] += 1
                unresolved_by[s].add("<top level of " + r + ">")

    def closure(start):
        seen, todo = set(), [start]
        while todo:
            n = todo.pop()
            for m in edges.get(n, []):
                if m not in seen:
                    seen.add(m); todo.append(m)
        return seen

    commands = {}
    for n, ds in defs.items():
        if not n.startswith("c:"):
            continue
        reach = closure(n)
        own_file = ds[0]["file"]
        other_files = sorted({d["file"] for m in reach for d in defs[m]} - {own_file})
        unres = sorted({s for m in reach | {n} for s in calls[m] if classify(s) == "unresolved"})
        commands[n] = {"file": own_file, "line": ds[0]["line"], "reaches": len(reach),
                       "depends_on_files": other_files, "unresolved": unres}

    used_by = collections.Counter()
    for n, es in edges.items():
        for m in es:
            used_by[m] += 1
    file_role = collections.Counter()
    for n, ds in defs.items():
        for d in ds:
            file_role[d["file"]] += used_by[n]

    duplicates = {n: {"identical": len({d["body_hash"] for d in ds}) == 1,
                      "at": [f'{d["file"]}:{d["line"]}' for d in ds]}
                  for n, ds in defs.items() if len(ds) > 1}
    return {
        "files": len(files),
        "definitions": {"commands": sum(1 for n in defs if n.startswith("c:")),
                        "functions": sum(1 for n in defs if not n.startswith("c:"))},
        "duplicates": duplicates,
        "unresolved": [{"symbol": s, "uses": c, "used_by": sorted(unresolved_by[s])[:5]} for s, c in unresolved.most_common()],
        "library_files": [{"file": f, "incoming_calls": c} for f, c in file_role.most_common(10) if c],
        "most_used_functions": [{"function": n, "callers": c, "defined_in": [d["file"] for d in defs[n]]} for n, c in used_by.most_common(15)],
        "loads": dict(loads),
        "commands": commands,
        "edges": edges,
        "definitions_detail": dict(defs),
        "parse_problems": problems,
    }


if __name__ == "__main__":
    args = sys.argv[1:]
    exclude = []
    while "--exclude" in args:
        i = args.index("--exclude"); exclude.append(args[i + 1]); del args[i:i + 2]
    src, bpath, out = args
    help_index = json.load(open(bpath, encoding="utf-8"))
    builtins = {k.lower() for k in help_index["functions"]} | {k.lower() for k in help_index.get("ambiguousFunctions", {})}
    result = analyse(src, builtins, set(exclude))
    result["source"] = src
    result["excluded"] = exclude
    json.dump(result, open(out, "w", encoding="utf-8"), indent=1, default=str)
    cmds = result["commands"]
    print(f'files {result["files"]}  commands {result["definitions"]["commands"]}  functions {result["definitions"]["functions"]}')
    diff = sum(1 for d in result["duplicates"].values() if not d["identical"])
    print(f'duplicate definitions {len(result["duplicates"])} (of which differing bodies {diff})  unresolved symbols {len(result["unresolved"])}')
    print(f'commands depending on other files {sum(1 for c in cmds.values() if c["depends_on_files"])} / {len(cmds)}')
    print(f'commands with unresolved calls {sum(1 for c in cmds.values() if c["unresolved"])} / {len(cmds)}')
