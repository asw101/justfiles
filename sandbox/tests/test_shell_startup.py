from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class ShellStartupTests(unittest.TestCase):
    def test_logins_open_a_plain_shell(self):
        for dockerfile, image_home in (
            (ROOT / "sandbox" / "Dockerfile", "/home/agent"),
            (ROOT / "cmbox" / "base" / "Dockerfile", "/opt/cmbox"),
        ):
            with self.subTest(dockerfile=dockerfile), tempfile.TemporaryDirectory() as temp:
                home = Path(temp)
                lines = dockerfile.read_text().splitlines()
                start = next(
                    i for i, line in enumerate(lines)
                    if line.startswith("RUN echo ") and f"{image_home}/.bashrc" in line
                )
                end = start
                while lines[end].endswith("\\"):
                    end += 1
                command = "\n".join(lines[start:end + 1]).removeprefix("RUN ")
                for name in (".bashrc", ".profile"):
                    command = command.replace(
                        f"> {image_home}/{name}", f"> {shlex.quote(str(home / name))}"
                    )
                env = {"HOME": temp, "PATH": "/usr/bin:/bin"}
                subprocess.run(
                    ["/bin/sh", "-c", command],
                    env=env, check=True, capture_output=True, text=True, timeout=5,
                )
                for connection in ("", "192.0.2.1 12345 192.0.2.2 22"):
                    for interactive in (False, True):
                        with self.subTest(connection=connection, interactive=interactive):
                            # Functions detect accidental launches without starting real sessions.
                            shell = (
                                "tmux() { printf 'unexpected tmux launch\\n'; return 1; }; "
                                "shpool() { printf 'unexpected shpool launch\\n'; return 1; }; "
                                '. "$HOME/.profile"; '
                                "printf 'shell ready\\n'; "
                                'printf "%s\\n" "$PATH"'
                            )
                            result = subprocess.run(
                                ["/bin/bash", "--noprofile", "--norc",
                                 "-ic" if interactive else "-c", shell],
                                env=env | {"SSH_CONNECTION": connection},
                                stdin=subprocess.DEVNULL, capture_output=True,
                                text=True, timeout=5,
                            )
                            self.assertEqual(result.returncode, 0, result.stderr)
                            output = result.stdout.splitlines()
                            self.assertEqual(output[0], "shell ready")
                            self.assertEqual(len(output), 2)
                            self.assertIn("/home/linuxbrew/.linuxbrew/bin", output[1])
                            self.assertTrue(output[1].endswith("/usr/bin:/bin"))


if __name__ == "__main__":
    unittest.main()
