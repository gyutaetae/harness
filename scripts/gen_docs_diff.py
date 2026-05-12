#!/usr/bin/env python3
"""Generate docs-diff.md from git diff against a baseline commit.

Usage: python scripts/gen_docs_diff.py <task_dir> <baseline_commit>
Example: python scripts/gen_docs_diff.py tasks/0-mvp a1b2c3d
"""

import subprocess
import sys
from pathlib import Path

from _utils import find_project_root

ROOT = find_project_root()


def git_diff(baseline: str, path: str = "docs/") -> str:
    r = subprocess.run(
        ["git", "diff", baseline, "--", path],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    return r.stdout


def git_diff_names(baseline: str) -> list[str]:
    r = subprocess.run(
        ["git", "diff", baseline, "--name-only", "--", "docs/"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    return [f for f in r.stdout.strip().splitlines() if f]


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python scripts/gen_docs_diff.py <task_dir> <baseline_commit>")
        sys.exit(1)

    task_dir = Path(sys.argv[1])
    baseline = sys.argv[2]
    task_name = task_dir.name.split("-", 1)[1] if "-" in task_dir.name else task_dir.name

    if not task_dir.is_absolute():
        task_dir = ROOT / task_dir

    changed_files = git_diff_names(baseline)
    out_file = task_dir / "docs-diff.md"

    if not changed_files:
        out_file.write_text(
            f"# docs-diff: {task_name}\n\nNo documentation changes.\n",
            encoding="utf-8",
        )
        print("  docs-diff.md: no changes")
        return

    lines = [f"# docs-diff: {task_name}\n", f"Baseline: `{baseline[:7]}`\n"]
    for fpath in changed_files:
        diff = git_diff(baseline, fpath)
        lines.append(f"## `{fpath}`\n")
        lines.append(f"```diff\n{diff}```\n")

    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"  docs-diff.md: {len(changed_files)} file(s)")


if __name__ == "__main__":
    main()
