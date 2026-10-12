# Capability preflight (ENG-16, source-level slice)

`release/capability-contract.yaml` is the repository-side requirements inventory.
`contract.py` and `validate_contract.py` validate the static declaration
structure and source links. The new `preflight.py` takes a **caller-supplied**
host/channel capability view and produces a deterministic gate result. It
does not probe a tool or execute a skill.

Usage (pure-function example):

```python
from contract import load_contract
from preflight import preflight
contract = load_contract(repository_root)
result = preflight(contract, "investment-record-store", {
    "network": "supported",
    "external_actions": "requiring_approval",
})
# The result cannot authorize writes or certify connector availability.
```

Possible decisions:
- `BLOCKED_UNAVAILABLE`: a required provider capability was explicitly unavailable.
- `BLOCKED_UNVERIFIED`: a source requirement, credential class or host availability
  is unassessed/unknown. A required provider cannot be silently substituted.
- `REQUIRES_APPROVAL`: channel claims support but a write or action needs an
  independent authorization gate; `supported` never implies consent.
- `STATIC_CAPABILITY_MATCH_ONLY`: the declaration and host's *asserted*
  availability do not contradict; actual provider/runtime identity, side effects
  and credentials remain **NOT_RUN/NOT_VERIFIED**.

All outcomes have `execution_authorized: false`. The active runtime must wire
this contract into routing/preconditions, verify the live host manifest, review
`observed vs declared` side effects, and obtain specific authorization before
any action. Do not promote a source-only preflight to production certification.
