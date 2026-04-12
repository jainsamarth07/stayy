"""
Generate an Excel workbook with all project files organized into 3 sheets:
  1. Frontend  – all files under frontend/
  2. Backend   – all files under backend/
  3. Other     – root-level and docs/ files, CI configs, etc.

Each row: File Path (relative) | File Content
"""

import base64
import os
import re
import sys
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

# Regex to strip characters illegal in XML (openpyxl uses XML internally)
ILLEGAL_XML_CHARS = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f"
    r"\ud800-\udfff\ufdd0-\ufdef\ufffe\uffff]"
)

# Default to the directory containing this script (works on any machine)
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent
OUTPUT = ROOT / "Project_Files.xlsx"

# Directories / files to skip
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".next", ".venv", "venv", "dist", "build", ".mypy_cache", ".pytest_cache", ".ruff_cache"}
SKIP_FILES = {"generate_excel.py", "setup_from_excel.py", "Project_Files.xlsx", "package-lock.json", ".coverage", ".DS_Store"}
SKIP_PATTERNS = {".env"}  # skip .env files (contain secrets); .env.example is kept

# Binary extensions to skip
BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".woff", ".woff2",
    ".ttf", ".eot", ".otf", ".mp4", ".mp3", ".zip", ".tar", ".gz",
    ".exe", ".dll", ".so", ".pyc", ".pyo", ".class", ".jar", ".lock",
    ".db", ".sqlite", ".sqlite3", ".coverage",
}


def collect_files():
    """Walk the project tree and return categorised file lists."""
    frontend, backend, other = [], [], []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # Prune unwanted directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for fname in filenames:
            full = Path(dirpath) / fname
            rel = full.relative_to(ROOT).as_posix()

            if fname in SKIP_FILES:
                continue
            if full.suffix.lower() in BINARY_EXT:
                continue
            # Skip secret env files (keep .env.example templates)
            if fname in SKIP_PATTERNS and not fname.endswith(".example"):
                continue

            if rel.startswith("frontend/"):
                frontend.append((rel, full))
            elif rel.startswith("backend/"):
                backend.append((rel, full))
            else:
                other.append((rel, full))

    # Sort each list alphabetically by path
    frontend.sort(key=lambda x: x[0])
    backend.sort(key=lambda x: x[0])
    other.sort(key=lambda x: x[0])
    return frontend, backend, other


def read_content(filepath: Path) -> str:
    """Read file content, return placeholder for unreadable files."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
        # Strip characters that openpyxl/XML cannot represent
        return ILLEGAL_XML_CHARS.sub("", content)
    except Exception as e:
        return f"[Could not read file: {e}]"


def style_sheet(ws, file_list):
    """Populate and style a worksheet with file data."""
    # Header styling
    header_font = Font(name="Calibri", bold=True, size=12, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    # Write headers
    headers = ["#", "File Path", "File Content", "Encoded Content"]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border

    # Content styling
    path_font = Font(name="Calibri", bold=True, size=10, color="1F4E79")
    content_font = Font(name="Consolas", size=9)
    content_align = Alignment(vertical="top", wrap_text=True)
    path_align = Alignment(vertical="top", wrap_text=True)

    for idx, (rel_path, full_path) in enumerate(file_list, 1):
        row = idx + 1
        content = read_content(full_path)

        # Row number
        cell_num = ws.cell(row=row, column=1, value=idx)
        cell_num.font = Font(name="Calibri", size=10)
        cell_num.alignment = Alignment(horizontal="center", vertical="top")
        cell_num.border = thin_border

        # File path
        cell_path = ws.cell(row=row, column=2, value=rel_path)
        cell_path.font = path_font
        cell_path.alignment = path_align
        cell_path.border = thin_border

        # File Content (human-readable)
        cell_content = ws.cell(row=row, column=3, value=content)
        cell_content.font = content_font
        cell_content.alignment = content_align
        cell_content.border = thin_border

        # Encoded Content (base64 — preserves exact whitespace/indentation)
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
        cell_encoded = ws.cell(row=row, column=4, value=encoded)
        cell_encoded.font = Font(name="Consolas", size=8, color="999999")
        cell_encoded.alignment = Alignment(vertical="top")

    # Column widths
    ws.column_dimensions["A"].width = 6
    ws.column_dimensions["B"].width = 55
    ws.column_dimensions["C"].width = 120
    ws.column_dimensions["D"].hidden = True  # hide encoded column

    # Freeze top row
    ws.freeze_panes = "A2"


def main():
    frontend, backend, other = collect_files()

    wb = Workbook()

    # Create sheets
    ws_frontend = wb.active
    ws_frontend.title = "Frontend"
    ws_backend = wb.create_sheet("Backend")
    ws_other = wb.create_sheet("Other Files")

    style_sheet(ws_frontend, frontend)
    style_sheet(ws_backend, backend)
    style_sheet(ws_other, other)

    wb.save(str(OUTPUT))
    print(f"Excel file created: {OUTPUT}")
    print(f"  Frontend files : {len(frontend)}")
    print(f"  Backend files  : {len(backend)}")
    print(f"  Other files    : {len(other)}")
    print(f"  Total          : {len(frontend) + len(backend) + len(other)}")


if __name__ == "__main__":
    main()
