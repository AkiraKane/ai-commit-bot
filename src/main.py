#!/usr/bin/env python3
"""AI Commit Message Bot — generate commit messages from git diffs."""

import argparse
import sys
import os

from diff_parser import parse_diff, get_diff_from_git, get_diff_from_pr, DiffSummary
from llm import generate_commit_message, check_ollama


def format_for_github(message: str) -> str:
    """Format commit message as a GitHub-friendly comment."""
    return f"**Suggested commit message:**\n\n```\n{message}\n```"


def main():
    parser = argparse.ArgumentParser(
        description="Generate AI commit messages from git diffs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                      # From staged changes
  %(prog)s --unstaged           # From unstaged changes
  %(prog)s --pr 42              # From a PR
  %(prog)s --pr 42 --comment    # Post as PR comment
  %(prog)s --file changes.diff  # From a diff file
  %(prog)s --dry-run            # Show parsed diff only
        """,
    )
    parser.add_argument("--unstaged", action="store_true",
                        help="Use unstaged changes instead of staged")
    parser.add_argument("--pr", type=int, metavar="NUM",
                        help="Get diff from a GitHub PR number")
    parser.add_argument("--repo", default="",
                        help="GitHub repo (owner/repo) for PR diff")
    parser.add_argument("--file", metavar="PATH",
                        help="Read diff from a file")
    parser.add_argument("--comment", action="store_true",
                        help="Post as GitHub PR comment (requires --pr)")
    parser.add_argument("--ollama-url", default="http://localhost:11434",
                        help="Ollama API URL")
    parser.add_argument("--model", default="llama3.2",
                        help="Ollama model to use")
    parser.add_argument("--output", choices=["message", "github", "json"],
                        default="message", help="Output format")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show parsed diff without generating message")

    args = parser.parse_args()

    # Get the diff
    if args.file:
        with open(args.file) as f:
            raw_diff = f.read()
    elif args.pr:
        raw_diff = get_diff_from_pr(args.pr, args.repo)
    else:
        raw_diff = get_diff_from_git(staged=not args.unstaged)

    if not raw_diff.strip():
        print("No changes found.", file=sys.stderr)
        sys.exit(1)

    # Parse the diff
    summary = parse_diff(raw_diff)

    # Show analysis
    print(f"Files changed: {summary.file_count}")
    print(f"Additions: +{summary.total_additions}")
    print(f"Deletions: -{summary.total_deletions}")
    if summary.languages:
        print(f"Languages: {', '.join(summary.languages)}")
    print()

    if args.dry_run:
        print("--- Parsed diff summary ---")
        print(summary.to_prompt()[:2000])
        return

    # Check Ollama
    if not check_ollama(args.ollama_url):
        print("Warning: Ollama not running. Trying OpenAI fallback...",
              file=sys.stderr)
        if not os.environ.get("OPENAI_API_KEY"):
            print("Error: Neither Ollama nor OPENAI_API_KEY available.",
                  file=sys.stderr)
            sys.exit(1)

    # Generate commit message
    print("Generating commit message...")
    try:
        message = generate_commit_message(
            summary.to_prompt(),
            ollama_url=args.ollama_url,
            model=args.model,
        )
    except ConnectionError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Output
    if args.output == "json":
        import json
        print(json.dumps({"message": message, "files": summary.file_count}))
    elif args.output == "github":
        print(format_for_github(message))
    else:
        print(message)

    # Post as PR comment if requested
    if args.comment and args.pr:
        _post_pr_comment(args.pr, message, args.repo)


def _post_pr_comment(pr_number: int, message: str, repo: str = ""):
    """Post the commit message as a PR comment."""
    import subprocess
    comment = format_for_github(message)
    cmd = ["gh", "pr", "comment", str(pr_number), "--body", comment]
    if repo:
        cmd.extend(["--repo", repo])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"\nPosted comment on PR #{pr_number}")
    else:
        print(f"\nFailed to post comment: {result.stderr}", file=sys.stderr)


if __name__ == "__main__":
    main()
