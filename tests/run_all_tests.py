"""
Test Runner Script for Cyber Deception & Attack Detection Framework
Runs all unit and integration tests and prints an executive summary report.
"""
import sys
import os
import subprocess
import time


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print("=" * 70)
    print("AI-Driven Cyber Deception Framework - Automated Test Suite")
    print(f"Working Directory: {base_dir}")
    print(f"Python Executable: {sys.executable}")
    print("=" * 70)

    start_time = time.time()
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-v", "--tb=short"],
        cwd=base_dir,
        capture_output=False,
    )
    elapsed = time.time() - start_time

    print("=" * 70)
    if result.returncode == 0:
        print(f"SUCCESS: All test suites passed in {elapsed:.2f} seconds!")
    else:
        print(f"FAILED: Tests completed with exit code {result.returncode} in {elapsed:.2f} seconds.")
    print("=" * 70)

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
