#!/usr/bin/env python3
"""Fail-closed check of all numerical, structural, and figure audit outputs."""
import csv,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'results/computational_audit'
summary=json.loads((OUT/'summary.json').read_text())
expected={'design_cells':54,'canonical_variants':108,'financial_checks':216,
          'structural_faults':324,'full_validator_alerts':324,
          'metadata_only_alerts':54,'clean_control_alerts':0,
          'semantic_defect_structural_alerts':0,'ablation_alerts_each':270}
assert all(summary[k]==v for k,v in expected.items()),summary
assert float(summary['max_numerical_abs_error'])<=1e-9
for name,count in [('corpus_audit.csv',108),('numerical_recomputation.csv',108),
                   ('financial_branches.csv',9),('ablation_matrix.csv',48),
                   ('ablation_summary.csv',8),('mutation_diagnostics.csv',2592)]:
    with (OUT/name).open() as f:
        actual=sum(1 for _ in csv.DictReader(f))
    assert actual==count,(name,actual,count)
for path in [ROOT/'figures/fig03_diagnostic_ablation.pdf',
             ROOT/'figures/fig03_diagnostic_ablation.svg',
             OUT/'fig03_diagnostic_ablation.png']:
    assert path.is_file() and path.stat().st_size>1000,path
assert not list(ROOT.rglob('*fig04*')),'Obsolete figure 4 assets remain'
print('PASS: 54 cells, 108 variants, 216 numerical outputs, 324 structural perturbations, 54 clean controls, 54 semantic controls, six ablations, Figure 3')
