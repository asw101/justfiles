import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SANDBOX = Path(__file__).resolve().parents[1]
JUST = shutil.which("just")


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(JUST, "just is required to exercise sandbox recipes")
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.project = self.root / "project with spaces"
        self.project.mkdir()
        self.log = self.root / "calls.jsonl"
        self.env = {
            "HOME": str(self.root),
            "PATH": f"{self.bin}:/usr/bin:/bin",
            "TEST_LOG": str(self.log),
            "GH_TOKEN": "dummy-github-token",
        }
        stub = (
            "#!/usr/bin/env python3\n"
            "import json, os, sys\n"
            "tool = os.path.basename(sys.argv[0])\n"
            "args = sys.argv[1:]\n"
            "with open(os.environ['TEST_LOG'], 'a') as log:\n"
            "    log.write(json.dumps(dict(tool=tool, args=args,\n"
            "        token=os.environ.get('COPILOT_GITHUB_TOKEN'),\n"
            "        gh_token=os.environ.get('GH_TOKEN'))) + '\\n')\n"
            "if tool == 'just':\n"
            "    assert args[0] == '--justfile' and args[2] == 'get', args\n"
            "    print('dummy-copilot-token')\n"
            "    sys.exit(int(os.environ.get('TEST_SECRET_EXIT', '0')))\n"
            "if args == ['system', 'status']:\n"
            "    print('status running')\n"
            "    sys.exit(0)\n"
            "if args[0] == 'inspect':\n"
            "    sys.exit(0 if os.environ.get('TEST_EXISTS') == '1' else 1)\n"
            "action = 'probe' if args[0] == 'exec' and args[-1] == '/usr/bin/true' else args[0]\n"
            "assert action in ('start', 'run', 'exec', 'probe', 'stop', 'delete'), args\n"
            "code = int(os.environ.get('TEST_' + action.upper() + '_EXIT', '0'))\n"
            "if code:\n"
            "    print('simulated ' + action + ' failure', file=sys.stderr)\n"
            "sys.exit(code)\n"
        )
        for tool in ("container", "just"):
            path = self.bin / tool
            path.write_text(stub)
            path.chmod(0o755)

    def run_recipe(self, *args, **env):
        return subprocess.run(
            [JUST, "--justfile", str(SANDBOX / "Justfile"), *args],
            cwd=self.project,
            env=self.env | env,
            capture_output=True,
            text=True,
        )

    def calls(self, tool="container"):
        if not self.log.exists():
            return []
        return [
            call
            for line in self.log.read_text().splitlines()
            if (call := json.loads(line))["tool"] == tool
        ]

    def test_up_creates_default_with_token_and_shell(self):
        result = self.run_recipe("up", COPILOT_SANDBOX_NAME="ignored-old-name")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.calls()
        self.assertEqual([call["args"][0] for call in calls], ["system", "inspect", "run", "exec"])
        self.assertEqual(calls[1]["args"], ["inspect", "sandbox"])
        creation = calls[2]
        args = creation["args"]
        self.assertEqual(args[args.index("--name") + 1], "sandbox")
        self.assertIn("-d", args)
        self.assertNotIn("--rm", args)
        self.assertIn("COPILOT_GITHUB_TOKEN", args)
        self.assertIn("GH_TOKEN", args)
        self.assertEqual(creation["token"], "dummy-copilot-token")
        self.assertEqual(creation["gh_token"], "dummy-github-token")
        self.assertEqual(
            args[args.index("--volume") + 1],
            f"{self.project}:/home/agent/pwd",
        )
        self.assertEqual(args[-3:], ["/bin/bash", "-lc", "exec sleep infinity"])
        self.assertEqual(calls[-1]["args"], ["exec", "-it", "sandbox", "/bin/bash", "-l"])
        self.assertEqual(len(self.calls("just")), 1)

    def test_named_up_preserves_extra_arguments(self):
        result = self.run_recipe(
            "up", "dev", "--env", "MESSAGE=two words", COPILOT_SECRET_NAME="custom/token"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        creation = next(call["args"] for call in self.calls() if call["args"][0] == "run")
        self.assertEqual(creation[creation.index("--name") + 1], "dev")
        self.assertIn("MESSAGE=two words", creation)
        self.assertEqual(self.calls("just")[0]["args"][-1], "custom/token")
        self.assertEqual(self.calls()[-1]["args"], ["exec", "-it", "dev", "/bin/bash", "-l"])

    def test_up_reopens_existing_container_without_fetching_secret(self):
        result = self.run_recipe("up", "copilot-sandbox", TEST_EXISTS="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            [call["args"] for call in self.calls()],
            [
                ["system", "status"],
                ["inspect", "copilot-sandbox"],
                ["start", "copilot-sandbox"],
                ["exec", "-it", "copilot-sandbox", "/bin/bash", "-l"],
            ],
        )
        self.assertEqual(self.calls("just"), [])

    def test_up_attaches_if_already_running(self):
        result = self.run_recipe("up", "dev", TEST_EXISTS="1", TEST_START_EXIT="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(["exec", "dev", "/usr/bin/true"], [call["args"] for call in self.calls()])
        self.assertEqual(self.calls()[-1]["args"], ["exec", "-it", "dev", "/bin/bash", "-l"])
        self.assertEqual(self.calls("just"), [])

    def test_up_surfaces_start_failure_without_recreating(self):
        result = self.run_recipe(
            "up", "dev", TEST_EXISTS="1", TEST_START_EXIT="1", TEST_PROBE_EXIT="1"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("couldn't be started", result.stderr)
        self.assertEqual(self.calls("just"), [])
        self.assertEqual(self.calls()[-1]["args"], ["exec", "dev", "/usr/bin/true"])

    def test_up_does_not_create_when_secret_lookup_fails(self):
        result = self.run_recipe("up", TEST_SECRET_EXIT="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual([call["args"][0] for call in self.calls()], ["system", "inspect"])

    def test_up_does_not_attach_when_creation_fails(self):
        result = self.run_recipe("up", TEST_RUN_EXIT="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("simulated run failure", result.stderr)
        self.assertEqual(self.calls()[-1]["args"][0], "run")

    def test_down_stops_default_without_deleting(self):
        result = self.run_recipe("down")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            [call["args"] for call in self.calls()],
            [["system", "status"], ["stop", "--", "sandbox"]],
        )
        self.assertEqual(self.calls("just"), [])

    def test_down_stops_named_container_without_deleting(self):
        result = self.run_recipe("down", "dev")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls()[-1]["args"], ["stop", "--", "dev"])
        self.assertNotIn("delete", [call["args"][0] for call in self.calls()])

    def test_down_surfaces_stop_failure(self):
        result = self.run_recipe("down", "dev", TEST_STOP_EXIT="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("simulated stop failure", result.stderr)
        self.assertNotIn("delete", [call["args"][0] for call in self.calls()])

    def test_delete_requires_explicit_name(self):
        result = self.run_recipe("delete")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.calls(), [])

    def test_only_short_lifecycle_names_are_exposed(self):
        result = self.run_recipe("--summary")
        self.assertEqual(result.returncode, 0, result.stderr)
        recipes = result.stdout.split()
        self.assertIn("up", recipes)
        self.assertIn("down", recipes)
        self.assertNotIn("run-persistent", recipes)
        self.assertNotIn("run-copilot-persistent", recipes)

    def test_explicit_delete_still_removes_container(self):
        result = self.run_recipe("delete", "dev")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            [call["args"] for call in self.calls()],
            [["system", "status"], ["stop", "dev"], ["delete", "dev"]],
        )


if __name__ == "__main__":
    unittest.main()
