# Findings: VeLisp calibrated against recorded AutoCAD runs (2026-11-03)

**Question:** how much real, cleanly licensed library code runs in VeLisp, and can VeLisp's results be trusted as a stand-in for AutoCAD on pure logic?

**Sources** (both MIT, no third-party marks, `corpus/MANIFEST.json`): [manualChair/commonlib](https://github.com/manualChair/commonlib) `79164a1` (209 files), [Jciel/cathedral](https://github.com/Jciel/cathedral) `6d593cb` (8 files). Runtime: VeLisp 0.8.0 (`77e5a95`), `--no-dcl`.

**Why commonlib is special:** its author documents functions with **Visual LISP console transcripts** from AutoCAD (`;;;_$ (call)` followed by the printed result). 560 such transcripts in 114 files are recorded runs in the original environment, made by the author: an independent oracle against which VeLisp can be checked, call by call.

Tools: `tools/velisp_examples.py` (replay transcripts), `tools/velisp_load_coverage.py` (load each file). Raw results in `results/2026-11-03-velisp-*.json`.

## 1. Can VeLisp read the code? (load coverage)

| Library | Files | Load | Parse error | Runtime error |
|---|---|---|---|---|
| commonlib | 209 | **178 (85 %)** | 23 | 8 |
| cathedral | 8 | **2** | 6 | 0 |

Parse errors come from a handful of VeLisp grammar gaps (valid AutoLISP that VeLisp rejects); one unreadable file blocks every file that includes it:

| Gap | Example | Effect |
|---|---|---|
| G1 quoting a special-form name | `(eval (list 'lambda …))` | commonlib `defstruct`, `compose`, `apply-partial`, `stack` |
| G2 dotted pair with a symbol in quoted data | `'((("AB" "ABK") . AB) …)` | commonlib ISO-639-1 table |
| G3 `?` and `\|` in symbol names | `even?`, `\|>` | 6 of 8 cathedral files |
| G4 other grammar rejections | character predicates (end-of-file), `_format-formatString` | commonlib `format` and its dependants |

One runtime workaround was applied to the temporary copy only: **W1**, `(defun f (/ a) …)` raises "too few arguments" in VeLisp unless a space follows `(`; 10 definitions were rewritten to `( / a)`, which is the same AutoLISP.

## 2. Does VeLisp give AutoCAD's answers? (560 transcripts)

| Outcome | Count | Meaning |
|---|---|---|
| **Same result as AutoCAD** | **147 (26 %)** | 144 exact, 3 equal within 1e-6 |
| Missing function | 282 | almost all the cascade from §1 (`format` 124, multi-byte predicates 103) |
| Arity error | 58 | `equal` with its optional tolerance argument (25) is not supported; others unexplained |
| Other runtime error | 43 | `apply`/`mapcar` with symbols naming library functions, `vl-symbol-value`, `set` on non-symbols |
| **Different result** | **21** | see §3 |
| Example not valid input | 9 | transcripts showing AutoCAD's printed forms (`#<…>`, `\|…\|`), not callable |

## 3. Where VeLisp gives a different answer

**D1 — `fix` on negative numbers.** VeLisp rounds down (`(fix -1.6)` → -2); AutoCAD truncates towards zero (-1). Proven by the transcripts: commonlib's `floor` gives -2 for -1.6 in AutoCAD, which requires `fix` → -1. All 9 numeric mismatches (`floor`, `ceiling`, `truncate`, `round-off`) follow from this one difference. **Every rounding helper built on `fix` is wrong for negative numbers in VeLisp**, including the widely copied `LM:Round` used in civil-autolisp. Probe velisp-001 used only positive values and is unaffected.

The other 12 mismatches concern strings typed as lists (`string-trim` with result type `LIST` returns an empty result), periodic indexing with negative indices, `mapl`, transforms; causes not yet traced.

## 4. What this means for LLCO

1. **A substitute runtime must be calibrated before its results count.** Without the transcripts, D1 would have produced wrong rule evidence silently. LLCO should keep a calibration suite (these 147 passing and 21 failing cases) and re-run it whenever VeLisp changes.
2. **VeLisp is usable for tier-1 evidence only where calibrated:** list, string and integer logic and non-negative arithmetic. Not for negative-number rounding (D1), `equal` with tolerance, or code that hits G1–G4.
3. **Recorded transcripts are the most valuable source material found so far.** They are exactly the baseline LLCO needs, produced by the original author in the original environment. Asking estate owners for console logs, test drawings or old outputs is cheaper than recreating a baseline.
4. Recovered-rule records that rely on a VeLisp probe must name the calibration status of every function the kernel uses.

## 5. Limits

- One VeLisp version; one transcript-bearing library. 26 % is a floor caused mostly by four grammar gaps, not by wrong results.
- Transcripts are source-reported runs: the AutoCAD version and settings behind them are unknown.
- Comparison is textual after whitespace normalisation, with a numeric tolerance; printing conventions that differ (e.g. real-number formatting) would show as mismatches.
- Example expressions and expected results quoted in `results/` come from commonlib (MIT, © 2020 manual chair japan).
