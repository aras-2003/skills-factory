"""python3 -m unittest discover -s docs/architecture/archify/scripts -p 'test_*.py'"""
import copy
import json
import unittest
from check_fixture import UnsafeFixture, validate, FIXTURE

class TestArchifyInput(unittest.TestCase):
    def setUp(self):
        self.data=json.loads(FIXTURE.read_text())

    def test_fixture_valid(self):
        validate(self.data)

    def test_reject_html_and_active_uris(self):
        for label in ("<script>alert(1)</script>","<img src=x onerror=alert(1)>","javascript:alert(1)"):
            obj=copy.deepcopy(self.data)
            obj["components"][0]["label"]=label
            with self.subTest(label=label),self.assertRaises(UnsafeFixture):
                validate(obj)

    def test_reject_path_traversal(self):
        for path in ("../../index.html","/var/tmp/out.html","subdir/synthetic-architecture.html"):
            obj=copy.deepcopy(self.data)
            obj["meta"]["output"]=path
            with self.subTest(path=path),self.assertRaises(UnsafeFixture):
                validate(obj)

    def test_reject_dangling_and_duplicate(self):
        for action in ("dangling","duplicate"):
            obj=copy.deepcopy(self.data)
            if action=="dangling":
                obj["connections"][0]["to"]="missing"
            else:
                obj["components"][1]["id"]="router"
            with self.subTest(action=action),self.assertRaises(UnsafeFixture):
                validate(obj)

if __name__=="__main__":
    unittest.main()
