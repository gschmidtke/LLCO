; LLCO probe velisp-001 (2026-11-03): rule kernels re-expressed from civil-autolisp (MIT, 72d6813) for CIV-PIPE-01 and CIV-MS-01.
; Not the original routines. distance and rtos are MOCKS because VeLisp 0.8.0 lacks them.
(defun distance (a b) (sqrt (apply (quote +) (mapcar (quote (lambda (x y) (* (- x y) (- x y)))) a b)))) ; MOCK: velisp lacks distance; 3D like AutoLISP
(defun rtos (r mode prec / s) (setq s (vl-princ-to-string (/ (fix (+ (* r (expt 10.0 prec)) (if (minusp r) -0.5 0.5))) (expt 10.0 prec)))) s) ; MOCK: velisp lacks rtos; decimal only, no DIMZIN handling
(defun LM:Round ( n ) (fix (+ n (if (minusp n) -0.5 0.5))))
(defun gradient-label (p1 p2 il1 il2 / d)
  (setq d (distance p1 p2))
  (strcat (rtos d 2 1) "m @ 1/" (itoa (LM:Round (/ d (abs (- il2 il1)))))))
(defun chamber-size (dmax)   ; same comparisons as CIV-MS-01
  (cond ((< dmax 0.375) "DN1200")
        ((and (> dmax 0.375) (< dmax 0.700)) "DN1500")
        ((and (> dmax 0.700) (< dmax 0.900)) "DN1800")
        ((> dmax 0.9) "Consult Undertaker")))
(princ (gradient-label '(0.0 0.0) '(30.0 0.0) 10.0 9.8)) (princ "\n")
(princ (gradient-label '(0.0 0.0 0.0) '(30.0 0.0 5.0) 10.0 9.8)) (princ "\n")
(foreach d '(0.300 0.375 0.450 0.700 0.900 1.000)
  (princ (strcat (rtos d 2 3) " -> ")) (princ (chamber-size d)) (princ "\n"))
