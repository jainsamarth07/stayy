"""
Read Offer_Changes.xlsx and update ONLY the 14 offer-in-messaging files
in a target project directory.

This overwrites existing files at their correct relative paths.
It will NOT touch any other files in the target directory.

Usage:
    python apply_offer_changes.py                                # updates files in current dir
    python apply_offer_changes.py --target C:\\other\\project      # updates in specified dir
    python apply_offer_changes.py --excel path/to/Offer_Changes.xlsx  # custom Excel path
"""

import argparse
import base64
import sys
from pathlib import Path

from openpyxl import load_workbook


def apply_changes(excel_path: Path, target_dir: Path) -> None:
    """Read the Excel workbook and overwrite the 14 files in target_dir."""
    if not excel_path.exists():
        print(f"ERROR: Excel file not found: {excel_path}")
        sys.exit(1)

    print(f"Reading : {excel_path}")
    print(f"Target  : {target_dir}\n")

    wb = load_workbook(str(excel_path), read_only=True, data_only=True)

    total_updated = 0
    total_created = 0
    total_skipped = 0

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        sheet_updated = 0
        sheet_created = 0
        sheet_skipped = 0

        print(f"--- Sheet: {sheet_name} ---")

        first_row = True
        for row in ws.iter_rows(min_row=1, values_only=True):
            # Skip header row
            if first_row:
                first_row = False
                continue

            # Columns: #, File Path, File Content, Encoded Content
            if len(row) < 3:
                continue

            _, file_path_str, plain_content, *rest = row
            encoded_content = rest[0] if rest else None

            if not file_path_str:
                continue

            rel_path = Path(str(file_path_str).strip())
            full_path = target_dir / rel_path

            # Prefer base64 column (exact fidelity), fall back to plain text
            if encoded_content:
                try:
                    content = base64.b64decode(str(encoded_content)).decode("utf-8")
                except Exception:
                    content = plain_content if plain_content is not None else ""
            else:
                content = plain_content if plain_content is not None else ""

            try:
                existed = full_path.exists()

                # Create parent directories if needed
                full_path.parent.mkdir(parents=True, exist_ok=True)

                # Write file
                full_path.write_text(str(content), encoding="utf-8")

                if existed:
                    print(f"  UPDATED  {rel_path}")
                    sheet_updated += 1
                else:
                    print(f"  CREATED  {rel_path}")
                    sheet_created += 1
            except Exception as exc:
                print(f"  SKIP     {rel_path}  ({exc})")
                sheet_skipped += 1

        print(f"  Updated: {sheet_updated}  |  Created: {sheet_created}  |  Skipped: {sheet_skipped}")
        total_updated += sheet_updated
        total_created += sheet_created
        total_skipped += sheet_skipped

    wb.close()

    print(f"\n{'=' * 50}")
    print(f"Done!  Files updated : {total_updated}")
    print(f"       Files created : {total_created}")
    if total_skipped:
        print(f"       Files skipped : {total_skipped}")
    print(f"       Target folder : {target_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply the 14 offer-in-messaging changes from Offer_Changes.xlsx"
    )
    parser.add_argument(
        "--excel",
        type=str,
        default="Offer_Changes.xlsx",
        help="Path to the Excel workbook (default: Offer_Changes.xlsx in current dir)",
    )
    parser.add_argument(
        "--target",
        type=str,
        default=".",
        help="Target project directory to update files in (default: current directory)",
    )
    args = parser.parse_args()

    excel_path = Path(args.excel).resolve()
    target_dir = Path(args.target).resolve()

    apply_changes(excel_path, target_dir)


if __name__ == "__main__":
    main()
