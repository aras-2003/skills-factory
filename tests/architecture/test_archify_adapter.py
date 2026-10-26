"""ARC-03 adapter and sandbox-boundary contract tests."""
import copy
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.architecture.archify_adapter import SANDBOX_IMAGE,SANDBOX_SCRIPT,UPSTREAM_SHA,RenderError,_sandbox_command,archify_candidate,offline_svg_fallback,render

REV="a"*40
REF={"uri":"repo://docs/example.md","revision":REV,"locator":"L1"}

def sample():
    def node(node_id,kind,label):
        return {"id":node_id,"type":kind,"label":label,"state":"observed","evidence":[copy.deepcopy(REF)]}
    return {"schema_version":1,"model_id":"arc3","source_revision":REV,
            "nodes":[node("a","skill","<script>alert(1)</script>"),node("b","tool","Tool")],
            "edges":[{"id":"ab","type":"calls","from":"a","to":"b","state":"observed","evidence":[copy.deepcopy(REF)]}]}

class AdapterTests(unittest.TestCase):
    def test_repeatable_candidate_and_relation_mapping(self):
        obj=sample()
        a=archify_candidate(obj)
        self.assertEqual(a,archify_candidate(copy.deepcopy(obj)))
        self.assertEqual(a["diagram_type"],"architecture")
        self.assertEqual((a["connections"][0]["from"],a["connections"][0]["to"]),("n0","n1"))
        self.assertEqual(a["connections"][0]["label"],"call")
        # Any authored offset pins a label and disables upstream collision
        # avoidance. Keep automatic placement for source graphs that evolve.
        self.assertNotIn("labelDy", a["connections"][0])
        self.assertNotIn("labelAt", a["connections"][0])
        self.assertTrue(all(component["size"] == [300,76] for component in a["components"]))

    def test_architecture_labels_are_compact_but_provenance_stays_in_ir(self):
        obj=sample()
        obj["nodes"][0].update(type="workflow")
        obj["nodes"][1].update(type="process",label="Failure gate, source line 1: a very long explanatory failure condition")
        obj["edges"][0].update(type="depends_on")
        candidate=archify_candidate(obj)
        self.assertEqual(candidate["components"][1]["label"],"Gate at L1")
        self.assertEqual(obj["nodes"][1]["label"],"Failure gate, source line 1: a very long explanatory failure condition")
        self.assertEqual(candidate["connections"][0]["label"],"dep")

    def test_safe_static_fallback_escapes_content(self):
        out=offline_svg_fallback(sample())
        self.assertIn("&lt;script&gt;",out)
        self.assertNotIn("<script>",out)
        self.assertNotIn("javascript:",out)
        self.assertNotIn("<foreignObject",out)
        self.assertIn("<svg",out)

    def test_unknown_edge_is_dashed(self):
        m=sample()
        m["edges"][0].update(type="unknown",state="unknown",evidence=[])
        self.assertEqual(archify_candidate(m)["connections"][0]["variant"],"dashed")

    def test_invalid_relation_fails_closed(self):
        m=sample()
        m["edges"][0]["to"]="ghost"
        with self.assertRaises(ValueError):
            archify_candidate(m)

    def test_container_command_enforces_isolation_and_mount_contract(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)
            cmd=_sandbox_command("docker","arc-test",p/"source",p/"candidate.json",p/"out",os.getuid(),os.getgid())
        self.assertEqual(cmd[cmd.index("--network")+1],"none")
        self.assertIn("--read-only",cmd)
        self.assertEqual(cmd[cmd.index("--cap-drop")+1],"ALL")
        self.assertEqual(cmd[cmd.index("--pids-limit")+1],"256")
        self.assertIn("no-new-privileges:true",cmd)
        self.assertIn('--no-sandbox "$@"',SANDBOX_SCRIPT)
        mounts=[cmd[i+1] for i,x in enumerate(cmd[:-1]) if x=="--mount"]
        self.assertEqual(len(mounts),3)
        self.assertTrue(mounts[0].endswith(",readonly"))
        self.assertTrue(mounts[1].endswith(",readonly"))
        self.assertFalse(mounts[2].endswith(",readonly"))
        self.assertEqual(cmd[-4],SANDBOX_IMAGE)
        self.assertNotIn("/var/run/docker.sock"," ".join(cmd))
        self.assertNotIn("--env-file",cmd)
        self.assertNotIn("-e",cmd)

    def test_timeout_fails_closed_and_removes_container(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)
            upstream=p/"upstream"
            cli=upstream/"archify"/"bin"
            cli.mkdir(parents=True)
            (cli/"archify.mjs").write_text("",encoding="utf-8")
            timed_out=subprocess.TimeoutExpired(cmd=["docker","run"],timeout=5)
            completed=SimpleNamespace(returncode=0,stdout="",stderr="")
            with patch("scripts.architecture.archify_adapter.verify_sources",return_value=sample()), \
                 patch("scripts.architecture.archify_adapter._git_sha",return_value=UPSTREAM_SHA), \
                 patch("scripts.architecture.archify_adapter.subprocess.run",side_effect=[completed,timed_out,completed]) as run:
                with self.assertRaisesRegex(RenderError,"timed out"):
                    render(sample(),p,upstream,p/"out",timeout=5)
            self.assertEqual(run.call_count,3)
            self.assertEqual(run.call_args_list[2].args[0][:3],["docker","rm","--force"])

    def test_output_symlink_is_rejected_before_source_access(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root); target=p/"target"; target.mkdir(); link=p/"link"; link.symlink_to(target,target_is_directory=True)
            with self.assertRaises(RenderError):
                render(sample(),p/"missing-repo",p/"missing-upstream",link)

    def test_unavailable_pinned_image_fails_closed(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root); upstream=p/"upstream"; cli=upstream/"archify"/"bin"; cli.mkdir(parents=True)
            (cli/"archify.mjs").write_text("",encoding="utf-8")
            with patch("scripts.architecture.archify_adapter.verify_sources",return_value=sample()),patch("scripts.architecture.archify_adapter._git_sha",return_value=UPSTREAM_SHA),patch("scripts.architecture.archify_adapter.subprocess.run",return_value=type("P",(),{"returncode":1,"stdout":"","stderr":""})()) as run:
                with self.assertRaises(RenderError): render(sample(),p,upstream,p/"out")
            self.assertEqual(run.call_count,1)
            self.assertEqual(run.call_args.args[0][:3],["docker","image","inspect"])

if __name__=="__main__":
    unittest.main()
