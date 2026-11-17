import importlib.util
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parents[1] / "executive_editorial_v2.py"
spec=importlib.util.spec_from_file_location("editorial",HERE)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
validate=module.validate
Error=module.EditorialContractError

class EditorialContractTests(unittest.TestCase):
    def test_valid_reference_roles(self):
        decision={"recommendation":"Pilot before scale","rationale":"Evidence not yet validated",
          "board_ask":"Authorize bounded pilot","guardrail":"No proven savings","evidence":"Measure baseline"}
        self.assertEqual(validate("decision",decision),decision)
        options={"criterion_rows":[{"criterion":str(i),"central":"Central","federated":"Shared","local":"Local"}
             for i in range(3)],"recommendation":"Pilot","decision_condition":"Measure first"}
        self.assertEqual(len(validate("options",options)["criterion_rows"]),3)
        architecture={"markets":["Market A","Market B"],"contracts":["Identity","APIs"],
          "platforms":["Core","Security"],"nodes":["M","C","P"],"edges":[
          {"from":"M","to":"C","type":"accesses"},{"from":"C","to":"P","type":"enables"}],
          "model_status":"Illustrative"}
        self.assertEqual(len(validate("architecture",architecture)["nodes"]),3)
        roadmap={"phases":[{"name":f"Stage {i}","window":"M1","deliverable":"Measure"}
          for i in range(4)],"gates":["Evidence","Control","Value"],"decision_rule":"Stop if invalid"}
        self.assertEqual(len(validate("roadmap",roadmap)["phases"]),4)
    def test_unsupported_roles_fail_closed(self):
        with self.assertRaises(Error):validate("risk",{})
    def test_missing_decision_fields_fail_closed(self):
        with self.assertRaises(Error):validate("decision",{"recommendation":"Go"})
    def test_unknown_options_columns_fail_closed(self):
        bad={"criterion_rows":[{"criterion":"Cost","central":"A","federated":"B","extra":"C"}]*3,
           "recommendation":"B","decision_condition":"Test"}
        with self.assertRaises(Error):validate("options",bad)
    def test_architecture_disconnected_edges_fail_closed(self):
        bad={"markets":["A","B"],"contracts":["C","D"],"platforms":["E","F"],
            "nodes":["M","C","P"],"edges":[{"from":"M","to":"P","type":"enables"},
               {"from":"C","to":"P","type":"enables"}],"model_status":"Unknown"}
        with self.assertRaises(Error):validate("architecture",bad)
    def test_roadmap_requires_three_gates(self):
        bad={"phases":[{"name":"Stage","window":"M1","deliverable":"Evidence"}]*4,
             "gates":["One","Two"],"decision_rule":"Decision"}
        with self.assertRaises(Error):validate("roadmap",bad)

if __name__=="__main__":
    unittest.main()
