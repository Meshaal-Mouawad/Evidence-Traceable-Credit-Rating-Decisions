#!/usr/bin/env python3
"""Executed finite-corpus numerical and structural audit for Figure 3 and Table 1."""
from __future__ import annotations
import copy
import csv
import hashlib
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from methodology import ROOT, family_numbers, make_case, validate_record

OUT=ROOT/'results/computational_audit'
FIG=ROOT/'figures'
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
CATEGORIES=['duplicate_statement_id','dangling_link','dependency_cycle',
            'post_cutoff_evidence','source_digest_mismatch','incomplete_decision_metadata']


def checksum(p:Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save_csv(name:str,rows:list[dict]):
    assert rows
    with (OUT/name).open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def save_json(name:str, data):
    (OUT/name).write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n')


def mutate(source, category):
    """One in-memory fault, unchanged from the original computational audit."""
    r=copy.deepcopy(source)
    evidence=next(s for s in r['statements'] if s['kind']=='evidence')
    if category=='duplicate_statement_id':r['statements'].append(copy.deepcopy(evidence))
    elif category=='dangling_link':r['asserted_links'].append(['J1','NONEXISTENT'])
    elif category=='dependency_cycle':r['asserted_links'].append(['C1','A1'])
    elif category=='post_cutoff_evidence':evidence['available_day']=r['cutoff']+1
    elif category=='source_digest_mismatch':evidence['text']+=' Altered after hashing.'
    elif category=='incomplete_decision_metadata':del r['decision_metadata']['owner']
    else:raise ValueError(category)
    return r


def generate_figure(matrix:list[dict]):
    configurations=['full']+['without_'+x for x in CATEGORIES]
    values=np.array([[next(r['detected']/r['total'] for r in matrix if r['fault']==f and r['configuration']==c)
                      for c in configurations] for f in CATEGORIES])
    row_labels=['Duplicate identifier','Dangling reference','Dependency cycle',
                'Post-cutoff evidence','Source text changed','Decision field missing']
    col_labels=['Full','No ID\ncheck','No\nreference\ncheck','No cycle\ncheck',
                'No cutoff\ncheck','No digest\ncheck','No\nmetadata\ncheck']
    fig,ax=plt.subplots(figsize=(8.6,4.5))
    ax.set_xlim(-.5,6.5);ax.set_ylim(5.5,-.5)
    for i in range(6):
        for j in range(7):
            ax.text(j,i,'54/54' if values[i,j] else '0/54',ha='center',va='center',fontsize=11,
                    fontweight='bold' if values[i,j]==0 else 'normal')
    ax.set_xticks(range(7),col_labels,fontsize=10)
    ax.xaxis.tick_top();ax.tick_params(axis='x',length=0,pad=12)
    ax.set_yticks(range(6),row_labels,fontsize=11);ax.tick_params(axis='y',length=0,pad=10)
    ax.set_xticks(np.arange(-.5,7,1),minor=True);ax.set_yticks(np.arange(-.5,6,1),minor=True)
    ax.grid(which='minor',linewidth=.5);ax.tick_params(which='minor',length=0)
    ax.set_xlabel('Alerts / controlled perturbations; each cell covers all 54 design cells',labelpad=16,fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG/'fig03_diagnostic_ablation.pdf',bbox_inches='tight')
    fig.savefig(FIG/'fig03_diagnostic_ablation.svg',bbox_inches='tight')
    fig.savefig(OUT/'fig03_diagnostic_ablation.png',dpi=160,bbox_inches='tight')
    plt.close(fig)


def main():
    rows=list(csv.DictReader((ROOT/'data/case_design_grid.csv').open()))
    assert len(rows)==54 and len({r['design_cell'] for r in rows})==54
    files=sorted((ROOT/'cases').glob('D*.json'))
    assert len(files)==108, f'Expected 108 canonical case records, found {len(files)}'
    manifest={str(p.relative_to(ROOT)):checksum(p) for p in
              files+[ROOT/'data/case_design_grid.csv',ROOT/'scripts/methodology.py']}
    records={p.stem:json.loads(p.read_text()) for p in files}
    expected_ids={r['design_cell']+suffix for r in rows for suffix in ('-C','-X')}
    assert set(records)==expected_ids
    metadata={}
    for r in rows:
        for defective in (False,True):
            rebuilt,key=make_case(r,defective)
            cid=rebuilt['case_id']
            assert rebuilt==records[cid], f'Input case differs from deterministic generation: {cid}'
            metadata[cid]=key
    numerical=[];corpus=[]
    for cid,case in sorted(records.items()):
        key=metadata[cid]
        baseline,candidate,_=family_numbers(key['family'],key['effect'])
        calc=next(s['text'] for s in case['statements'] if s['id']=='C1')
        parsed=re.search(r'baseline\s+(-?\d+(?:\.\d+)?)\s+and candidate\s+(-?\d+(?:\.\d+)?)',calc)
        assert parsed is not None, f'Missing recorded output: {cid}'
        stored_base,stored_candidate=map(Decimal,parsed.groups())
        computed_base,computed_candidate=map(Decimal,(baseline,candidate))
        diffb=abs(stored_base-computed_base)
        diffc=abs(stored_candidate-computed_candidate)
        assert diffb<=Decimal('1e-9') and diffc<=Decimal('1e-9'),cid
        numerical.append(dict(case_id=cid,family=key['family'],effect=key['effect'],
                              stored_baseline=str(stored_base),recomputed_baseline=str(computed_base),
                              stored_candidate=str(stored_candidate),recomputed_candidate=str(computed_candidate),
                              baseline_abs_error=str(diffb),candidate_abs_error=str(diffc)))
        diagnostics=validate_record(case)
        assert not diagnostics, (cid,diagnostics)
        corpus.append(dict(case_id=cid,design_cell=key['design_cell'],family=key['family'],
                           effect=key['effect'],methodological_status=key['status'],
                           evidence_state=key['evidence_state'],defective=key['defective'],
                           structural_diagnostics=';'.join(diagnostics)))
    controls={k:v for k,v in records.items() if k.endswith('-C')}
    semantic={k:v for k,v in records.items() if k.endswith('-X')}
    assert len(controls)==len(semantic)==54
    configs=['metadata_only','full']+['without_'+x for x in CATEGORIES]
    mutants=[];matrix=[]
    for cid,record in sorted(controls.items()):
        for fault in CATEGORIES:
            changed=mutate(record,fault)
            diagnostics=validate_record(changed)
            prefixes={x.split(':')[0] for x in diagnostics}
            assert prefixes=={fault},(cid,fault,diagnostics)
            for config in configs:
                disabled=config.removeprefix('without_') if config!='full' else None
                remaining=([d for d in diagnostics if d.split(':')[0]=='incomplete_decision_metadata']
                           if config=='metadata_only' else
                           [d for d in diagnostics if d.split(':')[0]!=disabled])
                mutants.append(dict(case_id=cid,fault=fault,configuration=config,
                                    alert=int(bool(remaining)),diagnostics=';'.join(diagnostics)))
    for fault in CATEGORIES:
        for config in configs:
            part=[r for r in mutants if r['fault']==fault and r['configuration']==config]
            matrix.append(dict(fault=fault,configuration=config,detected=sum(x['alert'] for x in part),total=len(part)))
    summaries=[]
    for config in configs:
        part=[r for r in mutants if r['configuration']==config]
        summaries.append(dict(configuration=config,detected=sum(x['alert'] for x in part),
                              structural_faults=len(part),detection_rate=sum(x['alert'] for x in part)/len(part),
                              control_alerts=sum(bool(validate_record(x)) for x in controls.values()),
                              control_n=len(controls),
                              semantic_defect_alerts=sum(bool(validate_record(x)) for x in semantic.values()),
                              semantic_defect_n=len(semantic)))
    oracle={('exposure_amount','favorable'):('0.8','0.48'),
            ('exposure_amount','adverse'):('0.8','1.12'),
            ('exposure_amount','unchanged'):('0.8','0.8'),
            ('refinancing','favorable'):('1.584','0.8'),
            ('refinancing','adverse'):('1.584','2.35232'),
            ('refinancing','unchanged'):('1.584','1.584'),
            ('sponsor_support','favorable'):('0','10'),
            ('sponsor_support','adverse'):('0','-10'),
            ('sponsor_support','unchanged'):('0','0')}
    branches=[]
    for (family,effect),(ob,oc) in oracle.items():
        b,c,_=family_numbers(family,effect)
        assert (Decimal(b),Decimal(c))==(Decimal(ob),Decimal(oc))
        delta=Decimal(c)-Decimal(b)
        branches.append(dict(family=family,effect=effect,baseline=b,candidate=c,
                             signed_difference=str(delta),
                             relative_change=None if Decimal(b)==0 else float(delta/Decimal(b)),
                             variants=sum(r['family']==family and r['effect']==effect for r in corpus)))
    assert len(numerical)==108 and len(mutants)==324*len(configs)
    assert next(x for x in summaries if x['configuration']=='full')['detected']==324
    assert next(x for x in summaries if x['configuration']=='metadata_only')['detected']==54
    assert all(x['detected']==270 for x in summaries if x['configuration'].startswith('without_'))
    for path,digest in manifest.items():
        assert checksum(ROOT/path)==digest, f'Input changed during audit: {path}'
    save_csv('corpus_audit.csv',corpus)
    save_csv('numerical_recomputation.csv',numerical)
    save_csv('financial_branches.csv',branches)
    save_csv('mutation_diagnostics.csv',mutants)
    save_csv('ablation_matrix.csv',matrix)
    save_csv('ablation_summary.csv',summaries)
    save_json('input_checksums.json',manifest)
    summary=dict(audit_type='exhaustive deterministic computational audit on fixed synthetic corpus',
                 design_cells=54,canonical_variants=len(records),financial_checks=2*len(numerical),
                 max_numerical_abs_error=str(max(Decimal(r[k]) for r in numerical for k in
                                           ('baseline_abs_error','candidate_abs_error'))),
                 structural_faults=324,full_validator_alerts=324,
                 metadata_only_alerts=54,clean_control_alerts=0,semantic_defect_structural_alerts=0,
                 ablation_alerts_each=270,ablation_coverage_each_percent=100*270/324,
                 configurations=summaries,environment={'python':sys.version.split()[0],
                                                       'numpy':np.__version__,
                                                       'matplotlib':matplotlib.__version__},
                 input_files=len(manifest))
    save_json('summary.json',summary)
    generate_figure(matrix)
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
