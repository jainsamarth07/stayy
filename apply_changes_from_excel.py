"""
Apply incremental changes from Project_Files.xlsx to an existing project.

Unlike setup_from_excel.py (which recreates everything from scratch), this
script compares the Excel contents against files already on disk and ONLY
writes files that are new or different.  Perfect for updating projects that
were initially cloned from a Git repo.

Usage:
    python apply_changes_from_excel.py                        # dry-run (preview only)
    python apply_changes_from_excel.py --apply                # apply changes
    python apply_changes_from_excel.py --apply --target /path # apply to specific dir
    python apply_changes_from_excel.py --excel other.xlsx     # use a different Excel
    python apply_changes_from_excel.py --diff                 # show unified diffs

Workflow (two-machine setup):
    Machine A (development):
        python generate_excel.py          # creates Project_Files.xlsx
        # copy Project_Files.xlsx to Machine B

    Machine B (target — already has the repo cloned):
        python apply_changes_from_excel.py                # preview changes
        python apply_changes_from_excel.py --apply        # apply them
"""

import argparse
import base64
import difflib
import sys
from pathlib import Path

from openpyxl import load_workbook


# ANSI colours (works on modern terminals including Windows Terminal)
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def read_excel(excel_path: Path) -> dict[str, str]:
    """Read all files from the Excel workbook into a {rel_path: content} dict."""
    wb = load_workbook(str(excel_path), read_only=True, data_only=True)
    files: dict[str, str] = {}

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        first_row = True
        for row in ws.iter_rows(min_row=1, values_only=True):
            if first_row:
                first_row = False
                continue

            if len(row) < 3:
                continue

            _, file_path_str, plain_content, *rest = row
            encoded_content = rest[0] if rest else None

            if not file_path_str:
                continue

            # Prefer base64 (exact fidelity), fall back to plain text
            if encoded_content:
                try:
                    content = base64.b64decode(str(encoded_content)).decode("utf-8")
                except Exception:
                    content = plain_content if plain_content is not None else ""
            else:
                content = plain_content if plain_content is not None else ""

            rel_path = str(file_path_str).strip()
            files[rel_path] = str(content)

    wb.close()
    return files


def read_disk_file(path: Path) -> str | None:
    """Read a file from disk, return None if it doesn't exist."""
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return None


def normalise(content: str) -> str:
    """Normalise line endings for comparison (CRLF → LF)."""
    return content.replace("\r\n", "\n").replace("\r", "\n")


def show_diff(rel_path: str, old: str, new: str) -> None:
    """Print a unified diff between old and new content."""
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    diff = difflib.unified_diff(old_lines, new_lines, fromfile=f"a/{rel_path}", tofile=f"b/{rel_path}", lineterm="")
    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            print(f"{GREEN}{line}{RESET}", end="")
        elif line.startswith("-") and not line.startswith("---"):
            print(f"{RED}{line}{RESET}", end="")
        elif line.startswith("@@"):
            print(f"{CYAN}{line}{RESET}", end="")
        else:
            print(line, end="")
        if not line.endswith("\n"):
            print()
    print()


