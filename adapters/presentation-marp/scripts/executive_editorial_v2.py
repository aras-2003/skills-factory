"""Executive Editorial v2: four canonical, editable native ODP compositions.

T01 decision / T02 operating-model options / T03 architecture / T04 roadmap.
No external code or brand assets. Rendered by existing PRES-07 ODP emitter.
All meaningful labels are from the DeckSpec extensions (no invented metrics).
"""
from __future__ import annotations
from typing import Callable

PAGE_W = 28.22
INK = "#17243a"
ACCENT = "#176b87"
MUTED = "#52627a"
LIGHT = "#e8eeee"
WARM = "#eee1cb"
CANVAS = "#f6f4ee"
WHITE = "#ffffff"
RULE = "#a3b2b8"

class EditorialContractError(ValueError):
    pass

def validate(role, data):
    """Return complete, strictly typed author-controlled content."""
    if not isinstance(data, dict):
        raise EditorialContractError("editorial_v2 must be an object")
    common = {
       "decision": ("recommendation","rationale","board_ask","guardrail","evidence"),
       "options": ("criterion_rows","recommendation","decision_condition"),
       "architecture": ("markets","contracts","platforms","nodes","edges","model_status"),
       "roadmap": ("phases","gates","decision_rule"),
    }
    if role not in common:
        raise EditorialContractError(f"Unsupported v2 role: {role}")
    missing = [key for key in common[role] if key not in data]
    if missing:
        raise EditorialContractError(f"Missing v2 fields for {role}: {missing}")
    def short(value, key, limit=160):
        if not isinstance(value, str) or not value.strip() or len(value)>limit:
            raise EditorialContractError(f"{role}.{key}: expected 1..{limit} characters")
        return value
    if role=="decision":
        for k in common[role]:
            short(data[k],k,230 if k=="rationale" else 90 if k=="board_ask" else 160)
    elif role=="options":
        rows=data["criterion_rows"]
        if not isinstance(rows,list) or not 3<=len(rows)<=4:
            raise EditorialContractError("options.criterion_rows requires 3..4 rows")
        for idx,row in enumerate(rows):
            if not isinstance(row,dict) or set(row)!={"criterion","central","federated","local"}:
                raise EditorialContractError(f"options row {idx}: invalid columns")
            for k,v in row.items():short(v,f"row {idx}.{k}",18 if k=="criterion" else 35)
        short(data["recommendation"],"recommendation")
        short(data["decision_condition"],"decision_condition",230)
    elif role=="architecture":
        for k,low,high in (("markets",2,3),("contracts",2,3),("platforms",2,3)):
            values=data[k]
            if not isinstance(values,list) or not low<=len(values)<=high:
                raise EditorialContractError(f"architecture.{k}: {low}..{high} strings")
            for i,v in enumerate(values):short(v,f"{k}[{i}]",48)
        nodes=data["nodes"];edges=data["edges"]
        if not isinstance(nodes,list) or len(nodes)!=3 or any(not isinstance(n,str) or not n for n in nodes):
            raise EditorialContractError("architecture.nodes: exactly 3 semantic IDs")
        if len(set(nodes))!=3:
            raise EditorialContractError("architecture.nodes: duplicate IDs")
        if not isinstance(edges,list) or len(edges)!=2:
            raise EditorialContractError("architecture.edges: exactly 2 typed relations")
        if [(e.get("from"),e.get("to")) for e in edges] != [(nodes[0],nodes[1]),(nodes[1],nodes[2])]:
            raise EditorialContractError("architecture.edges: unstable or disconnected semantic chain")
        for e in edges:
            if e.get("type") not in {"serves","enables","accesses","realizes"}:
                raise EditorialContractError("architecture edge type invalid")
        short(data["model_status"],"model_status",210)
    elif role=="roadmap":
        phases=data["phases"]; gates=data["gates"]
        if not isinstance(phases,list) or len(phases)!=4:
            raise EditorialContractError("roadmap.phases requires 4 stages")
        if not isinstance(gates,list) or len(gates)!=3:
            raise EditorialContractError("roadmap.gates requires exactly 3 stage transitions")
        for i,p in enumerate(phases):
            if not isinstance(p,dict) or set(p)!={"name","window","deliverable"}:
                raise EditorialContractError(f"roadmap phase {i} invalid")
            for k,v in p.items():short(v,f"phase {i}.{k}",70 if k=="deliverable" else 35)
        for i,g in enumerate(gates):short(g,f"gate {i}",90)
        short(data["decision_rule"],"decision_rule",210)
    return data

