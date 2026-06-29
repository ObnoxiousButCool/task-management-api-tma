#!/usr/bin/env python3
"""CI sanity check run by Agent OS after each code-generation iteration."""

import glob
import importlib
import os
import subprocess
import sys


def run(cmd):
    """Run a subprocess command and return its exit code."""
    # Defect #3: avoid shell=True so composed command strings cannot be injected.
    result = subprocess.run(cmd, shell=False, capture_output=True, text=True, timeout=120)
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0 and result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode


def pytest_executable(root):
    """Resolve the pytest executable in the local virtual environment."""
    venv = os.path.join(root, ".venv")
    windows_pytest = os.path.join(venv, "Scripts", "pytest.exe")
    linux_pytest = os.path.join(venv, "bin", "pytest")
    if os.path.exists(windows_pytest):
        return windows_pytest
    if os.path.exists(linux_pytest):
        return linux_pytest
    return None


def main():
    """Run syntax import checks and the iteration test suite."""
    root = os.path.dirname(os.path.abspath(__file__))
    try:
        importlib.import_module("app")
    except Exception as exc:
        print(f"Import check failed: {exc}", file=sys.stderr)
        return 1

    test_files = glob.glob(os.path.join(root, "tests", "test_*.py"))
    if not test_files:
        print("Import check passed; no test files found, skipping pytest")
        return 0

    pytest_exe = pytest_executable(root)
    if pytest_exe:
        pytest_cmd = [pytest_exe, *test_files, "--tb=short", "-q", "--no-header"]
    else:
        pytest_cmd = [sys.executable, "-m", "pytest", *test_files, "--tb=short", "-q", "--no-header"]
    rc = run(pytest_cmd)
    if rc == 0:
        print("CI check passed: import check and pytest succeeded")
    else:
        print("CI check failed: pytest reported failures", file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main())
