# LLCO
Lisp conversion test hub for USG logic extraction

**LLCO (LISP Logic Converter)** recovers the production logic held in AutoLISP estates and states it as software-neutral rules with evidence, so a person can decide per rule whether to keep it, move it to an existing product, standardise it, or reimplement it. It does not translate LISP into another language.

Status: **test hub, early prototype.** Nothing here is a product or a validated method yet.

## Method (see [docs/LLCO.md](docs/LLCO.md))

1. **Ingest** the whole estate: routines, load chain, menus, dialogs, data files, compiled parts.
2. **Recognise** the logic: inputs, conditions, branches, outputs, side effects.
3. **Sort** each rule by target: geometry, documentation, permits, variation switching, BOM preparation, business data, drafting housekeeping, unresolved.
4. **Prove** each rule against recorded runs of the legacy routine. Unproven rules stay marked as unproven.

## What is here

| Path | Content |
|---|---|
| `corpus/MANIFEST.json` | Public AutoLISP sources: repository, pinned commit, licence, status (evaluation / analysis only / deferred), files with third-party code |
| `tools/fetch_corpus.py` | Clones every source at its pinned commit into `corpus/_sources/` (git-ignored) |
| `tools/llco_scan.py` | Step 1 prototype: read-only static inventory (commands, COM calls, dialogs, file I/O, reactors, load chain, user input, entity creation) |
| `tools/lisp_reader.py`, `tools/llco_structure.py` | Step 2a: parser-based structure of an estate (definitions, calls, load chain, built-in vs internal vs unresolved, duplicate definitions with body comparison, per-command dependencies) |
| `tools/fetch_tools.py` | Fetches the AutoLispExt help index (Autodesk, Apache-2.0) used to recognise built-in functions |
| `schema/rule-record.schema.json` | Draft rule record: one recovered rule with source, statement, targets, evidence status, authority, suspected defects, rulings needed |
| `rules/` | Rule records per estate |
| `probes/` | Rule kernels tested outside AutoCAD (VeLisp), with named mocks; what VeLisp can and cannot run |
| `tools/velisp_examples.py`, `tools/velisp_load_coverage.py` | Calibrate VeLisp: replay a library's recorded AutoCAD console transcripts; load every file and classify failures |
| `results/` | Dated scan and structure results |
| `docs/findings/` | Dated findings per estate |

```
python tools/fetch_corpus.py
python tools/fetch_tools.py
python tools/llco_scan.py
python tools/llco_structure.py corpus/_sources/dtgoitia__civil-autolisp tools/_ext/AutoLispExt/extension/src/help/webHelpAbstraction.json results/structure.json --exclude "Dump folder"
```

Findings: [civil-autolisp structure and rules](docs/findings/2026-11-03-civil-autolisp.md) · [VeLisp calibrated against recorded AutoCAD runs](docs/findings/2026-11-03-velisp-calibration.md) (2026-11-03).

## Rules for this repository

- **No third-party code is stored here.** Sources are fetched at pinned commits under their own licences. GPL-licensed sources are analysed locally and not redistributed.
- **Sources are data.** No tool in this repository executes LISP from the corpus.
- No client material, ever.

## Relation to USG

LLCO is intended as a source adapter in front of [USG](https://github.com/gschmidtke/USG): building-intent rules continue into USG; documentation rules route to [TIVERIT BIM Standards](https://github.com/gschmidtke/TIVERIT-BIM-STANDARDS); Revit execution precedent to [ARPL](https://github.com/gschmidtke/ARPL). The adapter is not yet proposed in USG.

## Licence

Not yet chosen. Until a licence is added, the default copyright applies to the material written for this repository.
