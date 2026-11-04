# Goal Record schema v0.1 — notes, mapping and limitations

Dispatch: PM-DEVELOPER-LLCO-GOAL-SCHEMA-2026-11-03-001 (P1, REQUESTED).
Direction: USG `docs/proposals/legacy-automation-purpose-recovery.md` (adopted
at USG main commit 8d07d26, LOG-0023). This file documents what
`schema/goal-record.schema.json` encodes, how it maps to USG concepts, how it
was validated, and what it deliberately does not do.

## 1. What a Goal Record is

One recovered production goal from a legacy automation estate: three separate
claims (behaviour / purpose / correctness), its concern classification, the
choices it embeds, its required outputs, and its coverage items. **Adapter-local
to LLCO** per the adopted direction: fields stay in LLCO until a second adapter
needs them; everything handed to USG maps to existing USG concepts.

Naming: `LLCO-GR-<estate>-<NNNN>` (e.g. `LLCO-GR-caad4lisp-0001`). Stable, never
reused. Two record kinds, kept apart at the schema level:

- `recovered` — grounded in an observed estate at a pinned commit (requires
  `source`).
- `hypothetical` — invented illustration, never evidence of a real firm
  (requires `hypothetical_notice`; the shipped example prefixes all invented
  content with `[HYPOTHETICAL]`).

## 2. Mapping to USG concepts (per the proposal's mapping table)

| Goal Record field (LLCO) | USG concept |
| --- | --- |
| `claims.behaviour` | `statement_model` claim (behaviour) |
| `claims.purpose` | `statement_model` claim (purpose); candidate basis `ai_generated` until ruled |
| `claims.correctness` | `statement_model` claim (correctness); regulated content → `professional_review` |
| `claims.*.status` | `evidence_model.claim_status_rule` (insufficient / confirmed_positive / confirmed_negative / conflicting) |
| `evidence[]` kinds | LLCO rule-record kinds (static_reading, interpreter_probe, recorded_run, human_ruling, source_comment) + goal-side additions (historical_output, governing_document, owner_statement) |
| `authority` (basis/relaxable_by) | `statement_model.basis` (stakeholder_choice, legal, preference, assumption, open) |
| `concerns[].concern` | `statement_model.concerns` (outcome, condition, means); `means_reason` is an adapter-local refinement, no protocol field |
| `choices[]` | `rule_model` (choice space; scopes object_rule vs catalogue_availability) |
| `pending_user` | `pending_user` gate (high-materiality open items block binding output) |
| `coverage[]` | dispositions per LOG-0023: native_coverage / external_system / retained_legacy / reimplement / retire / uncovered_gap / undecided |
| `reconciliation[]` | coverage-based readiness (reconciled historical case + second-runner re-run) |
| promotion gate | NOT in schema — remains human: rights-cleared real estate (KANZLER / Owner) |

**Link direction (LOG-0023):** many-to-many held on the goal side. Goal records
carry `related_rule_records` and per-item `coverage.ref` back-references; rule
records get **no mandatory goal field** (optional derived back-references only).

## 3. Design decisions encoded as schema constraints

- `record_kind: recovered` ⇒ `source` required; `hypothetical` ⇒
  `hypothetical_notice` required (top-level `if/then`).
- `purpose.status: confirmed_positive` ⇒ `evidence` required AND must
  `contain` an item with `kind: human_ruling`. This is the human-authority
  rule in machine-checkable form: matching outputs never confirm purpose.
- `concern: means` ⇒ `means_reason` required (platform_mechanism / era_constraint
  / unknown) — means do not descend as requirements.
- `disposition: native_coverage` ⇒ `coverage_kind` (native / configured /
  scripted / product_extension), `evidence` and `reason` required; `retire` and
  `undecided` ⇒ `reason` required. `undecided` blocks binding output that
  depends on it; `uncovered_gap` is never silent.
- `evidence_item.kind: owner_statement` ⇒ `confidence` capped at low/medium
  (owner statements never reach high — USG owner_statement and
  reviewer_independence rules).
