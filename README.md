# Day 2: AI Commit Message Bot

> DevOps + AI Project Series — Building intelligent infrastructure tools

A GitHub Action and CLI tool that analyzes git diffs and generates meaningful, conventional commit messages using a local LLM.

## Why This Project?

Writing good commit messages is tedious but important. This tool:
- Analyzes what actually changed (not just file names)
- Follows [Conventional Commits](https://www.conventionalcommits.org/) format
- Runs as a GitHub Action on every PR
- Works locally for staged/unstaged changes
- Uses local AI (Ollama) — no API keys, no cost

**Interview Talking Points:**
- CI/CD automation with AI
- Git diff parsing and analysis
- GitHub Actions integration
- Conventional Commits enforcement
- Developer experience tooling

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Git Diff    │────▶│ Diff Parser  │────▶│  LLM (local) │
│              │     │              │     │              │
│  staged, PR, │     │ file changes │     │  generates   │
│  or file     │     │ languages    │     │  commit msg  │
│              │     │ stats        │     │              │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                 │
                                          ┌──────▼───────┐
                                          │   Output     │
                                          │   - terminal │
                                          │   - PR comment│
                                          │   - JSON     │
                                          └──────────────┘
```

## Quick Start

```bash
# Prerequisites
brew install ollama
ollama pull llama3.2

# Generate message from staged changes
git add -A
python src/main.py

# Generate from a PR
python src/main.py --pr 42

# Dry run (see parsed diff)
python src/main.py --dry-run
```

## Usage

### CLI

```bash
# From staged changes (default)
python src/main.py

# From unstaged changes
python src/main.py --unstaged

# From a GitHub PR
python src/main.py --pr 42

# From a diff file
python src/main.py --file changes.diff

# Output formats
python src/main.py --output message     # Plain text (default)
python src/main.py --output github      # Markdown code block
python src/main.py --output json        # JSON with metadata

# Post as PR comment
python src/main.py --pr 42 --comment

# Dry run (no AI call)
python src/main.py --dry-run
```

### GitHub Action

Add to `.github/workflows/suggest-commit.yml`:

```yaml
name: AI Commit Suggestion
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  suggest:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: AkiraKane/ai-commit-bot@main
```

## What It Parses

| Metric | Example |
|--------|---------|
| Files changed | 3 files |
| Additions | +45 lines |
| Deletions | -12 lines |
| Languages | Python, YAML |
| File status | added, modified, deleted |
| Diff content | Actual code changes |

## Example Output

```bash
$ git add src/auth.py src/models.py
$ python src/main.py

Files changed: 2
Additions: +28
Deletions: -5
Languages: Python

feat(auth): add JWT token validation middleware
```

## Project Structure

```
ai-commit-bot/
├── src/
│   ├── main.py          # CLI entry point
│   ├── diff_parser.py   # Git diff parsing
│   └── llm.py           # Ollama/OpenAI client
├── tests/
│   └── test_diff_parser.py
├── .github/workflows/
│   ├── suggest-commit.yml  # PR comment workflow
│   └── ci.yml              # Test workflow
├── action.yml           # GitHub Action definition
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Key Design Decisions

### 1. Diff parsing before LLM
Instead of sending raw diffs to the LLM (which can be huge), we parse them first into structured summaries: file paths, change stats, languages, and truncated diff content.

### 2. Conventional Commits format
The LLM is instructed to output in Conventional Commits format (`feat:`, `fix:`, `docs:`, etc.) — a widely adopted standard that enables automated changelogs.

### 3. Fallback to OpenAI
If Ollama isn't available and `OPENAI_API_KEY` is set, the tool falls back to OpenAI's API. Best of both worlds — local when possible, cloud when needed.

### 4. Multiple output modes
- `message`: plain text for `git commit -m`
- `github`: markdown for PR comments
- `json`: for programmatic use

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Language | Python 3.10+ (stdlib only) | Zero dependencies |
| LLM | Ollama (local) | Free, private, no API keys |
| Fallback | OpenAI API | Cloud backup if needed |
| CI/CD | GitHub Actions | Standard for open source |
| Git | subprocess + gh CLI | Native integration |

## Running Tests

```bash
python -m pytest tests/ -v
```

## Series Progress

| Day | Project | Status |
|-----|---------|--------|
| 1 | [AI Dockerfile Generator](https://github.com/AkiraKane/ai-dockerfile-generator) | ✓ Done |
| 2 | AI Commit Message Bot | ✓ Done |
| 3 | AI Changelog Generator | Coming soon |
| ... | ... | ... |

## License

MIT
