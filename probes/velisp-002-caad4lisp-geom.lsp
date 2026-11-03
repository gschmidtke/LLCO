;;; velisp-002 — caad4lisp extracted kernels, probe (NOT EXECUTED BY AUTHOR)
;;; Source: caadxyz/caad4lisp @ 393eaa7893bdbf307a3615573fe22a8c1e2b9412
;;; Probe per probes/README.md: extracted logic run outside AutoCAD.
;;; Evidence kind: interpreter_probe. NEVER raises a rule to confirmed.
;;; Runtime: VeLisp 0.8.0, run with --no-dcl (BAUMEISTER's calibrated runtime).
;;; EXECUTION STATUS: EXECUTION NOT VERIFIED — authoring session could not
;;; install VeLisp (sandbox package installation unavailable). No substitute
;;; runtime was used. Expected values below are hand-computed from the code.
;;;
;;; Named mocks and temporary-copy rewrites (all documented, none silent):
;;;   - Util-Working  -> no-op (original: util.lisp 13-25, debug spinner:
;;;     prompt "\010" + princ + global @Util-Working rotation). Mocked to
;;;     keep probe output clean; mock is named at the call site too.
;;;   - Util-Math-Odd? -> renamed Util-Math-Odd-P in this temporary copy
;;;     ("?" in names is VeLisp grammar gap G3; same temporary-copy
;;;     discipline as W1). Logic untouched.
;;;
;;; Calibrated-function rule: probe uses only car/cadr/caddr/list/+/*/-/=,
;;; princ, and defun — all inside calibrated areas (arithmetic/lists/strings;
;;; see results/2026-11-03-velisp-commonlib-transcripts.json pass classes and
;;; probes/README.md). No geometry (polar/angle/inters/distance), no drawing
;;; database, no command/getvar.

;; ---------- kernel 1: Geom-Line-GetPointAtParam (geom.lisp 110-125) ----------

;; MOCK (named): replaces debug spinner Util-Working
(defun Util-Working () nil)

(defun Geom-Line-GetPointAtParam (line param / p0 p1)
  "get a point at parament from a line"
  (Util-Working) ; original call retained; mock named above
  (setq p0 (car line))
  (setq p1 (cadr line))
  (list (+ (* (- 1 param) (car p0))
           (* param (car p1))
           )
        (+ (* (- 1 param) (cadr p0))
           (* param (cadr p1)))
        (+ (* (- 1 param) (caddr p0))
           (* param (caddr p1)))
        )
  )

;; line ((0 0 0) (10 20 30)); param 0 -> startpoint
(princ "\nK1 param 0  -> ") (princ (Geom-Line-GetPointAtParam '((0 0 0) (10 20 30)) 0))
(princ " | expected (0 0 0)")
;; param 1 -> endpoint
(princ "\nK1 param 1  -> ") (princ (Geom-Line-GetPointAtParam '((0 0 0) (10 20 30)) 1))
(princ " | expected (10 20 30)")
;; param 0.5 -> midpoint (hand-computed: (1-0.5)*0 + 0.5*10 = 5 etc.)
(princ "\nK1 param 0.5-> ") (princ (Geom-Line-GetPointAtParam '((0 0 0) (10 20 30)) 0.5))
(princ " | expected (5.0 10.0 15.0)")
;; param 0.25 -> quarter point
(princ "\nK1 param 0.25-> ") (princ (Geom-Line-GetPointAtParam '((0 0 0) (10 20 30)) 0.25))
(princ " | expected (2.5 5.0 7.5)")
;; nonzero origin: ((1 2 3) (11 22 33)), param 0.5
(princ "\nK1 param 0.5 origin-> ") (princ (Geom-Line-GetPointAtParam '((1 2 3) (11 22 33)) 0.5))
(princ " | expected (6.0 12.0 18.0)")

;; ---------- kernel 2: Geom-Line-IsPointOnLine (geom.lisp 130-149) ----------
;; Verbatim body plus diagnostic prints (prints added by the probe; the
;; division itself is NOT asserted on, because VeLisp's division-by-zero
;; behavior is uncalibrated — the point of this kernel is to show that
;; y and z are ALWAYS 0 regardless of input (SD-1 in
;; docs/findings/2026-11-03-caad4lisp-static-defects.md).

(defun Geom-Line-IsPointOnLine (line point / dx dy dz x y z p0 p1)
  "check a point on a line or not."
  (setq p0 (car line))
  (setq p1 (cadr line))
  (setq dx (- (car point) (car p0)))
  (setq dy (- (cadr point) (cadr p0)))
  (setq dz (- (caddr point) (caddr p0)))
  (setq x (- (car p1) (car p0)))
  (setq y (- (cadr p1) (cadr p1)))   ; verbatim defect (geom.lisp 140)
  (setq z (- (caddr p1) (caddr p1))) ; verbatim defect (geom.lisp 141)
  (princ "\nK2 diag dx dy dz x y z -> ")
  (princ (list dx dy dz x y z))
  (princ " | y and z expected 0 for EVERY input (copy-paste defect)")
  (if (and (= (/ dx x) (/ dy y))
           (= (/ dx x) (/ dz z))
           )
      (/ dx x)
      nil
      )
  )

(princ "\nK2 mid     -> ") (princ (Geom-Line-IsPointOnLine '((0 0 0) (10 10 10)) '(5 5 5)))
(princ " | x=10 y=0 z=0 at the divisions: degenerate (division by zero or error expected in any faithful runtime; AutoCAD failure mode needs a recorded run)")
(princ "\nK2 off     -> ") (princ (Geom-Line-IsPointOnLine '((0 0 0) (10 10 10)) '(5 5 9)))
(princ " | same degenerate divisions; note dz arrives nonzero but divides by z=0")
(princ "\nK2 vertical-> ") (princ (Geom-Line-IsPointOnLine '((0 0 0) (0 10 0)) '(0 5 0)))
(princ " | x=0 as well: dx/x division by zero in the FIRST comparison (independent of the copy-paste defect)")

;; ---------- kernel 3: Util-Math-Odd? (util.lisp 50-54) ----------
;; RENAMED in temporary copy: Util-Math-Odd-P (VeLisp G3 "?" gap).
;; Logic verbatim: (= (rem number 2) 1).
;; Column A = expected under documented AutoLISP rem semantics (remainder
;; takes the sign of the dividend): (rem -3 2) = -1 => predicate nil.
;; Column B = whatever VeLisp returns; a VeLisp/AutoCAD difference here is an
;; INTERPRETER DIFFERENCE (calibration data point), not rule evidence.
;; The negative-rem case is uncalibrated: the commonlib transcript example
;; (rem -5 3) parse-errored before evaluation.

(defun Util-Math-Odd-P (number)
  "check a numer is odd or not?"
  (= (rem number 2) 1)
  )

(princ "\nK3 odd(3)     -> ") (princ (Util-Math-Odd-P 3))
(princ " | expected T in both AutoLISP and VeLisp (calibrated: positive rem passes)")
(princ "\nK3 odd(4)     -> ") (princ (Util-Math-Odd-P 4))
(princ " | expected nil")
(princ "\nK3 odd(-3)    -> ") (princ (Util-Math-Odd-P -3))
(princ " | expected NIL under documented AutoLISP rem (-1 /= 1) — suspected estate defect SD-4; VeLisp value recorded as calibration data point only")
(princ "\nK3 odd(-4)    -> ") (princ (Util-Math-Odd-P -4))
(princ " | expected nil")
(princ "\nK3 odd(2.5)   -> ") (princ (Util-Math-Odd-P 2.5))
(princ " | expected nil (remainder 0.5); non-integer input falls through")

(princ "\nvelisp-002 end\n")
