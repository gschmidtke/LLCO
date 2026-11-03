# Probes

Small programs that test a **recovered rule kernel** outside AutoCAD. A probe shows how the logic as LLCO extracted it behaves; it does **not** show how the original routine behaves in AutoCAD. Probe results are recorded with evidence kind `interpreter_probe` and never raise a rule to `confirmed_positive`.

## Runtime: VeLisp

[ten0s/velisp](https://github.com/ten0s/velisp) 0.8.0 (GPL-3.0-or-later), run with `--no-dcl`, installed with only its non-GUI dependencies (`antlr4`, `commander`, `temp`). Not stored here.

What VeLisp 0.8.0 can and cannot run (from its function list, checked 2026-11-03, and the probe below):

| Area | Status |
|---|---|
| Arithmetic, lists, strings, symbols, `defun`, `cond`, `foreach`, `mapcar` | Runs |
| File I/O (`open`, `read-line`, `write-line`, `vl-file-*`) | Runs |
| DCL dialogs | Runs (needs GTK; not used here) |
| Geometry: `distance`, `angle`, `polar`, `inters` | **Not implemented** ("expected") |
| Number formatting `rtos`, `terpri` | **Not implemented** |
| `vl-catch-all-apply`, `initget`, `getkword`, `setvar` | **Not implemented** ("expected") |
| Drawing database: `entget`, `entmake`, `entmod`, `ssget`, `tblsearch`, `command`, `getpoint` | **Not available** |
| Visual LISP COM (`vla-`, `vlax-`), reactors | **Not available** |

So VeLisp can test pure logic (calculations, tables, string building, library functions) once drawing access is cut away or mocked. Every mock is named in the probe.

## velisp-001: civil kernels

`velisp-001-civil-kernels.lsp`, output in `../results/2026-11-03-velisp-001.txt`.

| Kernel | Inputs | Output | Meaning |
|---|---|---|---|
| CIV-MS-01 chamber size | 0.300 / 0.450 / 1.000 m | DN1200 / DN1500 / Consult Undertaker | as read |
| CIV-MS-01 chamber size | **0.375 / 0.700 / 0.900 m** | **nil** | the suspected boundary gap reproduces in the extracted logic |
| CIV-PIPE-01 gradient | 30 m plan, fall 0.2 m | 1/150 | — |
| same, with 5 m Z difference between the two points | | 1/152 | 3D distance gives a different gradient than plan distance (CIV-INT-01) |
