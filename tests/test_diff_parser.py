"""Tests for the diff parser."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from diff_parser import parse_diff, DiffSummary, FileChange


SAMPLE_DIFF = """diff --git a/src/main.py b/src/main.py
index 1234567..abcdefg 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,5 @@
 import sys

-def main():
-    print("hello")
+def main(name: str = "world"):
+    print(f"hello {name}")
+
+if __name__ == "__main__":
+    main()
diff --git a/README.md b/README.md
new file mode 100644
--- /dev/null
+++ b/README.md
@@ -0,0 +1,3 @@
+# My Project
+
+This is a test project.
"""


def test_parse_diff_file_count():
    summary = parse_diff(SAMPLE_DIFF)
    assert summary.file_count == 2


def test_parse_diff_file_paths():
    summary = parse_diff(SAMPLE_DIFF)
    paths = [f.path for f in summary.files]
    assert "src/main.py" in paths
    assert "README.md" in paths


def test_parse_diff_additions():
    summary = parse_diff(SAMPLE_DIFF)
    assert summary.total_additions > 0


def test_parse_diff_deletions():
    summary = parse_diff(SAMPLE_DIFF)
    assert summary.total_deletions > 0


def test_parse_diff_languages():
    summary = parse_diff(SAMPLE_DIFF)
    assert "Python" in summary.languages
    assert "Markdown" in summary.languages


def test_parse_diff_new_file():
    summary = parse_diff(SAMPLE_DIFF)
    readme = [f for f in summary.files if f.path == "README.md"][0]
    assert readme.status == "added"


def test_parse_diff_modified_file():
    summary = parse_diff(SAMPLE_DIFF)
    main = [f for f in summary.files if f.path == "src/main.py"][0]
    assert main.status == "modified"


def test_parse_empty_diff():
    summary = parse_diff("")
    assert summary.file_count == 0
    assert summary.total_additions == 0


def test_to_prompt():
    summary = parse_diff(SAMPLE_DIFF)
    prompt = summary.to_prompt()
    assert "src/main.py" in prompt
    assert "README.md" in prompt
    assert "Python" in prompt


def test_parse_deleted_file():
    diff = """diff --git a/old.py b/old.py
deleted file mode 100644
--- a/old.py
+++ /dev/null
@@ -1,2 +0,0 @@
-def old():
-    pass
"""
    summary = parse_diff(diff)
    assert summary.files[0].status == "deleted"
    assert summary.total_deletions == 2
