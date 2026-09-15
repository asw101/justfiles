import json
from pathlib import Path
import runpy
import shlex
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch


SANDBOX = Path(__file__).resolve().parents[1]
SCRIPTS = SANDBOX / "scripts"


class ShpoolSessionTests(unittest.TestCase):
    def test_environment_config(self):
        with (SANDBOX / "shpool.toml").open("rb") as config_file:
            config = tomllib.load(config_file)
        self.assertTrue(config["noread_etc_environment"])
        self.assertEqual(config["session_restore_mode"], "screen")
        for name in (
            "PATH",
            "GH_TOKEN",
            "COPILOT_GITHUB_TOKEN",
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
        ):
            self.assertIn(name, config["forward_env"])

    def launch(self, *args):
        with (
            patch.object(sys, "argv", ["shpool-session", *args]),
            patch("os.execvp") as execvp,
        ):
            runpy.run_path(str(SCRIPTS / "shpool-session"), run_name="__main__")
        return execvp.call_args.args

    def test_command_round_trip(self):
        args = [
            "",
            "a space",
            "single' and double\" quotes",
            "back\\slash",
            "two\nlines",
            '{"key": "{workspace}"}',
            "{unclosed",
            "$(exit 19); `exit 20` *",
            "--flag",
            "\u2603",
        ]
        program = "import json, sys; print(json.dumps(sys.argv[1:]))"
        binary, command = self.launch("-named", sys.executable, "-c", program, *args)
        self.assertEqual(binary, "terminal-session")
        self.assertEqual(
            command[:6], ["terminal-session", "shpool", "attach", "--dir", ".", "--cmd"]
        )
        self.assertEqual(command[7:], ["--", "-named"])
        self.assertNotIn("{", command[6])
        result = subprocess.run(
            shlex.split(command[6]), check=True, capture_output=True, text=True
        )
        self.assertEqual(json.loads(result.stdout), args)

    def test_invalid_names(self):
        for session in ("", ".", "..", "two words", "two\nlines", "a/b", "{var}", "a}"):
            with self.subTest(session=session), self.assertRaises(SystemExit):
                self.launch(session, "true")

    def test_usage(self):
        for args in ((), ("session",)):
            with self.subTest(args=args), self.assertRaises(SystemExit):
                self.launch(*args)

    def test_exec_failure_is_not_hidden(self):
        with (
            patch.object(sys, "argv", ["shpool-session", "session", "true"]),
            patch("os.execvp", side_effect=FileNotFoundError("terminal-session")),
            self.assertRaises(FileNotFoundError),
        ):
            runpy.run_path(str(SCRIPTS / "shpool-session"), run_name="__main__")


class AgentWrapperTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.bin = Path(temp.name)
        stub = self.bin / "shpool-session"
        stub.write_text(
            "#!/usr/bin/env python3\n"
            "import json, sys\n"
            "print(json.dumps(sys.argv[1:]))\n"
        )
        stub.chmod(0o755)
        self.env = {"PATH": f"{self.bin}:/usr/bin:/bin"}

    def launch(self, agent, *args, **env):
        return subprocess.run(
            ["bash", str(SCRIPTS / f"{agent}-shpool"), *args],
            env=self.env | env,
            capture_output=True,
            text=True,
        )

    def test_claude_and_codex(self):
        for agent in ("claude", "codex"):
            for session in (None, "feature"):
                with self.subTest(agent=agent, session=session):
                    env = {f"{agent.upper()}_SHPOOL_SESSION": session} if session else {}
                    result = self.launch(agent, "--flag", "a b", "", **env)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(
                        json.loads(result.stdout),
                        [session or agent, f"{agent}-auto", "--flag", "a b", ""],
                    )

    def test_codex_auto_defaults_and_arguments(self):
        (self.bin / "codex").symlink_to(self.bin / "shpool-session")
        for dockerfile in (
            SANDBOX / "Dockerfile",
            SANDBOX.parent / "cmbox" / "base" / "Dockerfile",
        ):
            line = next(
                line
                for line in dockerfile.read_text().splitlines()
                if "> /usr/local/bin/codex-auto " in line
            )
            script = shlex.split(line.removesuffix("\\"))[1].replace("\\n", "\n")
            for args in ([], ["resume", "--last"], ["a b", "", '{"key": "value"}']):
                with self.subTest(dockerfile=dockerfile, args=args):
                    result = subprocess.run(
                        ["bash", "-c", script, "codex-auto", *args],
                        env=self.env,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(
                        json.loads(result.stdout),
                        ["--yolo", *args],
                    )

    def test_copilot(self):
        for remote in ("1", "true", "yes", "0", "false", "no", ""):
            with self.subTest(remote=remote):
                result = self.launch(
                    "copilot",
                    "--prompt",
                    '{"key": "value"}',
                    "",
                    COPILOT_SHPOOL_SESSION="feature",
                    COPILOT_SESSION_NAME="my project",
                    COPILOT_REMOTE=remote,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                args = json.loads(result.stdout)
                self.assertEqual(args[:3], ["feature", "/bin/bash", "-lc"])
                self.assertIn("copilot update", args[3])
                expected = ["copilot-shpool", "--name", "my project"]
                if remote in ("1", "true", "yes"):
                    expected.append("--remote")
                self.assertEqual(args[4:], expected + ["--prompt", '{"key": "value"}', ""])

    def test_copilot_defaults(self):
        result = self.launch("copilot")
        self.assertEqual(result.returncode, 0, result.stderr)
        args = json.loads(result.stdout)
        self.assertEqual(args[0], "copilot")
        self.assertEqual(args[4:], ["copilot-shpool"])

    def test_invalid_remote(self):
        result = self.launch("copilot", COPILOT_REMOTE="invalid")
        self.assertEqual(result.returncode, 2)
        self.assertIn("COPILOT_REMOTE must be", result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