- `additionalProperties: false` everywhere — records are closed structs, so a
  mis-typed field fails validation instead of being silently ignored.

## 4. Validation

Commands (run 2026-11-04, Mis, sandbox: python3 stdlib only):

```
python3 tools/validate_goal_record.py --selftest .
python3 tools/validate_goal_record.py schema/goal-record.schema.json FILE...
```

Results:

- `c4l-wal-01.json` — PASS
- `option-bom-hypothetical.json` — PASS
- all 7 invalid fixtures — FAIL as expected, each with the expected marker:
  01 `coverage` (missing), 02 `human_ruling` (purpose confirmed without
  ruling), 03 `coverage_kind` (native_coverage without kind), 04 `source`
  (recovered without pin), 05 `hypothetical_notice` (hypothetical without
  notice), 06 `means_reason` (means without reason), 07 `goal_id` (bad id
  pattern). Selftest summary: 2 valid, 7 invalid, 0 test failures, exit 0.

`tools/validate_goal_record.py` is a **stdlib-only subset validator** (the
environment has no `jsonschema` package and pip installation is blocked). It
supports exactly the keywords used by the schema ($ref local, type incl.
lists, enum, const, pattern, properties, required, additionalProperties:false,
items, minItems, contains, allOf, if/then/else, $defs). It is NOT a JSON
Schema implementation; unknown keywords are ignored. Replace with the
`jsonschema` package when available. The selftest checks that each invalid
fixture fails AND that the expected marker appears in the violation output; it
does not assert the absence of additional violations.

## 5. The two fixtures

- `fixtures/goal-record/c4l-wal-01.json` — real, evidence-limited: the
  double-line wall goal behind rule record C4L-WAL-01 (caad4lisp @ 393eaa7,
  src/wall.lisp 60-173). Both coverage items are deliberately `undecided`
  with reasons: candidate native coverage is **not claimed** (no versioned
  evidence, no process owner to rule purpose, no successor selected). Claims
  are all `insufficient` — static readings and source comments only.
- `fixtures/goal-record/option-bom-hypothetical.json` — explicitly
  hypothetical option→BOM illustration exercising choices (two scopes),
  cross_output_consistency with read_back, reconciliation (pending case),
  and all four coverage shapes (undecided, retire, uncovered_gap, plus a
  governing_document evidence item marked illustrative-pointer-only).

## 6. Limitations and open issues

- No recorded runs exist for any caad4lisp kernel; every evidence item in
  fixture 1 is static reading or source comment. Probe `velisp-002`
  (geom.lisp) is pushed but **execution unverified**; it covers geom.lisp
  kernels, not wall.lisp.
- caad4lisp is a public development-alpha library with **no named process
  owner**; its purpose claims cannot be confirmed under the human-authority
  rule, now or later, without an authorized ruling.
- The hypothetical fixture is invented; it is schema-shape evidence only and
  must never be cited as evidence of any real firm.
- No real qualifying estate exists yet; schema is draft 0.1, adapter-local,
  subject to independent review (self-review insufficient per PM correction).
- Draft LLCO PR #1 (rule records, branch `mis-caad4lisp-records-2026-11-03` @
  817b019) remains open/draft/unmerged; this PR builds on its C4L-WAL-01
  record but does not modify it.

## 7. Dependency links

- USG direction: `docs/proposals/legacy-automation-purpose-recovery.md` @ USG
  main 8d07d26, LOG-0023 (adopted, incl. ten PM corrections).
- PM dispatch: PM-DEVELOPER-LLCO-GOAL-SCHEMA-2026-11-03-001.
- Rule record: C4L-WAL-01 @ LLCO branch `mis-caad4lisp-records-2026-11-03`,
  commit 817b019 (draft PR #1).
- Corpus pin: caad4lisp @ 393eaa7893bdbf307a3615573fe22a8c1e2b9412 (MIT),
  corpus status: evaluation.
