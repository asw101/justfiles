from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class CodexInstallTests(unittest.TestCase):
    def test_images_use_the_standalone_installer(self):
        for dockerfile in (
            ROOT / "sandbox" / "Dockerfile",
            ROOT / "cmbox" / "base" / "Dockerfile",
        ):
            with self.subTest(dockerfile=dockerfile):
                source = dockerfile.read_text()
                for line in source.splitlines():
                    if line.startswith("RUN brew install "):
                        self.assertNotIn("codex", shlex.split(line))
                self.assertIn(
                    "RUN curl -fsSL https://chatgpt.com/codex/install.sh "
                    "-o /tmp/codex-install.sh && \\\n"
                    "    CODEX_NON_INTERACTIVE=1 sh /tmp/codex-install.sh && \\\n"
                    "    rm -f /tmp/codex-install.sh",
                    source,
                )

    def test_machine_users_get_the_managed_package_not_shared_credentials(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tool_home = root / "tools"
            package = tool_home / ".codex/packages/standalone"
            release = package / "releases/test"
            (release / "bin").mkdir(parents=True)
            binary = release / "bin/codex"
            binary.touch()
            (package / "current").symlink_to(release)
            (tool_home / ".codex/auth.json").write_text('{"test": "private"}')
            skel = root / "skel"
            source = (ROOT / "cmbox/base/Dockerfile").read_text()
            command = next(
                block.split("\n\n", 1)[0]
                for block in source.split("\nRUN ")
                if block.startswith("install -d /etc/skel/.codex/packages")
            )
            command = command.replace("/opt/cmbox", shlex.quote(str(tool_home)))
            command = command.replace("/etc/skel", shlex.quote(str(skel)))
            subprocess.run(
                ["/bin/sh", "-c", command],
                check=True, capture_output=True, text=True, timeout=5,
            )
            for user in ("alice", "bob"):
                home = root / user
                shutil.copytree(skel, home, symlinks=True)
                managed_binary = home / ".codex/packages/standalone/current/bin/codex"
                self.assertEqual(managed_binary.resolve(strict=True), binary)
                self.assertFalse((home / ".codex").is_symlink())
                self.assertFalse((home / ".codex/auth.json").exists())


if __name__ == "__main__":
    unittest.main()
