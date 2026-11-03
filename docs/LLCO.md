# LLCO method (draft)

## Purpose

An AutoLISP estate often holds decades of a firm's production rules: how options change a plan, how framing is laid out, what goes on which sheet. The rules live in code few people still read. LLCO makes those rules visible, testable and portable without assuming that the code must be translated.

## Steps and evidence

| Step | Output | Evidence status of a rule |
|---|---|---|
| 1 Ingest | Inventory of files, load chain, menus, dialogs, data, compiled parts | — |
| 2 Recognise | Candidate rules per routine (deterministic analysis first, AI-drafted statements second) | `insufficient` |
| 3 Sort | Target per rule (table below) | unchanged |
| 4 Prove | Recorded runs on fixed inputs; output compared with the rule's claim | `confirmed_positive`, `conflicting` or still `insufficient` |

Evidence statuses follow USG's evidence model. A rule read from code alone never counts as confirmed.

## Sorting targets

| Target | Typical content | Continues to |
|---|---|---|
| Geometry | Walls, openings, framing, placement rules | USG (building intent), then Revit via ARPL |
| Documentation | Sheets, views, title blocks, annotation, naming | TIVERIT BIM Standards |
| Permits | Required content of a permit set | External permit process |
| Variation switching | Options, compatibility, what changes with a choice | Exchange contract (configuration payload) |
| BOM preparation | Quantities, part identity, waste, assemblies | BOM standard, then business systems |
| Business data | Prices, suppliers, ERP fields | External systems |
| Drafting housekeeping | Layers, text placement, plotting | Usually retired: the target platform does it natively |
| Unresolved | Unclear purpose or no owner | Gap list for the estate owner |

## Known limits

- Static analysis in `tools/llco_scan.py` is regex-based triage, not a parser.
- Code using Visual LISP COM (`vla-`, `vlax-`) cannot run in the headless AutoCAD Core Console; recording such routines needs desktop AutoCAD.
- Compiled `.fas` / `.vlx` files are reported as unreadable inputs, never decompiled.

## Related public work (not used here yet)

- Autodesk Platform Services `aps-lisp-dotnet-skill`: per-file AutoLISP to .NET migration for Design Automation. No licence file at the time of review (2026-11-03).
- Autodesk `AutoLispExt` (Apache-2.0): VS Code extension with an AutoLISP parser; candidate for step 2.
- `ten0s/velisp` (GPL-3.0): AutoLISP interpreter with DCL support outside AutoCAD; candidate for recording basic (non-COM) routines in step 4.
