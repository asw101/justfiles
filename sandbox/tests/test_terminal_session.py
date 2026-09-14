import fcntl
import json
import os
from pathlib import Path
import pty
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import termios
import time
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
ENABLE_MOUSE = b"\x1b[?1003h\x1b[?1006h"


def controlling_terminal():
    os.setsid()
    fcntl.ioctl(0, termios.TIOCSCTTY, 0)


class TerminalSessionTests(unittest.TestCase):
    def start_command(self, command, redirect=False, env=None):
        master, slave = pty.openpty()
        self.addCleanup(os.close, master)
        self.addCleanup(os.close, slave)
        termios.tcsetwinsize(slave, (24, 80))
        settings = termios.tcgetattr(slave)
        settings[3] &= ~termios.ECHO
        termios.tcsetattr(slave, termios.TCSANOW, settings)
        process = subprocess.Popen(
            command,
            stdin=slave,
            stdout=subprocess.PIPE if redirect else slave,
            stderr=subprocess.PIPE if redirect else slave,
            preexec_fn=controlling_terminal,
            env=env,
        )

        def stop():
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

        self.addCleanup(stop)
        return process, master, slave, settings

    def start_terminal(self, program, redirect=False):
        return self.start_command(
            [sys.executable, str(SCRIPTS / "terminal-session"), sys.executable, "-c", program],
            redirect=redirect,
        )

    def read_until(self, master, marker):
        output = b""
        deadline = time.monotonic() + 5
        while marker not in output:
            remaining = deadline - time.monotonic()
            self.assertGreater(remaining, 0, output)
            ready, _, _ = select.select([master], [], [], remaining)
            self.assertTrue(ready, output)
            output += os.read(master, 4096)
        return output

    def assert_restored(self, master, slave, settings):
        output = self.read_until(master, b"\x1b[?1049l")
        for mode in (9, 1000, 1001, 1002, 1003, 1005, 1006, 1015, 1016, 1004, 2004):
            self.assertIn(f"\x1b[?{mode}l".encode(), output)
        self.assertIn(b"\x1b[?25h", output)
        self.assertNotIn(b"\x1bc", output)
        self.assertNotIn(b"\x1b[2J", output)
        self.assertEqual(termios.tcgetattr(slave), settings)
        return output

    def test_exit_restores_terminal_and_preserves_status(self):
        for status in (0, 23):
            with self.subTest(status=status):
                program = (
                    "import os, tty; tty.setraw(0); "
                    f"os.write(1, {ENABLE_MOUSE!r}); raise SystemExit({status})"
                )
                process, master, slave, settings = self.start_terminal(program)
                self.assertEqual(process.wait(timeout=5), status)
                output = self.assert_restored(master, slave, settings)
                self.assertIn(ENABLE_MOUSE, output)

    def test_signals_are_forwarded_before_cleanup(self):
        for signum in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM):
            with self.subTest(signum=signum):
                program = (
                    "import os, signal, time, tty; "
                    "signal.signal(signal.SIGINT, signal.SIG_DFL); "
                    "tty.setraw(0); "
                    f"os.write(1, {ENABLE_MOUSE!r} + b'READY'); time.sleep(30)"
                )
                process, master, slave, settings = self.start_terminal(program)
                self.read_until(master, b"READY")
                process.send_signal(signum)
                self.assertEqual(process.wait(timeout=5), 128 + signum)
                self.assert_restored(master, slave, settings)

    def test_redirected_output_has_no_cleanup_sequences(self):
        program = (
            "import os, tty; tty.setraw(0); "
            f"os.write(os.open('/dev/tty', os.O_WRONLY), {ENABLE_MOUSE!r}); "
            "print('captured output')"
        )
        process, master, slave, settings = self.start_terminal(program, redirect=True)
        stdout, stderr = process.communicate(timeout=5)
        self.assertEqual(process.returncode, 0, stderr)
        self.assertEqual(stdout, b"captured output\n")
        self.assertEqual(stderr, b"")
        self.assert_restored(master, slave, settings)

    @unittest.skipUnless(shutil.which("shpool"), "shpool is required for the integration test")
    def test_shpool_detach_reattach_and_exit(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        socket_dir = root / "shpool"
        socket_dir.mkdir()
        socket = socket_dir / "shpool.socket"
        env = {
            "HOME": str(root),
            "XDG_RUNTIME_DIR": str(root),
            "XDG_CONFIG_HOME": str(root),
            "PATH": f"{SCRIPTS}:{os.environ['PATH']}",
            "SHELL": "/bin/bash",
            "TERM": "xterm-256color",
        }
        shpool = [
            shutil.which("shpool"),
            "--socket", str(socket),
            "--config-file", str(SCRIPTS.parent / "shpool.toml"),
        ]
        daemon = subprocess.Popen(
            [*shpool, "daemon"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
        )

        def stop_daemon():
            try:
                subprocess.run(
                    [*shpool, "kill", "mouse-test"], env=env, capture_output=True, timeout=5
                )
            finally:
                daemon.terminate()
                daemon.communicate(timeout=5)

        self.addCleanup(stop_daemon)
        deadline = time.monotonic() + 5
        while not socket.exists():
            self.assertIsNone(daemon.poll())
            self.assertLess(time.monotonic(), deadline)
            time.sleep(0.01)

        program = (
            "import os, tty\n"
            "tty.setraw(0)\n"
            f"os.write(1, {ENABLE_MOUSE!r} + b'READY')\n"
            "while True:\n"
            "    char = os.read(0, 1)\n"
            "    if char == b'q':\n"
            "        break\n"
            "    os.write(1, b'ALIVE')\n"
        )
        command = [
            sys.executable, str(SCRIPTS / "shpool-session"), "mouse-test",
            sys.executable, "-c", program,
        ]
        process, master, slave, settings = self.start_command(command, env=env)
        self.read_until(master, b"READY")
        os.write(master, b"\x00\x11")
        self.assertEqual(process.wait(timeout=5), 0)
        self.assert_restored(master, slave, settings)

        deadline = time.monotonic() + 5
        while True:
            sessions = subprocess.run(
                [*shpool, "list"], env=env, capture_output=True, text=True, check=True, timeout=5
            ).stdout
            if "disconnected" in sessions.lower():
                break
            self.assertLess(time.monotonic(), deadline, sessions)
            time.sleep(0.01)

        # A reattach must retain the original process, ignoring this new command.
        command = [sys.executable, str(SCRIPTS / "shpool-session"), "mouse-test", "false"]
        process, master, slave, settings = self.start_command(command, env=env)
        self.read_until(master, b"READY")
        os.write(master, b"p")
        self.read_until(master, b"ALIVE")
        os.write(master, b"q")
        self.assertEqual(process.wait(timeout=5), 0)
        self.assert_restored(master, slave, settings)

    def test_noninteractive_arguments_and_status_are_preserved(self):
        args = ["a b", "", '{"key": "value"}']
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "terminal-session"),
                sys.executable,
                "-c",
                "import json, sys; print(json.dumps(sys.argv[1:])); sys.exit(19)",
                *args,
            ],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertEqual(result.returncode, 19, result.stderr)
        self.assertEqual(json.loads(result.stdout), args)
        self.assertEqual(result.stderr, "")

    def test_usage_and_missing_command_fail(self):
        for args, message in (
            ([], "usage: terminal-session"),
            (["/nonexistent-terminal-session-command"], "No such file or directory"),
        ):
            with self.subTest(args=args):
                result = subprocess.run(
                    [sys.executable, str(SCRIPTS / "terminal-session"), *args],
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
