"""Source-bound profit pools, driver-tree reconciliation, PVM, and cost bridges."""
from __future__ import annotations
import argparse, json, sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

class InputError(ValueError): pass

def dec(value: Any, field: str) -> Decimal:
    if isinstance(value,bool): raise InputError(f"{field} must be numeric")
    try: out=Decimal(str(value))
    except (InvalidOperation,TypeError,ValueError) as exc: raise InputError(f"{field} must be numeric") from exc
    if not out.is_finite(): raise InputError(f"{field} must be finite")
    return out

def evidence(item: Any, field: str, as_of: date) -> tuple[Decimal,dict[str,str]]:
    if not isinstance(item,dict) or not isinstance(item.get("source_id"),str) or not item["source_id"].strip(): raise InputError(f"{field} requires source_id and published_at")
    try: published=date.fromisoformat(item.get("published_at",""))
    except ValueError as exc: raise InputError(f"{field}.published_at must be YYYY-MM-DD") from exc
    if published.isoformat()!=item["published_at"] or published>as_of: raise InputError(f"{field} has invalid or future-dated evidence")
    return dec(item.get("value"),f"{field}.value"),{"source_id":item["source_id"].strip(),"published_at":published.isoformat()}

def calculate(data:dict[str,Any])->dict[str,Any]:
    try: as_of=date.fromisoformat(data.get("as_of",""))
    except (ValueError,TypeError) as exc: raise InputError("as_of must be YYYY-MM-DD") from exc
    if as_of.isoformat()!=data["as_of"]: raise InputError("as_of must be YYYY-MM-DD")
    currency=data.get("currency")
    if not isinstance(currency,str) or len(currency)!=3 or not currency.isalpha(): raise InputError("currency must be an explicit three-letter code")
    pools=data.get("profit_pools")
    if not isinstance(pools,list) or not pools: raise InputError("profit_pools must be a non-empty list")
    names=set(); total_revenue=Decimal(0); total_profit=Decimal(0); pool_rows=[]
    for i,row in enumerate(pools):
        if not isinstance(row,dict) or not isinstance(row.get("entity"),str) or not row["entity"].strip() or row["entity"] in names: raise InputError("profit pool entities require unique names")
        names.add(row["entity"]); rev,rev_ev=evidence(row.get("revenue"),f"profit_pools[{i}].revenue",as_of); profit,profit_ev=evidence(row.get("operating_profit"),f"profit_pools[{i}].operating_profit",as_of)
        if rev<0: raise InputError("revenue cannot be negative")
        total_revenue+=rev; total_profit+=profit
        pool_rows.append({"entity":row["entity"],"revenue":str(rev),"operating_profit":str(profit),"margin":str(profit/rev if rev else Decimal(0)),"evidence":{"revenue":rev_ev,"operating_profit":profit_ev}})
    # PVM is an exact sequential decomposition: volume, then mix at base prices, then price.
    products=data.get("pvm")
    if not isinstance(products,list) or not products: raise InputError("pvm must contain products")
    ids=set(); items=[]; q0=Decimal(0); q1=Decimal(0); prior_mix_value=Decimal(0); current_mix_value=Decimal(0); prior_revenue=Decimal(0); current_revenue=Decimal(0); price_effect=Decimal(0)
    for i,p in enumerate(products):
        if not isinstance(p,dict) or not isinstance(p.get("id"),str) or not p["id"].strip() or p["id"] in ids: raise InputError("pvm products require unique ids")
        ids.add(p["id"]); p0,e0=evidence(p.get("prior_price"),f"pvm[{i}].prior_price",as_of); p1,e1=evidence(p.get("current_price"),f"pvm[{i}].current_price",as_of); v0,e2=evidence(p.get("prior_volume"),f"pvm[{i}].prior_volume",as_of); v1,e3=evidence(p.get("current_volume"),f"pvm[{i}].current_volume",as_of)
        if min(p0,p1,v0,v1)<0: raise InputError("PVM prices and volumes must be non-negative")
        q0+=v0; q1+=v1; prior_revenue+=p0*v0; current_revenue+=p1*v1; price_effect+=(p1-p0)*v1
        items.append((p["id"],p0,p1,v0,v1,{"prior_price":e0,"current_price":e1,"prior_volume":e2,"current_volume":e3}))
    if q0<=0 or q1<=0: raise InputError("PVM total prior and current volumes must be positive")
    for _,p0,_,v0,v1,_ in items:
        prior_mix_value+=p0*(v0/q0); current_mix_value+=p0*(v1/q1)
    volume_effect=(q1-q0)*prior_mix_value; mix_effect=q1*(current_mix_value-prior_mix_value)
    if volume_effect+mix_effect+price_effect != current_revenue-prior_revenue: raise InputError("PVM bridge failed to reconcile")
    # Driver tree is bounded to explicit observed child values and sum/product operations.
    tree=data.get("driver_tree")
    if not isinstance(tree,dict): raise InputError("driver_tree is required")
    def eval_node(node:Any,path:str,depth:int=0)->tuple[Decimal,dict[str,Any]]:
        if depth>12 or not isinstance(node,dict): raise InputError("driver_tree is malformed or too deep")
        value,ev=evidence(node.get("reported_value"),path+".reported_value",as_of); children=node.get("children",[]); op=node.get("operation")
        if not isinstance(children,list): raise InputError(f"{path}.children must be a list")
        if children:
            if op not in {"sum","product"}: raise InputError(f"{path}.operation must be sum or product")
            vals=[eval_node(ch,f"{path}.children[{i}]",depth+1) for i,ch in enumerate(children)]
            calculated=sum((x[0] for x in vals),Decimal(0)) if op=="sum" else __import__("functools").reduce(lambda a,b:a*b,(x[0] for x in vals),Decimal(1))
            if calculated!=value: raise InputError(f"{path} does not reconcile to its {op} children")
            return value,{"reported_value":str(value),"operation":op,"evidence":ev,"children":[x[1] for x in vals]}
        return value,{"reported_value":str(value),"operation":"leaf","evidence":ev,"children":[]}
    tree_value,tree_audit=eval_node(tree,"driver_tree")
    costs=data.get("cost_bridge")
    if not isinstance(costs,list): raise InputError("cost_bridge must be a list")
    cost_delta=Decimal(0); cost_rows=[]
    for i,row in enumerate(costs):
        base,be=evidence(row.get("baseline"),f"cost_bridge[{i}].baseline",as_of); actual,ae=evidence(row.get("actual"),f"cost_bridge[{i}].actual",as_of); delta=actual-base; cost_delta+=delta
        cost_rows.append({"id":row.get("id"),"baseline":str(base),"actual":str(actual),"delta":str(delta),"evidence":{"baseline":be,"actual":ae}})
    return {"as_of":as_of.isoformat(),"currency":currency.upper(),"profit_pool":{"entities":pool_rows,"total_revenue":str(total_revenue),"total_operating_profit":str(total_profit),"aggregate_margin":str(total_profit/total_revenue if total_revenue else Decimal(0))},"driver_tree":{"reported_value":str(tree_value),"audit":tree_audit},"pvm":{"prior_revenue":str(prior_revenue),"current_revenue":str(current_revenue),"change":str(current_revenue-prior_revenue),"volume_effect":str(volume_effect),"mix_effect":str(mix_effect),"price_effect":str(price_effect),"reconciles":True},"cost_bridge":{"components":cost_rows,"total_delta":str(cost_delta)},"limitations":["All values are supplied evidence or explicit model structure; no inputs are inferred.","Profit pools are descriptive and do not establish causality or strategic attractiveness.","PVM uses a sequential volume → mix at base prices → price convention; alternative bridge orders can allocate interaction effects differently.","Cost bridge signs are actual minus baseline; interpretation depends on the supplied cost definition."]}

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("input",nargs="?",type=Path);args=parser.parse_args()
    try:
        payload=args.input.read_text(encoding="utf-8") if args.input else sys.stdin.read(); data=json.loads(payload)
        if not isinstance(data,dict): raise InputError("input must be a JSON object")
        print(json.dumps(calculate(data),indent=2,sort_keys=True));return 0
    except (OSError,json.JSONDecodeError,InputError) as exc: print(json.dumps({"error":str(exc)},sort_keys=True));return 2

if __name__=="__main__": raise SystemExit(main())
