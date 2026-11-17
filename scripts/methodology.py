#!/usr/bin/env python3
"""Synthetic credit-case construction, financial arithmetic, and structural validation."""
from __future__ import annotations
import hashlib, json, random, re
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
D = Decimal
FIELDS = ['source_id','methodology','assumption','boundary','cutoff_version',
          'baseline','candidate','condition','classification','disposition']

def write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False)+'\n')

def digest(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def loss(exposure: list[str], q: list[str], lgd: list[str], h: list[str],
         discount: list[str]) -> Decimal:
    """Default occurs within a period; conditional termination follows at period end."""
    n = len(exposure)
    if not n or any(len(x) != n for x in (q,lgd,h,discount)):
        raise ValueError('Nonempty, equally sized vectors required')
    with localcontext() as ctx:
        ctx.prec = 28
        alive, out = D(1), D(0)
        for raw in zip(exposure,q,lgd,h,discount):
            e,p,l,t,d = map(D,raw)
            if not all(x.is_finite() for x in (e,p,l,t,d)):
                raise ValueError('Finite numeric values required')
            if e < 0 or d <= 0 or not all(0 <= x <= 1 for x in (p,l,t)):
                raise ValueError('Invalid financial input or probability')
            out += d * alive * p * l * e
            alive *= (1-p)*(1-t)
        return +out

def cash_flow(operating: str, reserve: str, debt: str,
              supports: list[dict[str,Any]], due: int = 0) -> dict[str,str]:
    """Single payment; unknown eligibility requires an explicit alternative scenario."""
    c,r,d = map(D,(operating,reserve,debt))
    if any(not x.is_finite() or x < 0 for x in (c,r,d)):
        raise ValueError('Finite nonnegative amounts required')
    ids = [x['id'] for x in supports]
    if len(ids)!=len(set(ids)):
        raise ValueError('A support transfer may be counted only once')
    total = c+r
    for x in supports:
        value=D(x['amount'])
        if not value.is_finite() or value < 0: raise ValueError('Invalid transfer amount')
        if x['eligible'] not in (True,False) or not isinstance(x['eligible'],bool):
            raise ValueError('Resolve unknown eligibility into explicit branches')
        if x['eligible'] and x['arrival'] <= due: total += value
    headroom=total-d
    return {'resources':str(total), 'headroom':str(headroom),
            'shortfall':str(max(D(0),-headroom))}

def classify(ordinary: bool | None, discretionary: bool | None) -> str:
    """Classification is separate from evidence sufficiency and approval."""
    if ordinary is True: return 'ordinary_application'
    if discretionary is True: return 'permitted_judgment'
    if ordinary is False and discretionary is False: return 'departure'
    return 'pending_interpretation'

def validate_record(record: dict[str,Any]) -> list[str]:
    """Structural validation of graph, dates, hashes, and decision metadata."""
    errors=[]
    required={'case_id','cutoff','statements','asserted_links','provenance','decision_metadata'}
    if required-set(record): return ['missing:'+','.join(sorted(required-set(record)))]
    ids=[s['id'] for s in record['statements']]
    if len(ids)!=len(set(ids)): errors.append('duplicate_statement_id')
    idset=set(ids)
    for a,b in record['asserted_links']:
        if a not in idset or b not in idset: errors.append('dangling_link')
        if a==b: errors.append('self_link')
    # Directed asserted citation dependencies must have no cycles.
    links={i:[] for i in ids}
    for a,b in record['asserted_links']:
        if a in idset and b in idset: links[a].append(b)
    visiting,done=set(),set()
    def visit(v: str) -> None:
        if v in visiting: raise ValueError('cycle')
        if v in done: return
        visiting.add(v)
        for w in links[v]: visit(w)
        visiting.remove(v); done.add(v)
    try:
        for v in ids: visit(v)
    except ValueError: errors.append('dependency_cycle')
    for s in record['statements']:
        if s['kind']=='evidence':
            fields={'version','issuer','passage','entity','sha256','issued_day','effective_day','available_day'}
            if fields-set(s):
                errors.append('incomplete_source:'+s['id']); continue
            if s['available_day'] > record['cutoff']:
                errors.append('post_cutoff_evidence:'+s['id'])
            if s['available_day'] < s['issued_day']:
                errors.append('availability_precedes_issue:'+s['id'])
            if hashlib.sha256(s['text'].encode()).hexdigest()!=s['sha256']:
                errors.append('source_digest_mismatch:'+s['id'])
    needed={'methodology','provision','affected_assumption','calculation_ref','rationale_ref',
            'owner','timestamp_day','challenge','disposition_ref','approval_ref','review_trigger'}
    if needed-set(record['decision_metadata']): errors.append('incomplete_decision_metadata')
    return sorted(set(errors))

def statement_hash(record: dict[str,Any]) -> str:
    return digest(sorted((s['id'],s['text']) for s in record['statements']))

def family_numbers(family: str, effect: str) -> tuple[str,str,dict[str,Any]]:
    q=['0.02']*3; l=['0.40']*3; disc=['1']*3
    if family=='exposure_amount':
        e={'favorable':'60','adverse':'140','unchanged':'100'}[effect]
        base=loss(['100'],q[:1],l[:1],['0'],disc[:1])
        cand=loss([e],q[:1],l[:1],['0'],disc[:1])
        return str(base),str(cand),{'candidate_exposure':e,'periods':1,'q':'0.02','lgd':'0.40','discount':'1'}
    if family=='refinancing':
        e={'favorable':['100','0','0'],'adverse':['100','100','100'],
           'unchanged':['100','100','0']}[effect]
        h={'favorable':['1','0','0'],'adverse':['0','0','1'],
           'unchanged':['0','1','0']}[effect]
        base=loss(['100','100','0'],q,l,['0','1','0'],disc)
        cand=loss(e,q,l,h,disc)
        return str(base),str(cand),{'candidate_exposures':e,'candidate_termination':h,
                                  'periods':3,'q':'0.02','lgd':'0.40','discount':'1'}
    amount,day={'favorable':('20',-5),'adverse':('20',5),'unchanged':('10',-5)}[effect]
    result=cash_flow('85','5','100',[{'id':'S1','amount':amount,'arrival':day,'eligible':True}])
    return '0',result['headroom'],{'operating':'85','reserve':'5','debt':'100',
                                  'support_amount':amount,'arrival_day':day,'payment_day':0}

def make_case(row: dict[str,str], defective: bool) -> tuple[dict[str,Any],dict[str,Any]]:
    cell,family,effect,status,state=(row[k] for k in ['design_cell','family','financial_effect',
                                                   'methodological_status','evidence_state'])
    cid=cell+('-X' if defective else '-C')
    baseline,candidate,params=family_numbers(family,effect)
    boundary='borrower' if family=='sponsor_support' else 'original_lender'
    condition='resolved' if state=='sufficient' else 'unresolved'
    base_disposition='accept' if condition=='resolved' else 'conditional'
    disposition=base_disposition+('_after_source_correction' if defective else '')
    scope={'exposure_amount':'documented utilization', 'refinancing':'exposure termination timing',
           'sponsor_support':'support availability at the debt-payment cutoff'}[family]
    status_rule={
      'ordinary_application':f'M1 authorizes an ordinary documentary update of {scope} when its conditions are established.',
      'permitted_judgment':f'M1 retains the original baseline and explicitly permits a judgment-based alternative scenario for {scope}, with stated assumptions.',
      'departure':f'M1 retains the original baseline and provides no ordinary or discretionary route for this alternative {scope}. The alternative requires a documented departure, rationale and approval.'}[status]
    approval=('R1 records approval to present the alternative as a departure, retaining its factual conditions.'
              if status=='departure' else 'R1 records review of the candidate treatment under M1.')
    decision=('Accept the candidate treatment under the supplied rule.' if condition=='resolved'
              else 'Retain the baseline; report the candidate branch conditionally and request the missing confirmation.')
    asserted='E0' if defective else 'E2'
    stmts=[
      {'id':'B1','kind':'brief','text':f'Assess {scope} for Entity-{cell}, boundary {boundary}. Monetary amounts are SAR millions; cutoff is day -10. The numerical branch is a stipulated scenario.'},
      {'id':'M1','kind':'rule','text':f'Study rule M1 version 1.0, issued day -20, effective day -18, available day -19. {status_rule} Evidence eligibility and numerical calculation rules remain mandatory. Unresolved conditions require conditional reporting.'},
      {'id':'E0','kind':'evidence','issued_day':-40,'available_day':-39,'effective_day':-35,
       'text':f'E0 version 0.9 is an onboarding credit schedule issued day -40 and available day -39. It records the original entity and baseline financial arrangement, with output {baseline}. No subsequent utilization instruction, settlement confirmation or support amendment is recorded in this schedule.'},
      {'id':'E1','kind':'evidence','issued_day':-15,'available_day':-14,'effective_day':-12,
       'text':f'E1 version 1.0, issued day -15, effective day -12, available day -14, states the baseline inputs. Baseline output is {baseline}. Exposure cases use 100, probability 0.02 and loss fraction 0.40; refinancing cases retain 100 for two periods with conditional probability 0.02 and loss fraction 0.40; support cases use operating cash 85, reserve 5, debt 100 and eligible support 10 on day -5. Apply only the inputs for the family in B1.'},
      {'id':'E2','kind':'evidence','issued_day':-12,'available_day':-11,'effective_day':-11,
       'text':f'E2 version 1.0, issued day -12, effective day -11, available day -11, provides the current candidate input and event conditions: {json.dumps(params,sort_keys=True)}. The required confirmation is {condition}. With an unresolved condition, these values define a conditional branch and do not replace the baseline.'},
      {'id':'C1','kind':'calculation','text':f'Applying the study calculation to E1 and to the E2 branch gives baseline {baseline} and candidate {candidate}. The output is '+('payment-date headroom.' if family=='sponsor_support' else 'expected loss.')},
      {'id':'R1','kind':'review','text':approval+' This review does not certify that an unresolved event has occurred.'},
      {'id':'A1','kind':'rationale','text':f'The analyst cites {asserted} as the source establishing the candidate input and event condition, invokes M1 and R1 for methodological authority, and uses C1 for the financial consequence.'},
      {'id':'J1','kind':'proposed_disposition','text':decision+' This recommendation relies on the evidence attribution in A1 and the calculation in C1.'}
    ]
    links=[['C1','E1'],['C1','E2'],['A1',asserted],['A1','M1'],['A1','R1'],['A1','C1'],['J1','A1'],['J1','C1']]
    for stmt in stmts:
        if stmt['kind']=='evidence':
            stmt.update(version='0.9' if stmt['id']=='E0' else '1.0', issuer='synthetic case issuer',
                        passage=stmt['id'], entity=boundary,
                        sha256=hashlib.sha256(stmt['text'].encode()).hexdigest())
    record={'case_id':cid,'cutoff':-10,'origin':'synthetic author-constructed instrument',
            'statements':stmts,'asserted_links':links,'provenance':{'version':'1.0',
            'entity':boundary,'assumption':scope,'created_by':'study_author','parent_hash':None},
            'decision_metadata':{'methodology':'M1:1.0','provision':'M1','affected_assumption':scope,
            'calculation_ref':'C1','rationale_ref':'A1','owner':'synthetic_analyst','timestamp_day':-10,
            'challenge':'none recorded in submitted recommendation','disposition_ref':'J1',
            'approval_ref':'R1','review_trigger':'three distinct cases in 90 days'}}
    answers={'source_id':['E2'],'methodology':['M1:1.0'],'assumption':[scope],'boundary':[boundary],
      'cutoff_version':['-10:E2:1.0'],'baseline':[baseline],'candidate':[candidate],
      'condition':[condition],'classification':[status],'disposition':[disposition]}
    key={'case_id':cid,'design_cell':cell,'family':family,'effect':effect,'status':status,
         'evidence_state':state,'defective':defective,'answers':answers,
         'defect_assertion':'A1' if defective else None,'required_detection_source':'E2' if defective else None,
         'reason':'E0 contains no candidate inputs or conditions; E2 does.' if defective else 'Attribution to E2 is supported.',
         'case_design':'fixed synthetic corpus'}
    # Source labels and source order are shuffled per cell, identically in C/X variants.
    # This prevents a fixed source identifier or source position from revealing correctness.
    alias_rng=random.Random(20261027+int(cell[1:]))
    targets=['E0','E1','E2']; alias_rng.shuffle(targets)
    aliases=dict(zip(['E0','E1','E2'],targets))
    def alias_text(text: str) -> str:
        return re.sub(r'\bE[012]\b',lambda m:aliases[m[0]],text)
    for stmt in record['statements']:
        original_id=stmt['id']; stmt['id']=aliases.get(original_id,original_id)
        stmt['text']=alias_text(stmt['text'])
        if stmt['kind']=='evidence':
            stmt['passage']=stmt['id']; stmt['sha256']=hashlib.sha256(stmt['text'].encode()).hexdigest()
    evidence=[stmt for stmt in record['statements'] if stmt['kind']=='evidence']
    alias_rng.shuffle(evidence)
    record['statements']=[*record['statements'][:2],*evidence,*record['statements'][5:]]
    record['asserted_links']=[[aliases.get(a,a),aliases.get(b,b)] for a,b in record['asserted_links']]
    record['source_aliases']=aliases
    for field,values in key['answers'].items(): key['answers'][field]=[alias_text(x) for x in values]
    if key['required_detection_source']: key['required_detection_source']=aliases['E2']
    key['reason']=alias_text(key['reason'])
    return record,key

