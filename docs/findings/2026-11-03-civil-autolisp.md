# Findings: civil-autolisp, step 2 (2026-11-03)

Source: [dtgoitia/civil-autolisp](https://github.com/dtgoitia/civil-autolisp) at `72d6813` (MIT), a civil engineering estate its author used daily at work. Main estate = all files outside `Dump folder/` (downloaded and untested routines, analysed separately). Everything below comes from reading the code; nothing has been run, so every rule is `insufficient`.

Tools: `tools/llco_structure.py` (parser-based, `results/2026-11-03-structure-civil-autolisp.json`), rule records in `rules/civil-autolisp/` against `schema/rule-record.schema.json`.

## 1. Structure

| Measure | Value |
|---|---|
| Files (main estate) | 48 |
| Commands / functions | 227 / 256 |
| Commands that need code from another file | 141 (62 %) |
| Commands needing 2 or more other files | 31 |
| Shared library files (incoming calls) | `0 - Function library.lsp` (285), `_PersonalLibrary.lsp` (172), `CIVIL - Load blocks.lsp` (57) |
| Most used function | `LM:rtos` (47 callers) |

**A per-file conversion would break most commands**: 62 % of them do not work without the library files.

## 2. Hidden dependencies

| Finding | Count | Why it matters |
|---|---|---|
| Functions defined more than once | 19 | Behaviour depends on load order |
| … of which with **different** bodies | 12 | e.g. `get_il_manhole` (pipe vs dynamic manholes), `dt:clic_or_type_level` (two libraries), `get_block_att` (twice in the same library file: the second silently wins) |
| Called symbols not defined anywhere in the repository | 43 | External toolkits (e.g. `c:ktf_*`), or code that was never committed (`dt:getsegment`, `undobegin`/`undoend`, …) |
| Called symbols defined only in `Dump folder/` | 12 | The working estate depends on routines its author filed as untested (manhole schedule diagrams, linear drainage, cut-and-fill strings) |

Commands with unresolved calls: 29 of 227. Built-ins were identified with Autodesk's AutoLispExt help index (2,565 functions) plus a small supplement of undocumented functions (`tools/llco_structure.py`, `SUPPLEMENT`).

## 3. First rule records (13, four routines)

| Routine | Records | Targets |
|---|---|---|
| House polylines (`c:hs`) | CIV-HS-01…03 | variation switching (house 0.302 m / garage 0.215 m), geometry, documentation |
| Draw single pipe (`c:pipe`) | CIV-PIPE-01…05 | geometry (gradient, same-system rule, invert level), documentation (label), unresolved (planned 1/150 check) |
| Manhole schedule (`c:mscs`) | CIV-MS-01…04 | BOM preparation (chamber size, depth to soffit, manhole type), housekeeping (text parsing) |
| Interpolate level (`c:int`) | CIV-INT-01 | geometry (gradient between points) |

## 4. Suspected legacy defects (for the estate owner's disposition, not fixed)

1. **CIV-MS-01** — pipes of exactly 375, 700 or 900 mm fall between the chamber-size bands; the size is left unchanged.
2. **CIV-PIPE-04** — an invert level of 0.000 counts as missing; non-contiguous levels leave the previous manhole's level in use.
3. **CIV-MS-04** — diameters not written as `DN<mm>` read as 0 without warning.
4. **CIV-PIPE-03** — text box width jumps from 1 to 2 below about 2.2 m pipe length.

## 5. Conflict between routines

**CIV-PIPE-01 vs CIV-INT-01**: both compute a gradient, one from block insertion points (which may carry Z), the other from flattened points. If manhole blocks are inserted at different Z, the same pipe gets two gradients. Needs a recorded run and a ruling (plan or true length).

## 6. What step 4 (proof) needs

All four routines use Visual LISP COM (6–20 calls each) and interactive input. They cannot run in the AutoCAD Core Console or in a LISP interpreter outside AutoCAD. Recording them needs **desktop AutoCAD** driven by a bridge, with scripted answers to the prompts.

## 7. Limits of this pass

- Static reading by one reviewer (Claude); no recorded runs; no domain review yet.
- Authorities are claims, mostly `unknown` or inferred (e.g. UK adoption standards); none is verified.
- The structure tool is a first parser: dynamic calls (`eval`, symbols built at runtime) are not resolved.
