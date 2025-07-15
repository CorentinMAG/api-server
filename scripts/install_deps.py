#!/usr/bin/env python3
"""
Dependency management script for api-server component.
Automates installation of production and development dependencies.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status"""
    print(f"🔄 {description}...")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {' '.join(cmd)}")
        print(f"   Exit code: {e.returncode}")
        print(f"   Error: {e.stderr}")
        return False


def install_dependencies(dev: bool = False) -> bool:
    """Install project dependencies"""
    success = True

    # Install production dependencies
    success &= run_command(["pip", "install", "-r", "requirements.txt"], "Installing production dependencies")

    # Install development dependencies if requested
    if dev:
        success &= run_command(
            ["pip", "install", "-r", "requirements-dev.txt"], "Installing development dependencies"
        )

    return success


def setup_pre_commit() -> bool:
    """Setup pre-commit hooks"""
    return run_command(["pre-commit", "install"], "Setting up pre-commit hooks")


def verify_installation() -> bool:
    """Verify that key packages are installed"""
    key_packages = ["flask", "sqlalchemy", "alembic", "dtr-common"]

    print("🔍 Verifying installation...")
    for package in key_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} not found")
            return False

    return True


def main():
    """Main installation script"""
    import argparse

    parser = argparse.ArgumentParser(description="Install api-server dependencies")
    parser.add_argument("--dev", action="store_true", help="Install development dependencies")
    parser.add_argument("--no-pre-commit", action="store_true", help="Skip pre-commit setup")

    args = parser.parse_args()

    print("🚀 API-Server Dependency Installation")
    print("=====================================")

    success = True

    # Install dependencies
    success &= install_dependencies(dev=args.dev)

    # Setup pre-commit hooks (only in dev mode)
    if args.dev and not args.no_pre_commit:
        success &= setup_pre_commit()

    # Verify installation
    success &= verify_installation()

    if success:
        print("\n🎉 Installation completed successfully!")
        if args.dev:
            print("💡 Development environment ready for testing and development")
        sys.exit(0)
    else:
        print("\n💥 Installation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
