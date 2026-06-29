#!/usr/bin/env python3
"""CI sanity check run by Agent OS after each code-generation iteration."""

import glob
import os
import subprocess
import sys


def run(cmd):
    """Run a subprocess command and return its exit code."""
    # Defect #9: avoid shell=True so composed command strings cannot be injected.
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
    python_exe = os.path.join(root, ".venv", "Scripts", "python.exe")
    if not os.path.exists(python_exe):
        python_exe = os.path.join(root, ".venv", "bin", "python")
    if not os.path.exists(python_exe):
        python_exe = sys.executable

    # Defect #9: perform the import check without shell=True and with the project interpreter.
    import_rc = run([python_exe, "-c", "import app"])
    if import_rc != 0:
        print("CI check failed: import check failed", file=sys.stderr)
        return import_rc

    test_files = glob.glob(os.path.join(root, "tests", "test_*.py"))
    if not test_files:
        print("Import check passed; no test files found, skipping pytest")
        return 0

    pytest_exe = pytest_executable(root)
    if pytest_exe:
        pytest_cmd = [pytest_exe, *test_files, "--tb=short", "-q", "--no-header"]
    else:
        pytest_cmd = [python_exe, "-m", "pytest", *test_files, "--tb=short", "-q", "--no-header"]
    rc = run(pytest_cmd)
    if rc == 0:
        print("CI check passed: import check and pytest succeeded")
    else:
        print("CI check failed: pytest reported failures", file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main())