def render(page, slide, frame:Callable, rect:Callable, editorial:dict):
    role=slide["role"].lower()
    d=validate(role,editorial)
    sid=slide["slide_id"]
    def bx(name,x,y,w,h,color):
        if x<0 or y<0 or x+w>PAGE_W+.01 or y+h>15.875+.01:
            raise EditorialContractError(f"{sid}/{name}: shape outside canvas")
        rect(page,f"{sid} ED2 {name}",x,y,w,h,color)
    def tx(name,x,y,w,h,value,style="outline"):
        if x<0 or y<0 or x+w>PAGE_W+.01 or y+h>15.875+.01:
            raise EditorialContractError(f"{sid}/{name}: text outside canvas")
        if not isinstance(value,str) or len(value)>245:
            raise EditorialContractError(f"{sid}/{name}: invalid text")
        frame(page,f"{sid} ED2 {name}",x,y,w,h,value,style)
    bx("background",0,0,PAGE_W,15.875,CANVAS)
    bx("ribbon",0,0,PAGE_W,.14,INK)
    tx("classification",1.0,.45,20.5,.52,"EXECUTIVE EDITORIAL  /  "+role.upper(),"small")
    tx("headline",1.0,1.22,25.8,1.55,slide["action_title"],"title")
    bx("headline underline",1.0,3.05,26.2,.045,RULE)
    tx("footer",1,14.92,23.5,.45,
       f"{sid}  |  {slide.get('layout_reference','REFERENCE-MAPPED')}  |  SYNTHETIC SCENARIO","small")

    if role=="decision":
        tx("eyebrow",1.0,3.65,16,.58,"PROVISIONAL RECOMMENDATION","small")
        bx("recommendation accent",1.0,4.55,.15,3.6,ACCENT)
        tx("recommendation",1.48,4.57,16.3,2.6,d["recommendation"],"metric")
        tx("rationale label",1.0,9.05,16,.54,"WHY THIS DECISION","small")
        tx("rationale",1.0,9.85,16.1,2.55,d["rationale"],"outline")
        bx("board decision block",18.4,3.8,8.5,5.2,WARM)
        tx("board decision label",18.85,4.2,7.7,.65,"BOARD DECISION","cardhead")
        tx("board decision",18.85,5.2,7.6,2.8,d["board_ask"],"outline")
        bx("evidence block",18.4,9.3,8.5,3.65,LIGHT)
        tx("evidence label",18.85,9.7,7.6,.56,"EVIDENCE GATE","cardhead")
        tx("evidence",18.85,10.65,7.6,1.8,d["evidence"],"small")
        tx("guardrail",1.0,13.25,25.8,.8,"LIMITATION  /  "+d["guardrail"],"small")
    elif role=="options":
        tx("recommendation",1,3.46,25.5,.75,"PROVISIONAL CHOICE  /  "+d["recommendation"],"cardhead")
        x=[1.0,6.82,13.35,19.88];w=[5.72,6.43,6.43,6.34]
        headers=["CRITERION","CENTRALIZED","FEDERATED PILOT","DECENTRALIZED"]
        for j in range(4):
            bx(f"column header {j}",x[j],4.65,w[j],1.25,INK if j!=2 else ACCENT)
            tx(f"header {j}",x[j]+.2,4.95,w[j]-.35,.6,headers[j],"headinglight")
        rows=d["criterion_rows"]
        for i,row in enumerate(rows):
            yy=5.97+i*1.43
            for j,(key) in enumerate(("criterion","central","federated","local")):
                bx(f"cell {i}.{j}",x[j],yy,w[j],1.34,WHITE if (i+j)%2==0 else LIGHT if j!=2 else "#d8e7e5")
                tx(f"cell text {i}.{j}",x[j]+.2,yy+.27,w[j]-.4,.85,row[key],"cardhead" if j==0 else "outline")
        yy=6.0+len(rows)*1.43
        bx("decision line",1.0,yy+.35,26.2,.045,RULE)
        tx("decision condition",1.0,yy+.8,25.4,1.1,d["decision_condition"],"small")
    elif role=="architecture":
        tx("zone heading",1.0,3.45,25.4,.57,"CONCEPTUAL LAYERS  /  FORMAL MODEL LINKAGE IS PROVISIONAL","small")
        # Three vertically stacked semantic layers, each with distinct native objects.
        layer_y=[4.32,7.53,10.75]
        groups=[("MARKETS",d["markets"],WHITE),("CONTRACTS",d["contracts"],"#d8e7e5"),("CORE PLATFORMS",d["platforms"],WARM)]
        for i,(label,values,color) in enumerate(groups):
            y=layer_y[i]
            tx(f"layer title {i}",1.0,y,5.1,.65,label,"cardhead")
            bx(f"layer rail {i}",6.0,y-.06,.12,1.94,ACCENT if i==1 else MUTED)
            count=len(values);width=(19.9-(count-1)*.33)/count
            for j,item in enumerate(values):
                xx=6.5+j*(width+.33)
                bx(f"node {i}.{j}",xx,y-.1,width,1.88,color)
                tx(f"node title {i}.{j}",xx+.2,y+.3,width-.4,1.05,item,"outline")
            tx(f"node id {i}",1.0,y+1.15,4.6,.5,d["nodes"][i],"small")
        # Explicit directed dependencies rather than decorative arrows.
        for i,edge in enumerate(d["edges"]):
            y=layer_y[i]+1.93
            bx(f"edge vertical {i}",15.92,y,.10,1.04,ACCENT)
            bx(f"edge arrow base {i}",15.71,y+.89,.51,.12,ACCENT)
            tx(f"edge label {i}",16.4,y+.16,9.4,.58,
               f"{edge['from']} → {edge['to']}  /  {edge['type']}","small")
        tx("model status",1.0,14.13,25.5,.54,d["model_status"],"small")
    elif role=="roadmap":
        tx("roadmap guidance",1,3.49,24.8,.6,"SEQUENCED DELIVERY  /  EVIDENCE GATES CONTROL PROGRESSION","small")
        phases=d["phases"]
        xs=[1.0,7.73,14.47,21.19]
        for i,p in enumerate(phases):
            x=xs[i];width=6.08 if i==3 else 6.18
            bx(f"phase bar {i}",x,4.6,width,1.08,ACCENT if i==1 else INK)
            tx(f"phase label {i}",x+.2,4.79,width-.4,.65,f"{i+1:02d}  {p['name']}","headinglight")
            tx(f"window {i}",x+.15,6.02,width-.3,.8,p["window"],"cardhead")
            bx(f"timeline {i}",x,7.4,width,.09,RULE)
            tx(f"deliverable {i}",x+.15,8.0,width-.35,2.3,p["deliverable"],"outline")
            if i<3:
                gx=x+width-.4
                bx(f"gate line {i}",gx,10.52,1.04,.1,ACCENT)
                tx(f"gate label {i}",x+.12,11.45,width-.1,1.18,
                   f"GATE {i+1}  /  {d['gates'][i]}","small")
        bx("decision rule bg",1,13.3,26.2,.95,WARM)
        tx("decision rule",1.3,13.52,25.4,.55,d["decision_rule"],"small")
    else:
        raise EditorialContractError(f"Unsupported role {role}")
