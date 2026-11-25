import { INVESTMENT_DECISION_FIXTURES } from "./investment-decision-fixture-data";

// Test-only, closed fixture set. This intentionally supports only the exact,
// independently reviewed inputs below; it is not an investment decision API.
export const FIXTURE_IDS = ["new-unfavorable-wait", "held-continuation-hold", "unresolved-new-snapshot-abstain", "hard-cap-reduction-review"] as const;

type FixtureId = typeof FIXTURE_IDS[number];
function canonical(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonical);
  if (value !== null && typeof value === "object") return Object.fromEntries(Object.entries(value).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0).map(([key, item]) => [key, canonical(item)]));
  return value;
}
async function digest(value: unknown): Promise<string> {
  const data = new TextEncoder().encode(JSON.stringify(canonical(value)));
  return Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", data)), byte => byte.toString(16).padStart(2, "0")).join("");
}
export async function calculateInvestmentDecisionFixture(fixtureId: FixtureId, sourceRevision: string) {
  const fixture = INVESTMENT_DECISION_FIXTURES.find(item => item.fixture_id === fixtureId);
  if (!fixture || await digest(fixture.input) !== fixture.input_sha256) throw new Error("FIXTURE_INTEGRITY_ERROR: Synthetic fixture could not be verified.");
  const input = fixture.input;
  const { quality, eligibility, thesis, valuation, portfolio } = input.signals;
  // Refuse inputs outside the validated port instead of silently generalizing.
  if (input.context.execution_mode !== "TEST" || input.context.write_scope.mode !== "NONE" ||
      quality.state !== "PASS" || eligibility.state !== "ELIGIBLE" || thesis.state !== "SURVIVES" ||
      valuation.state !== "READY" || !["ATTRACTIVE", "UNFAVORABLE"].includes(valuation.security_attractiveness) ||
      !["IN_POLICY", "HARD_CAP_BREACH"].includes(portfolio.state)) {
    throw new Error("UNSUPPORTED_FIXTURE: This pilot only evaluates its approved synthetic inputs.");
  }
  const complete = portfolio.position_snapshot_complete;
  const hardCap = portfolio.state === "HARD_CAP_BREACH";
  const gate5Status = !complete ? "UNRESOLVED" : hardCap ? "BLOCK" : "PASS";
  const gate5Reason = !complete ? "POSITION_SNAPSHOT_INCOMPLETE" : hardCap ? "POLICY_BREACH_REDUCTION_REVIEW" : "POLICY_IN_RANGE";
  let recommendation: "WAIT" | "HOLD" | null = null;
  if (complete && !hardCap && input.position_state === "NOT_HELD" && valuation.security_attractiveness === "UNFAVORABLE") recommendation = "WAIT";
  if (complete && !hardCap && input.position_state === "HELD" && valuation.security_attractiveness === "ATTRACTIVE" && "continuation_rule_ref" in portfolio && portfolio.continuation_rule_ref) recommendation = "HOLD";
  const action = !complete ? "UNRESOLVED" : hardCap ? "REDUCTION_REVIEW" : "NONE";
  const research = recommendation || hardCap ? "WATCH" : complete ? "RESEARCHED" : "RESEARCH";
  return {
    kind: "synthetic_fixture_pilot", coverage: "PARITY_SUBSET_ONLY", fixture_id: fixtureId,
    fixture_input_sha256: fixture.input_sha256, canonical_source_revision: sourceRevision,
    gate_results: [
      { gate_id: "G0", status: "PASS", reason_codes: ["IDENTITY_CUTOFF_AND_LINEAGE_VALID"] },
      { gate_id: "G1", status: "PASS", reason_codes: ["CRITICAL_EVIDENCE_VERIFIED"] },
      { gate_id: "G2", status: "PASS", reason_codes: ["POLICY_ELIGIBILITY_CONFIRMED"] },
      { gate_id: "G3", status: "PASS", reason_codes: ["THESIS_SURVIVES"] },
      { gate_id: "G4", status: "PASS", reason_codes: [`SECURITY_ATTRACTIVENESS_${valuation.security_attractiveness}`] },
      { gate_id: "G5", status: gate5Status, reason_codes: [gate5Reason] },
      { gate_id: "G6", status: "N/A", reason_codes: ["NO_TIMING_SIGNAL_REQUESTED"] },
    ],
    advisory_recommendation: recommendation, portfolio_action: action, research_state: research,
    owner_approval_required: true, execution_authorized: false, numeric_sizing_blocked: true,
    limitations: ["synthetic fixtures only", "partial Python parity; not user data or investment advice", "no retrieval, persistence, trade, or sizing"],
  };
}
