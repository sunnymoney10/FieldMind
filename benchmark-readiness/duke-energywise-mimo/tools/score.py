"""Explicit-denominator scoring for marked synthetic arithmetic tests. No real-data loader."""
from statistics import median
def fraction(n,d):return n/d if d else None
def score_fixture_verdicts(rows,prospects,times):
 if not all(r.get('synthetic') is True for r in rows+prospects+times):raise ValueError('Synthetic scoring inputs only')
 factual=[r for r in rows if r.get('kind')=='factual'];counts={v:sum(r.get('verdict')==v for r in factual) for v in ['correct','incorrect','unverifiable']}
 if sum(counts.values())!=len(factual):raise ValueError('Unknown verdict')
 authority=[r for r in rows if r.get('authority_current_verdict') in ['correct','incorrect','unverifiable']]
 ac={v:sum(r['authority_current_verdict']==v for r in authority) for v in ['correct','incorrect','unverifiable']}
 errors={name:sum(r.get('error_type')==name for r in rows) for name in ['wrong_business','wrong_suite','unsupported_verified_authority','history_current_conflation','fabricated_source']}
 paired={};excluded=0
 for t in times:
  if t.get('timing_kind')!='synthetic_scoring_test' or t.get('completion_status')!='completed' or t.get('elapsed_seconds') is None or t.get('elapsed_seconds',0)<=0:excluded+=1;continue
  group=paired.setdefault(t['record_ref'],{})
  if t.get('arm') not in ['manual','assisted'] or t['arm'] in group:raise ValueError('Duplicate/unknown arm')
  group[t['arm']]=t['elapsed_seconds']
 reductions=[100*(p['manual']-p['assisted'])/p['manual'] for p in paired.values() if set(p)=={'manual','assisted'}]
 observed=[p for p in prospects if isinstance(p.get('useful_verification_step'),bool)];changed=[p for p in prospects if p.get('priority_changed') is True];source_ratings=[r['source_usefulness'] for r in rows if r.get('source_usefulness') in [0,1,2]]
 return {'synthetic_only':True,'not_real_benchmark_results':True,'documentary_counts':counts,'documentary_accuracy':fraction(counts['correct'],counts['correct']+counts['incorrect']),'unverifiable_rate':fraction(counts['unverifiable'],len(factual)),'authority_counts':ac,'decision_authority_accuracy':fraction(ac['correct'],ac['correct']+ac['incorrect']),'critical_errors':errors,'hard_integrity_gate':'BLOCKED' if any(errors.values()) else 'PASS_SYNTHETIC_ONLY','useful_verification_steps':sum(p['useful_verification_step'] for p in observed),'usefulness_denominator':len(observed),'priority_changed_count':len(changed),'supported_priority_change_count':sum(p.get('priority_rationale_supported') is True for p in changed),'source_usefulness_rate':fraction(sum(x>=1 for x in source_ratings),len(source_ratings)),'complete_timing_pairs':len(reductions),'excluded_timing_rows':excluded,'median_paired_elapsed_reduction_percent':median(reductions) if reductions else None,'real_execution_authorized':False}
