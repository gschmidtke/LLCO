# Static defect findings — caad4lisp geom.lisp / wallx.lisp / util.lisp (2026-11-03)

**Author:** Mis (DEVELOPER seat, DEC-006; Vibe / Mistral, GLM 5.3)
**Status:** DRAFT — for BAUMEISTER (LLCO technical lead) review
**Parent dispatch:** BPL `inbox/developer/2026-11-03-pm-llco-review-and-continuation-001.md` (PM-DEVELOPER-LLCO-2026-11-03-001)
**Source:** caadxyz/caad4lisp at pinned commit 393eaa7893bdbf307a3615573fe22a8c1e2b9412 (MANIFEST: MIT, `third_party_files: []`, status evaluation)

## Reading path and provenance

- `git` is unavailable in the authoring session; files were read from the codeload tarball of the pinned commit (`https://codeload.github.com/caadxyz/caad4lisp/tar.gz/393eaa7893bdbf307a3615573fe22a8c1e2b9412`), which is a snapshot of exactly that commit. No other revision was consulted.
- The tarball was byte-compared to nothing; the commit pin is the provenance guarantee.

## Correction to finding F1 of `2026-11-03-mis-llco-caad4lisp-kernels-001.md`

**F1 is withdrawn.** `src/geom.lisp`, `src/wallx.lisp` and `src/util.lisp` are **regular files** at the pinned commit, not symlinks. The earlier "not a valid internal symbolic link" GitHub-API errors were a connector artifact, not a property of the repository. Consequence: the Geom-EntmakeLines dependency in rule record C4L-WAL-01 is upgraded from "assumed from call name" to **read** (geom.lisp lines 76-95), and the corrected record in `rules/caad4lisp/wall-dline.json` cites it.

## Static defects and observations

Each item separates the **observed** code fact (static reading at the pinned commit) from the **suspected** runtime impact (needs an AutoCAD recorded run before it is asserted as behavior). Dispositions are reserved to the estate's acceptance authority; LLCO proposes none. `disposition` fields in rule records stay `null`.

**SD-1 — Geom-Line-IsPointOnLine copy-paste defect (geom.lisp 130-149).**
Observed: line 140 `(setq y (- (cadr p1) (cadr p1)))` and line 141 `(setq z (- (caddr p1) (caddr p1)))` — the subtrahend and minuend are the same expression; `y` and `z` are always 0. The author's own marker `;; todo: test` sits at line 128. Suspected: the on-line test degenerates — `(/ dy y)` divides by zero whenever `dy` is nonzero, and the earlier `(/ dx x)` divides by zero for vertical lines; the AutoCAD-side failure mode (error vs value) is unverified. The author's marker suggests the function was never exercised as written.

**SD-2 — Geom-Line-GetParamAtPoint dead check flag (geom.lisp 153-163).**
Observed: lines 155-157 `(if (= checkpoint 1) (Geom-Line-IsPointOnLine line point))` — the `if` has no else branch and its result is discarded; the function's return value comes from the subsequent `setq`/`/` forms (lines 158-162). Also the parameter computation uses x-coordinates only (line 160-161), and the formal parameter is spelled `checkPoint` while the body references `checkpoint` (same symbol in case-insensitive AutoLISP). Suspected: the `checkPoint` flag has no effect on output in any state; for a vertical line (equal x-coordinates) the x-based parameter divides by zero. Unverified at runtime.

**SD-3 — Debug call inside a pure interpolation function (geom.lisp 110-125; util.lisp 13-25).**
Observed: `Geom-Line-GetPointAtParam` calls `(Util-working)` (line 112) before computing; `Util-Working` prints a backspace via `(prompt "\010")`, `princ`-es one spinner character, and mutates the global `@Util-Working` rotation list (util.lisp 13-25). The interpolation body itself (lines 113-124) is pure list/arithmetic logic on `(point0 point1)` and a parameter in [0,1] (linear interpolation: `(1-param)*p0 + param*p1` per coordinate). This makes the kernel the cleanest VeLisp probe candidate in the estate: only `car`/`cadr`/`caddr`, `list`, `+`, `*`, `-` — all inside calibrated areas — once `Util-Working` is replaced by a named no-op mock.

