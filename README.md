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
| `corpus/MANIFEST.json` | Public AutoLISP sources used for testing: repository, pinned commit, licence, why it is included |
| `tools/fetch_corpus.py` | Clones every source at its pinned commit into `corpus/_sources/` (git-ignored) |
| `tools/llco_scan.py` | Step 1 prototype: read-only static inventory (commands, COM calls, dialogs, file I/O, reactors, load chain, user input, entity creation) |
| `results/` | Dated scan results |

```
python tools/fetch_corpus.py
python tools/llco_scan.py
```

## Rules for this repository

- **No third-party code is stored here.** Sources are fetched at pinned commits under their own licences. GPL-licensed sources are analysed locally and not redistributed.
- **Sources are data.** No tool in this repository executes LISP from the corpus.
- No client material, ever.

## Relation to USG

LLCO is intended as a source adapter in front of [USG](https://github.com/gschmidtke/USG): building-intent rules continue into USG; documentation rules route to [TIVERIT BIM Standards](https://github.com/gschmidtke/TIVERIT-BIM-STANDARDS); Revit execution precedent to [ARPL](https://github.com/gschmidtke/ARPL). The adapter is not yet proposed in USG.

## Licence

Not yet chosen. Until a licence is added, the default copyright applies to the material written for this repository.
