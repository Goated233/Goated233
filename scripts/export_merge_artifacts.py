#!/usr/bin/env python3
"""Export merge artifacts for environments that cannot push to GitHub.

The script creates three review/merge artifacts from a Git commit range:

* alpha_omega_platform.patch: binary-safe patch from base..head
* alpha_omega_changed_files.txt: explicit changed-file manifest
* alpha_omega_full_file_contents.md: full contents for each changed text file

It intentionally uses only the Python standard library so it works before
project dependencies are installed.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


LANG_BY_SUFFIX = {
    ".py": "python",
    ".md": "markdown",
    ".toml": "toml",
    ".txt": "text",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".ini": "ini",
    ".example": "dotenv",
    ".gitignore": "gitignore",
}


def run_git(args: list[str], *, text: bool = True) -> str | bytes:
    completed = subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=text,
    )
    return completed.stdout


def changed_files(base: str, head: str) -> list[str]:
    output = run_git(["diff", "--name-only", "--diff-filter=ACMR", f"{base}..{head}"])
    assert isinstance(output, str)
    return [line.strip() for line in output.splitlines() if line.strip()]


def file_at_revision(path: str, revision: str) -> str | None:
    try:
        output = run_git(["show", f"{revision}:{path}"])
    except subprocess.CalledProcessError:
        return None
    assert isinstance(output, str)
    return output


def code_fence_language(path: str) -> str:
    file_path = Path(path)
    if file_path.name in LANG_BY_SUFFIX:
        return LANG_BY_SUFFIX[file_path.name]
    return LANG_BY_SUFFIX.get(file_path.suffix, "text")


def render_full_contents(files: list[str], head: str) -> str:
    lines = [
        "# Alpha Omega Arcade - Full Changed File Contents",
        "",
        "Generated from the local Git repository for manual review/merge.",
        "",
    ]
    for path in files:
        content = file_at_revision(path, head)
        lines.append(f"## `{path}`")
        lines.append("")
        if content is None:
            lines.append("_File is not present at the selected revision._")
            lines.append("")
            continue
        language = code_fence_language(path)
        lines.append(f"```{language}")
        lines.append(content.rstrip("\n"))
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def write_artifacts(base: str, head: str, out_dir: Path, *, stdout_contents: bool) -> int:
    files = changed_files(base, head)
    full_contents = render_full_contents(files, head)

    if stdout_contents:
        sys.stdout.write(full_contents)
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)

    patch = run_git(["diff", "--binary", f"{base}..{head}"], text=False)
    assert isinstance(patch, bytes)
    (out_dir / "alpha_omega_platform.patch").write_bytes(patch)
    (out_dir / "alpha_omega_changed_files.txt").write_text("\n".join(files) + "\n", encoding="utf-8")
    (out_dir / "alpha_omega_full_file_contents.md").write_text(full_contents, encoding="utf-8")

    print(f"Wrote {len(files)} changed file entries to {out_dir}")
    print(f"- {out_dir / 'alpha_omega_platform.patch'}")
    print(f"- {out_dir / 'alpha_omega_changed_files.txt'}")
    print(f"- {out_dir / 'alpha_omega_full_file_contents.md'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Export patch and full file contents for manual GitHub merge.")
    parser.add_argument("--base", default="HEAD~1", help="Base revision before the platform changes.")
    parser.add_argument("--head", default="HEAD", help="Head revision to export.")
    parser.add_argument("--out", default="dist", help="Output directory for merge artifacts.")
    parser.add_argument(
        "--stdout-contents",
        action="store_true",
        help="Print full changed-file contents to stdout instead of writing artifacts.",
    )
    args = parser.parse_args()
    return write_artifacts(args.base, args.head, Path(args.out), stdout_contents=args.stdout_contents)


if __name__ == "__main__":
    raise SystemExit(main())
