#!/usr/bin/env python3
"""
Cross-platform script to run tests for pre-commit hooks.
Ensures a consistent testing environment.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Run tests with proper environment variables."""
    # Navigate to the component's root directory
    component_dir = Path(__file__).parent.parent
    os.chdir(component_dir)

    # Set required environment variables for testing
    test_env = os.environ.copy()
    test_env.update(
        {
            "DTR_API_SERVER_VERSION": "1.0.0-precommit",
            "DTR_VERSION": "2.0.0-precommit",
            "DTR_LOG_LEVEL": "WARNING",
            "DTR_DB_PASSWORD": "precommit-password",
            "DTR_ENCRYPTION_KEY": "precommit-key-that-is-32-bytes",
        }
    )

    # Run pytest with coverage, focusing on changed files if possible
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "--cov=.",
        "--cov-fail-under=8",  # Keep this low initially, increase as we add tests
        "-q",
    ]

    try:
        result = subprocess.run(cmd, env=test_env, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        # The pytest command will print its own output, so we just return the error code
        return e.returncode


if __name__ == "__main__":
    sys.exit(main())
