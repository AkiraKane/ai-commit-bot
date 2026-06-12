"""Parse git diffs into structured, readable summaries for the LLM."""

import re
from dataclasses import dataclass, field


@dataclass
class FileChange:
    """A single file's changes."""
    path: str
    status: str  # added, modified, deleted, renamed
    additions: int = 0
    deletions: int = 0
    diff: str = ""


@dataclass
class DiffSummary:
    """Structured summary of all changes."""
    files: list[FileChange] = field(default_factory=list)
    total_additions: int = 0
    total_deletions: int = 0
    languages: list[str] = field(default_factory=list)

    @property
    def file_count(self) -> int:
        return len(self.files)

    def to_prompt(self) -> str:
        """Convert to a prompt-friendly string for the LLM."""
        parts = []
        parts.append(f"Changes: {self.file_count} files, "
                     f"+{self.total_additions} -{self.total_deletions}")
        if self.languages:
            parts.append(f"Languages: {', '.join(self.languages)}")
        parts.append("")

        for f in self.files:
            parts.append(f"--- {f.path} ({f.status}, +{f.additions} -{f.deletions}) ---")
            # Truncate large diffs
            diff_lines = f.diff.split("\n")[:50]
            parts.append("\n".join(diff_lines))
            if len(f.diff.split("\n")) > 50:
                parts.append(f"... ({len(f.diff.split(chr(10))) - 50} more lines)")
            parts.append("")

        return "\n".join(parts)


LANG_EXTENSIONS = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".go": "Go", ".rs": "Rust", ".java": "Java", ".rb": "Ruby",
    ".php": "PHP", ".cs": "C#", ".cpp": "C++", ".c": "C",
    ".swift": "Swift", ".kt": "Kotlin", ".sh": "Shell",
    ".yml": "YAML", ".yaml": "YAML", ".json": "JSON",
    ".md": "Markdown", ".tf": "Terraform", ".dockerfile": "Dockerfile",
}


def parse_diff(raw_diff: str) -> DiffSummary:
    """Parse a unified git diff into structured changes."""
    summary = DiffSummary()
    current_file = None
    lang_set = set()

    for line in raw_diff.split("\n"):
        # Detect file path
        if line.startswith("diff --git"):
            if current_file:
                summary.files.append(current_file)
            # Extract file path from "diff --git a/path b/path"
            match = re.search(r" b/(.+)$", line)
            path = match.group(1) if match else "unknown"
            current_file = FileChange(path=path, status="modified")

            # Detect language
            for ext, lang in LANG_EXTENSIONS.items():
                if path.endswith(ext):
                    lang_set.add(lang)
                    break

        elif line.startswith("new file"):
            if current_file:
                current_file.status = "added"
        elif line.startswith("deleted file"):
            if current_file:
                current_file.status = "deleted"
        elif line.startswith("rename from"):
            if current_file:
                current_file.status = "renamed"

        # Count additions/deletions
        elif line.startswith("+") and not line.startswith("+++"):
            if current_file:
                current_file.additions += 1
                summary.total_additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            if current_file:
                current_file.deletions += 1
                summary.total_deletions += 1

        # Collect diff content (skip binary files)
        elif not line.startswith("Binary"):
            if current_file:
                current_file.diff += line + "\n"

    # Don't forget the last file
    if current_file:
        summary.files.append(current_file)

    summary.languages = sorted(lang_set)
    return summary


def get_diff_from_git(staged: bool = True) -> str:
    """Get diff from git. Uses staged changes by default."""
    import subprocess
    cmd = ["git", "diff", "--cached"] if staged else ["git", "diff"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout


def get_diff_from_pr(pr_number: int, repo: str = "") -> str:
    """Get diff from a GitHub PR."""
    import subprocess
    cmd = ["gh", "pr", "diff", str(pr_number)]
    if repo:
        cmd.extend(["--repo", repo])
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout
