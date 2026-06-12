"""LLM client for generating commit messages via Ollama or OpenAI."""

import json
import urllib.request
import urllib.error
import os
from typing import Optional


SYSTEM_PROMPT = """You are an expert at writing clear, conventional commit messages.

Follow the Conventional Commits format:
<type>(<scope>): <description>

Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert

Rules:
- Use imperative mood ("add" not "added")
- Keep the first line under 72 characters
- Be specific about what changed
- If multiple files changed, summarize the overall intent
- Do NOT include file names in the subject line
- Add a blank line then a body if changes are complex

Output ONLY the commit message. No explanations, no markdown, no code blocks."""


def generate_commit_message(
    diff_summary: str,
    ollama_url: str = "http://localhost:11434",
    model: str = "llama3.2",
) -> str:
    """Generate a commit message from a diff summary."""
    user_prompt = f"""Write a commit message for these changes:

{diff_summary}"""

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {"temperature": 0.3},
    }

    try:
        req = urllib.request.Request(
            f"{ollama_url}/api/chat",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            message = result["message"]["content"].strip()
            # Strip markdown code blocks if present
            if message.startswith("```"):
                first = message.find("\n")
                if first != -1:
                    message = message[first + 1:]
                if message.endswith("```"):
                    message = message[:-3]
            return message.strip()
    except urllib.error.URLError:
        # Fallback to OpenAI if configured
        openai_key = os.environ.get("OPENAI_API_KEY")
        if openai_key:
            return _generate_openai(diff_summary, openai_key)
        raise ConnectionError(
            f"Cannot connect to Ollama at {ollama_url}. "
            "Start Ollama: ollama serve"
        )


def _generate_openai(diff_summary: str, api_key: str) -> str:
    """Fallback: generate via OpenAI API."""
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Write a commit message for:\n\n{diff_summary}"},
        ],
        "temperature": 0.3,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"].strip()


def check_ollama(ollama_url: str = "http://localhost:11434") -> bool:
    """Check if Ollama is running."""
    try:
        req = urllib.request.Request(f"{ollama_url}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError):
        return False
