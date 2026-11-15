"""
InternIQ Command-Line Interface (CLI)
Provides command-line execution for evaluating opportunities, running vetting,
ranking matches, generating verified drafts, and checking scam signals.
"""

import argparse
import sys
from tools.fetchers import import_csv
from tools.schemas import Profile, Education, Skill, Preference, WorkMode


def main():
    parser = argparse.ArgumentParser(description="InternIQ CLI")
    parser.add_argument("--eval", action="store_true", help="Run full evaluation suite")
    parser.add_argument("--version", action="version", version="InternIQ 0.1.0")
    args = parser.parse_args()

    if args.eval:
        from eval.run_eval import run_full_evaluation
        run_full_evaluation()
    else:
        print("InternIQ v0.1.0 CLI. Use --eval to run evaluation suite, or run pytest.")


if __name__ == "__main__":
    main()
