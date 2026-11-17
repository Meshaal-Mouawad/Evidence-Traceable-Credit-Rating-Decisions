# Evidence-Traceable Credit Rating Decisions — Reproducibility

This repository contains the **synthetic computational evidence** for *Evidence-Traceable Credit Rating Decisions: A Reproducible Framework for Methodology Review*.

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

The source code, 108 cases and archived results are copied **without modifications** from the finalized computational supplement dated 17 November 2026. No new experiments were executed to assemble this repository. The archive `Supplementary_1_Computational_Reproducibility.zip` submitted to the journal remains the frozen reference version.

No person-level reviewer records, editorial correspondence, author title page, or internal audit reports are present here.

## Licensing

No license is specified for this research release. An explicit license may be added by the research owner in a separate decision.
