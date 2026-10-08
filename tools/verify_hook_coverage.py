"""Exercise a rendered project's pinned hooks in an isolated fixture repository.

Run through the rendered project's prek group so its version remains canonical:
uv run --group prek python /path/to/tools/verify_hook_coverage.py prek.toml
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


def run_hook(root: Path, identifier: str) -> subprocess.CompletedProcess[str]:
    """Use all-files so prek includes broken symlinks from the Git index."""
    result = subprocess.run(
        ["prek", "run", identifier, "--all-files"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return result


def verify_fixture(
    root: Path,
    identifier: str,
    filename: str,
    content: bytes,
    *,
    fails: bool = False,
    skipped: bool = False,
    corrected: bytes | None = None,
) -> None:
    """Verify execution/filtering, exact bytes, and convergence after correction."""
    target = root / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    subprocess.run(["git", "add", "--", filename], cwd=root, check=True)
    try:
        result = run_hook(root, identifier)
        assert result.returncode == int(fails), result.stdout + result.stderr
        assert ("Skipped" in result.stdout) == skipped, result.stdout
        assert target.read_bytes() == (content if corrected is None else corrected)
        if corrected is not None:
            assert run_hook(root, identifier).returncode == 0
            assert target.read_bytes() == corrected
    finally:
        target.unlink()
        subprocess.run(
            ["git", "rm", "--cached", "-f", "--", filename], cwd=root, check=True
        )


def verify_hooks(config_path: Path) -> None:
    """Probe only audited upstream hooks, without installing the project."""
    with TemporaryDirectory(prefix="hook-coverage-") as directory:
        root = Path(directory)
        shutil.copyfile(config_path, root / "prek.toml")
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        cases = (
            ("check-xml", "probe.xml", b"<root/>\n", False, False),
            ("check-xml", "probe.xml", b"<root>\n", True, False),
            ("check-xml", "probe.txt", b"<root>\n", False, True),
            (
                "check-github-issue-forms",
                ".github/ISSUE_TEMPLATE/probe.yml",
                b"name: Probe\n",
                True,
                False,
            ),
            (
                "check-github-issue-forms",
                ".github/ISSUE_TEMPLATE/probe.md",
                b"name: Probe\n",
                False,
                True,
            ),
            (
                "check-github-issue-forms",
                ".github/ISSUE_TEMPLATE/config.yaml",
                b"blank_issues_enabled: false\n",
                False,
                True,
            ),
            (
                "check-github-issue-config",
                ".github/ISSUE_TEMPLATE/config.yaml",
                b"blank_issues_enabled: false\n",
                False,
                False,
            ),
            (
                "check-github-issue-config",
                ".github/ISSUE_TEMPLATE/config.yaml",
                b"blank_issues_enabled: invalid\n",
                True,
                False,
            ),
            (
                "check-github-workflows",
                ".github/workflows/probe.yml",
                b"name: Probe\non: push\njobs: {}\n",
                True,
                False,
            ),
            (
                "check-github-workflows",
                "outside.yml",
                b"name: Probe\non: push\njobs: {}\n",
                False,
                True,
            ),
            (
                "check-github-actions",
                ".github/actions/probe/action.yml",
                b"name: Probe\n",
                True,
                False,
            ),
            (
                "check-github-actions",
                ".github/workflows/probe.yml",
                b"name: Probe\n",
                False,
                True,
            ),
            (
                "check-dependabot",
                ".github/dependabot.yml",
                b"version: 2\nupdates: []\n",
                False,
                False,
            ),
            (
                "check-dependabot",
                ".github/dependabot.yml",
                b"version: 3\nupdates: []\n",
                True,
                False,
            ),
            (
                "check-dependabot",
                "dependabot.yml",
                b"version: 3\nupdates: []\n",
                False,
                True,
            ),
            (
                "check-renovate",
                "renovate.json5",
                b'{// comment\n extends: ["config:recommended"],}\n',
                False,
                False,
            ),
            ("check-renovate", "renovate.json5", b"{extends: 123}\n", True, False),
            ("check-renovate", "outside.json5", b"{extends: 123}\n", False, True),
        )
        for identifier, filename, content, fails, skipped in cases:
            verify_fixture(
                root, identifier, filename, content, fails=fails, skipped=skipped
            )
        verify_fixture(
            root,
            "fix-byte-order-marker",
            "bom.txt",
            b"\xef\xbb\xbfhello\n",
            fails=True,
            corrected=b"hello\n",
        )
        verify_fixture(
            root,
            "mixed-line-ending",
            "mixed.txt",
            b"one\ntwo\r\nthree\n",
            fails=True,
            corrected=b"one\ntwo\nthree\n",
        )
        verify_fixture(root, "mixed-line-ending", "windows.bat", b"one\r\ntwo\r\n")
        for identifier in ("fix-byte-order-marker", "mixed-line-ending"):
            verify_fixture(
                root,
                identifier,
                ".gitignore",
                b"\xef\xbb\xbfsealed\r\nbytes\n",
                skipped=True,
            )
            # This probe runs against the ai-rulez render in template CI.
            verify_fixture(
                root,
                identifier,
                ".continue/prompts/probe.yaml",
                b"\xef\xbb\xbfowned\r\nbytes\n",
                skipped=True,
            )
        for suffix in ("ps1", "psm1", "psd1", "PS1"):
            verify_fixture(
                root,
                "fix-byte-order-marker",
                f"script.{suffix}",
                b"\xef\xbb\xbf# calf\xc3\xa9\r\n",
                skipped=True,
            )
        executable = root / "executable.sh"
        executable.touch(mode=0o755)
        verify_fixture(
            root,
            "check-executables-have-shebangs",
            "executable.sh",
            b"hello\n",
            fails=True,
        )
        executable.touch(mode=0o755)
        verify_fixture(
            root,
            "check-executables-have-shebangs",
            "executable.sh",
            b"#!/bin/sh\nexit 0\n",
        )
        verify_fixture(
            root,
            "check-executables-have-shebangs",
            "ordinary.txt",
            b"hello\n",
            skipped=True,
        )
        link = root / "probe-link"
        link.symlink_to("does-not-exist")
        subprocess.run(["git", "add", "probe-link"], cwd=root, check=True)
        assert run_hook(root, "check-symlinks").returncode == 1
        (root / "does-not-exist").touch()
        assert run_hook(root, "check-symlinks").returncode == 0


if __name__ == "__main__":
    verify_hooks(Path(sys.argv[1]))
