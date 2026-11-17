"""Executive grammar for the existing ODP→LibreOffice native PPTX pathway.

This is layout composition on top of the existing PRES-07 editable-native emitter,
NOT an alternate renderer. All depicted target-state entities are illustrative.
"""
from __future__ import annotations

PAGE_W = 28.22
BG = "#f6f4ee"
INK = "#17243a"
ACCENT = "#176b87"
LIGHT = "#d8e5ed"
MUTED = "#52627a"
WARM = "#eee1cb"

def render(page, slide, ordinal, frame, rect, pattern, provenance):
    role = slide["role"].lower()
    sid = slide["slide_id"]
    title = slide["action_title"]
    if not pattern or not pattern.get("layout_id"):
        raise ValueError(f"{sid}: no approved pattern selection")
    if pattern.get("status") != "PLANNED_NOT_RENDERED":
        raise ValueError(f"{sid}: reference evidence not ready: {pattern.get('status')}")
    def box(name, x, y, w, h, fill=LIGHT):
        assert x >= 0 and y >= 0 and x+w <= PAGE_W+.01 and y+h <= 15.875+.01
        rect(page, f"{sid} {name}", x, y, w, h, fill)
    def txt(name, x, y, w, h, value, kind="body"):
        assert x >= 0 and y >= 0 and x+w <= PAGE_W+.01 and y+h <= 15.875+.01
        frame(page, f"{sid} {name}", x, y, w, h, value, "title" if kind=="title" else "small" if kind=="small" else "outline")
    box("top ribbon",0,0,PAGE_W,.17,ACCENT)
    txt("eyebrow",1.0,.45,22,.55,"CIO TRANSFORMATION  /  EXECUTIVE DECISION   •   ILLUSTRATIVE", "small")
    txt("action headline",1.0,1.18,26.2,1.7,title,"title")
    box("divider",1.0,2.91,26.15,.045,MUTED)
    note = "SOURCE / METHOD: " + ", ".join(pattern["source_ids"][:3]) + "   |   " + sid + " / " + pattern["layout_id"]
    txt("source footer",1.0,14.86,26,.52,note,"small")
    txt("page count",25.1,.39,2.15,.48,f"{ordinal:02d} / 10","small")

    def card(n,x,y,w,h,header,detail,accent=LIGHT):
        box(n+" bg",x,y,w,h,accent)
        txt(n+" heading",x+.28,y+.27,w-.56,.69,header)
        txt(n+" detail",x+.28,y+1.12,w-.56,h-1.33,detail,"small")

    if role=="decision":
        box("recommendation",1,3.45,17.2,9.6,LIGHT)
        txt("recommendation label",1.5,3.8,15,.6,"PROVISIONAL RECOMMENDATION","small")
        txt("recommendation message",1.5,4.65,15.9,2.6,"Run a reversible federated pilot")
        txt("decision consequences",1.5,7.5,15.6,3.9,"Approve: baseline measurement\nTest: two country archetypes\nDefer: full application consolidation")
        card("mandate",18.7,3.45,8.35,4.42,"ASK OF THE BOARD","Authorize a pilot, ownership and measurement.",WARM)
        card("guardrail",18.7,8.1,8.35,4.95,"DO NOT ASSUME","Neither 35% overlap nor 15% cost target proves realizable savings.")
    elif role=="options":
        for i,(head,body) in enumerate([
            ("CENTRALIZED","Higher consistency\nPotential market delay\nAuthority concentration"),
            ("FEDERATED PILOT","Shared guardrails\nLocal product autonomy\nDecision rights required"),
            ("DECENTRALIZED","Market responsiveness\nDuplication exposure\nIntegration risk")]):
            card(f"option {i}",1+i*8.85,3.7,8.45,8.1,head,body,WARM if i==1 else LIGHT)
        txt("decision condition",1.2,12.3,25.7,1.1,"Selection depends on measured lead time, service reliability and total cost.","small")
    elif role=="capability":
        txt("capability premise",1.2,3.5,25.4,.9,"First find overlapping outcomes; do not equate applications with capabilities.")
        for i,(head,detail) in enumerate([
            ("CUSTOMER & CHANNELS","Customer journeys, local variation"),
            ("PLATFORMS & DATA","Common APIs, identity, canonical data"),
            ("SECURITY & CONTROL","Policy, exceptions, evidence"),
            ("DELIVERY & OPERATIONS","Flow, releases, service reliability")]):
            x=1.0+(i%2)*13.45;y=5.0+(i//2)*4.1
            card(f"capability {i}",x,y,12.95,3.7,head,detail)
    elif role=="architecture":
        txt("architecture subtitle",1.2,3.4,24.9,.8,"Conceptual target hypothesis — not a verified deployment inventory.","small")
        card("local markets",1.2,4.6,7.2,7,"LOCAL EXPERIENCES","Country products\nMarket priorities\nRegulatory variations",LIGHT)
        card("contract",10.2,4.6,7.9,7,"SHARED CONTRACTS","API and event standards\nIdentity and customer data\nObservability",WARM)
        card("core",19.9,4.6,7.1,7,"CORE PLATFORMS","Core services\nSecurity controls\nIntegration platform",LIGHT)
        box("edge one",8.55,8.1,1.42,.13,ACCENT);box("edge two",18.25,8.1,1.44,.13,ACCENT)
        txt("model bound",1.1,12.1,26.1,1.2,"Formal ArchiMate / UML topology is out of scope until IR mappings are verified.","small")
    elif role=="governance":
        for i,(head,details) in enumerate([
            ("DECIDE","Named accountable owner\nDecision evidence\nRecorded outcome"),
            ("ADVISE","Architecture & security\nNo implicit veto\nExplicit exception grounds"),
            ("ESCALATE","Only unresolved material\ncross-domain constraints\nwith a clear deadline")]):
            card(f"governance {i}",1+i*8.85,4.0,8.45,7.8,head,details, WARM if i==0 else LIGHT)
        txt("governance policy",1.3,12.3,25.6,1.1,"Do not invent decision owners; confirm mandates in discovery.","small")
    elif role=="roadmap":
        for i,(phase,period,details) in enumerate([
            ("BASELINE","M1–2","Inventory\nDecision rights\nMetric definitions"),
            ("PILOT","M3–6","Two archetypes\nPlatform contracts\nExperiment review"),
            ("SCALE","M6–9","Expand proven patterns\nFix constraints"),
            ("REALIZE","M9–12","Measured benefit\nStop / adapt")]):
            x=1+i*6.76
            card(f"roadmap {i}",x,4.8,6.3,7.3,period+"  "+phase,details, WARM if i==1 else LIGHT)
            if i<3:box(f"connector {i}",x+6.31,8.2,.45,.12,ACCENT)
        txt("gates",1.2,12.6,25.5,1,"Every transition requires evidence; calendar dates alone are not approval.","small")
    elif role=="kpi":
        card("metric lead-time",1.0,4.0,12.6,8.4,"LEAD TIME","90 days • stated baseline\n30 days • management target\nAchieved result: UNKNOWN",LIGHT)
        card("metric cost",14.0,4.0,13.1,8.4,"IT COST","−15% • management target\nSpend baseline: UNKNOWN\nRealized saving: UNKNOWN",WARM)
        txt("measurement note",1.2,12.7,24.7,.9,"Targets are not outcomes. Validate denominator and observation period.","small")
    elif role=="risks":
        for i,(head,detail) in enumerate([
            ("OWNERSHIP","Conflicting decisions\nDefine accountable owner"),
            ("PLATFORM CAPACITY","Shared-team queues\nBaseline before scale"),
            ("SERVICE STABILITY","Migration disruption\nDefine service guardrails"),
            ("BENEFIT REALIZATION","Unproven savings\nEvidence before retirement")]):
            card(f"risk {i}",1+(i%2)*13.45,4.0+(i//2)*4.65,12.95,4.18,head,detail,WARM if i==3 else LIGHT)
    elif role=="value":
        for i,(head,detail) in enumerate([
            ("VALUE HYPOTHESES","Lower duplication\nShorter changes\nHigher reliability"),
            ("COSTS TO VALIDATE","Platform investment\nTransition effort\nOperating expense"),
            ("REALIZATION EVIDENCE","Financial baseline\nOwner and metric\nPost-change measured value")]):
            card(f"value {i}",1+i*8.85,4.0,8.45,8.1,head,detail,WARM if i==2 else LIGHT)
        txt("value disclaimer",1.2,12.6,25.5,.9,"No ROI, savings or maturity scores are calculated without inputs.","small")
    elif role=="handoff":
        parts=[("STRATEGY","OBJ-001"),("CAPABILITY","CAP-001"),("PROCESS","PROC-001"),("APPLICATION","APP-001"),("DELIVERY","INIT-001"),("MEASURE","KPI-001")]
        for i,(head,identifier) in enumerate(parts):
            x=1+(i%3)*9.0;y=4.4+(i//3)*4.65
            card(f"trace {i}",x,y,8.5,3.8,head,identifier+ "\nProposed link — verify")
        txt("trace warning",1.2,13.25,25.5,.65,"Illustrative identifiers only; not imported from a verified model.","small")
    else:
        raise ValueError(f"Unsupported executive role: {role}")
    source=slide.get("claims",[])
    statuses=", ".join(sorted({c.get("epistemic_status","UNKNOWN") for c in source}))
    txt("epistemic status",1.0,14.27,25.7,.48,"EVIDENCE: "+statuses+"   |   Layout source usage: reference-informed, not proprietary reproduction","small")