def apply_changes(excel_path: Path, target_dir: Path, *, do_apply: bool, show_diffs: bool) -> None:
    """Compare Excel contents to disk and optionally write changes."""
    if not excel_path.exists():
        print(f"{RED}ERROR: Excel file not found: {excel_path}{RESET}")
        sys.exit(1)

    print(f"{BOLD}Excel  : {excel_path}{RESET}")
    print(f"{BOLD}Target : {target_dir}{RESET}")
    if not do_apply:
        print(f"{YELLOW}Mode   : DRY RUN (use --apply to write changes){RESET}")
    else:
        print(f"{GREEN}Mode   : APPLY{RESET}")
    print()

    # Read all files from Excel
    print("Reading Excel workbook...", end=" ", flush=True)
    excel_files = read_excel(excel_path)
    print(f"{len(excel_files)} files found\n")

    # Categorise changes
    new_files: list[str] = []
    modified_files: list[str] = []
    unchanged_files: list[str] = []
    deleted_on_disk: list[str] = []  # files in Excel that are empty (deleted)

    for rel_path, excel_content in sorted(excel_files.items()):
        disk_path = target_dir / Path(rel_path)
        disk_content = read_disk_file(disk_path)

        excel_normalised = normalise(excel_content)

        if disk_content is None:
            # File doesn't exist on disk yet
            if excel_normalised.strip():  # Skip empty/placeholder files
                new_files.append(rel_path)
        else:
            disk_normalised = normalise(disk_content)
            if excel_normalised == disk_normalised:
                unchanged_files.append(rel_path)
            else:
                modified_files.append(rel_path)

    # ── Report ──────────────────────────────────────────────────────────────

    print(f"{BOLD}Summary:{RESET}")
    print(f"  {GREEN}New files      : {len(new_files)}{RESET}")
    print(f"  {YELLOW}Modified files : {len(modified_files)}{RESET}")
    print(f"  {DIM}Unchanged      : {len(unchanged_files)}{RESET}")
    print()

    if new_files:
        print(f"{GREEN}{BOLD}── New files ──{RESET}")
        for f in new_files:
            print(f"  {GREEN}+ {f}{RESET}")
        print()

    if modified_files:
        print(f"{YELLOW}{BOLD}── Modified files ──{RESET}")
        for f in modified_files:
            print(f"  {YELLOW}~ {f}{RESET}")
        print()

    # Show diffs if requested
    if show_diffs and modified_files:
        print(f"{BOLD}── Diffs ──{RESET}\n")
        for rel_path in modified_files:
            disk_path = target_dir / Path(rel_path)
            disk_content = read_disk_file(disk_path) or ""
            excel_content = excel_files[rel_path]
            show_diff(rel_path, normalise(disk_content), normalise(excel_content))

    if not new_files and not modified_files:
        print(f"{GREEN}Everything is up to date — no changes needed.{RESET}")
        return

    # ── Apply ───────────────────────────────────────────────────────────────

    if not do_apply:
        total = len(new_files) + len(modified_files)
        print(f"{YELLOW}{total} file(s) would be written. Run with --apply to proceed.{RESET}")
        return

    written = 0
    errors = 0

    for rel_path in new_files + modified_files:
        disk_path = target_dir / Path(rel_path)
        excel_content = excel_files[rel_path]
        try:
            disk_path.parent.mkdir(parents=True, exist_ok=True)
            disk_path.write_text(excel_content, encoding="utf-8")
            action = "created" if rel_path in new_files else "updated"
            print(f"  {GREEN}✓{RESET} {action}: {rel_path}")
            written += 1
        except Exception as e:
            print(f"  {RED}✗ FAILED: {rel_path} — {e}{RESET}")
            errors += 1

    print(f"\n{BOLD}Done!{RESET}")
    print(f"  Written : {written}")
    if errors:
        print(f"  {RED}Errors  : {errors}{RESET}")
    print(f"\n{DIM}Tip: Run 'git diff' to review all changes before committing.{RESET}")


def main():
    parser = argparse.ArgumentParser(
        description="Apply incremental changes from Project_Files.xlsx to an existing project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  %(prog)s                         Preview changes (dry run)
  %(prog)s --apply                 Apply changes to current directory
  %(prog)s --apply --target /path  Apply to a specific project directory
  %(prog)s --diff                  Preview with unified diffs
  %(prog)s --diff --apply          Apply and show diffs
""",
    )
    parser.add_argument(
        "--excel",
        type=str,
        default="Project_Files.xlsx",
        help="Path to the Excel workbook (default: Project_Files.xlsx in current dir)",
    )
    parser.add_argument(
        "--target",
        type=str,
        default=".",
        help="Target project directory (default: current directory)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually write changes (without this flag, only previews)",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Show unified diffs for modified files",
    )
    args = parser.parse_args()

    excel_path = Path(args.excel).resolve()
    target_dir = Path(args.target).resolve()

    apply_changes(excel_path, target_dir, do_apply=args.apply, show_diffs=args.diff)


if __name__ == "__main__":
    main()
