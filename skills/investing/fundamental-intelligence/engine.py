"""Deterministic evidence-gated financial comparisons."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
class Quality(str,Enum):
    VERIFIED="VERIFIED"; PROVISIONAL="PROVISIONAL"; BLOCKED="BLOCKED"
@dataclass(frozen=True)
class Metric:
    name:str; definition:str; value:Decimal|None; unit:str; published_at:str; source:str; quality:Quality
def compare(company:Metric,industry:Metric,as_of:str):
    if any(x.value is None or not x.value.is_finite() or not x.source or x.quality==Quality.BLOCKED for x in (company,industry)):
        return {"status":"BLOCKED","reason":"MISSING_INPUT","delta":None}
    if any(x.published_at>as_of for x in (company,industry)):
        return {"status":"BLOCKED","reason":"LOOKAHEAD","delta":None}
    if any((x.name,x.definition,x.unit)!=(company.name,company.definition,company.unit) for x in (industry,)):
        return {"status":"BLOCKED","reason":"INCOMPATIBLE_DEFINITION","delta":None}
    status="PROVISIONAL" if any(x.quality==Quality.PROVISIONAL for x in (company,industry)) else "VERIFIED"
    return {"status":status,"delta":str(company.value-industry.value)}
def percentile(value:Decimal,peers:list[Decimal],higher_is_better=True):
    if len(peers)<5 or not value.is_finite() or any(not x.is_finite() for x in peers): return None
    result=(Decimal(sum(x<value for x in peers))+Decimal(sum(x==value for x in peers))/2)/len(peers)
    return result if higher_is_better else 1-result
def economic_spread(roic:Metric,wacc:Metric,as_of:str):
    if any(x.value is None or not x.value.is_finite() or x.quality==Quality.BLOCKED or not x.source or x.published_at>as_of or x.unit!="fraction" for x in (roic,wacc)):
        return {"status":"BLOCKED","value":None}
    status="PROVISIONAL" if any(x.quality==Quality.PROVISIONAL for x in (roic,wacc)) else "VERIFIED"
    return {"status":status,"value":str(roic.value-wacc.value)}