**SD-4 — Util-Math-Odd? negative-input defect candidate (util.lisp 50-54).**
Observed: `(defun Util-Math-Odd? (number) ... (= (rem number 2) 1))`. AutoLISP `rem` is documented to return a remainder with the sign of the dividend, so `(rem -3 2)` is -1 and the predicate returns nil for negative odd numbers; non-integer reals (e.g. 2.5) also fall through (remainder 0.5 ≠ 1). Suspected defect on documented semantics — **not yet calibrated**: the VeLisp commonlib calibration contains no negative `rem` example (the one transcript `(rem -5 3)` parse-errored before evaluation; positive `rem` examples pass). Needs both an AutoCAD recorded run and a calibration data point before assertion. Related constants read in the same file: `Util-Math-Fuzz = 1.0e-6` (util.lisp 44, tolerance for equality; not applied in Util-Math-Odd?).

**SD-5 — Zero-argument call sites of Geom-Line-GetLineAngle (wall.lisp 24-25 vs geom.lisp 190-195).**
Observed: `Wall-CreateByEntLines` contains `(setq angle0 (Geom-Line-GetLineAngle) line0)` and `(setq angle1 (Geom-Line-GetLineAngle) line1)` — the function is called with zero arguments while its single `line` argument lands in the `setq` target position; the definition `(defun Geom-Line-GetLineAngle (line / p0 p1)` requires one argument. Suspected: the call errors in AutoCAD (too few arguments). Scope note: `Wall-CreateByEntLines` is not executed by `C:Wall-Dline` or `c:wallx`; `Wall-Flip`, `Wall-CreateByPoints`, `Wall-Intersected` are empty stubs (wall.lisp 39-49). No rule record is drafted from the stubs.

**SD-6 — Encoding note (all three files).**
Observed: `grep` treats `geom.lisp`, `wallx.lisp` and `util.lisp` as binary (mixed multi-byte content); `wallx.lisp` carries Chinese comments. Not a defect — a corpus-handling note: text tools must not assume UTF-8; the tarball read preserved bytes as committed. `wallx.lisp` is the wall-intersection cleanup command `c:wallx` (inner closures `neatx1`, `neatx2`, `sort`, `ssfunc`; uses `Command-Break` from `autolisp-comm.lisp`, the version-switching wrapper keyed on `Conf-AutoCAD-Version` 2015+ per readme). A rule record for wallx is deferred to the next selection; its `entget`/`command`/selection-set layer is outside calibrated VeLisp areas, so static reading with line pins is the bounded method for it.

**SD-7 — Author-embedded transcript comments (geom.lisp 203-210 and elsewhere).**
Observed: `%i:`/`%o:` console-style examples embedded as comments (e.g. `(angle '(1.0 1.0) '(1.0 4.0))` → `1.5708`). These are the author's recorded expectations, not LLCO evidence; they may serve as future calibration data with the same caveats as the commonlib transcripts (original AutoCAD version/settings unknown).

## Next small experiment (proposed)

`probes/velisp-002-caad4lisp-geom.lsp` (this branch) probes two extracted kernels under VeLisp 0.8.0 `--no-dcl`:

1. **Geom-Line-GetPointAtParam** (pure arithmetic; `Util-Working` replaced by a named no-op mock) — expected values computed by hand and stated in the file. Only calibrated function areas are used.
2. **Geom-Line-IsPointOnLine** with diagnostic prints — to show `y` and `z` arrive at 0 regardless of input (SD-1), independent of VeLisp's own uncalibrated division-by-zero behavior.
3. **Util-Math-Odd?** (renamed `Util-Math-Odd-P` in the temporary probe copy; `?` in names is VeLisp grammar gap G3, same temporary-copy discipline as W1) — with the expected-under-documented-AutoLISP column stated so VeLisp's `rem` on negatives becomes a calibration data point.

**Execution status: EXECUTION NOT VERIFIED by the author** — VeLisp 0.8.0 could not be installed in the authoring session (sandbox package installation unavailable); no substitute runtime was used. Run by BAUMEISTER with the calibrated runtime; record output under `results/`; evidence kind `interpreter_probe`, never raising any record to `confirmed_positive`.

— Mis, DEVELOPER seat, 2026-11-03
