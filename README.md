# Evidence-Traceable Credit Rating Decisions

This repository contains the **LaTeX manuscript, approved vector illustrations and synthetic computational evidence** for *Evidence-Traceable Credit Rating Decisions: A Reproducible Framework for Methodology Review*.

## Manuscript

- [Complete manuscript with tables and figures](manuscript/JFRC_Complete_Reading_Copy.pdf) — 19 pages.
- [Anonymous journal-layout manuscript](manuscript/JFRC_Anonymous_Manuscript.pdf) — 18 pages, with separate-table callouts.
- [LaTeX entry point](manuscript/main.tex), [complete reading source](manuscript/reading_copy.tex), and [build instructions](manuscript/README.txt).
- [Four approved MSVS V3 — Nordic Slate vector figures](manuscript/figures/), integrated on 18 November 2026.

Build the manuscripts with `bash manuscript/build.sh`. The exact approved bibliography is included.

## What is included

- `cases/`: 108 constructed decision-record variants (54 control/modified pairs).
- `data/case_design_grid.csv`: the 54-cell design grid.
- `scripts/methodology.py`: deterministic financial model and record validator.
- `scripts/results_audit.py`: archived finite-corpus calculations, perturbation audit and figure generation.
- `scripts/test_computational_study.py`: the original 12 computational tests.
- `scripts/verify_outputs.py`: consistency checks against archived results.
- `results/computational_audit/`: source-provided numerical and diagnostic outputs.
- `figures/`: the source-provided diagnostic ablation graphic.

## Reproduction

Requires Python 3 and the exact dependencies in `requirements.txt`.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
bash run_results_audit.sh
```

The supplied archived evaluation reports 216/216 financial outputs reproduced, 324/324 injected single-fault structural violations detected, and zero structural alerts on 54 unmodified controls and on 54 intentionally misleading-attribution controls. Suppressing each one of six balanced diagnostic families produces 270/324 detections (83.33%). The archived independent replication is separately supplied in the journal supplement.

**Research boundary:** The structural validator does not adjudicate whether the actual source passage semantically supports an analytical claim. This corpus does not measure human reviewer-accuracy effects. Results apply to the constructed cases and tested validator version.

## Provenance and scope

The source code, 108 cases and archived results are copied **without modifications** from the finalized computational supplement dated 17 November 2026. No new experiments were executed to assemble this repository. The computational supplement retained for journal submission remains the frozen reference version. The manuscript update on 18 November 2026 integrates four approved illustrations and their captions and references; the research calculations, case records and numerical outputs are unchanged.

No person-level reviewer records, editorial correspondence, author title page, or internal audit reports are present here.

## Licensing

No license is specified for this research release. An explicit license may be added by the research owner in a separate decision.

