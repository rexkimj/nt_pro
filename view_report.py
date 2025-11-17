#!/usr/bin/env python3
"""
Quick Report Viewer
===================

Simple script to open generated backtest reports in browser.
"""

import os
import sys
import webbrowser
from pathlib import Path


def list_reports():
    """List all available reports."""
    reports_dir = Path("reports")

    if not reports_dir.exists():
        print("❌ No reports directory found.")
        print("💡 Generate reports first by running:")
        print("   cd strategies/order_block && python demo_report.py all")
        return []

    html_reports = list(reports_dir.glob("*.html"))

    if not html_reports:
        print("❌ No HTML reports found in reports/ directory.")
        print("💡 Generate reports first by running:")
        print("   cd strategies/order_block && python demo_report.py all")
        return []

    return sorted(html_reports, key=lambda x: x.stat().st_mtime, reverse=True)


def open_report(report_path: Path):
    """Open report in default browser."""
    abs_path = report_path.resolve()

    print(f"\n📊 Opening report: {report_path.name}")
    print(f"📁 Location: {abs_path}")

    # Open in browser
    webbrowser.open(f"file://{abs_path}")

    print("✅ Report opened in your default browser!")


def main():
    """Main entry point."""

    print("\n" + "="*80)
    print("Order Block Strategy - Report Viewer")
    print("="*80 + "\n")

    # List available reports
    reports = list_reports()

    if not reports:
        return

    print(f"Found {len(reports)} report(s):\n")

    for i, report in enumerate(reports, 1):
        size = report.stat().st_size / 1024  # KB
        mtime = report.stat().st_mtime
        from datetime import datetime
        mod_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

        print(f"  {i}. {report.name:<40} ({size:.1f} KB, {mod_time})")

    print()

    # If specific report requested
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        # Check if it's a number (index)
        if arg.isdigit():
            idx = int(arg) - 1
            if 0 <= idx < len(reports):
                open_report(reports[idx])
                return
            else:
                print(f"❌ Invalid report number: {arg}")
                print(f"   Please choose 1-{len(reports)}")
                return

        # Check if it's a filename or pattern
        matching = [r for r in reports if arg.lower() in r.name.lower()]

        if matching:
            open_report(matching[0])
            return
        else:
            print(f"❌ No report matching '{arg}' found.")
            return

    # Interactive mode
    if len(reports) == 1:
        choice = input("Press Enter to open the report (or 'q' to quit): ").strip().lower()
        if choice != 'q':
            open_report(reports[0])
    else:
        choice = input(f"Enter report number (1-{len(reports)}) or 'q' to quit: ").strip()

        if choice.lower() == 'q':
            print("👋 Bye!")
            return

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(reports):
                open_report(reports[idx])
            else:
                print(f"❌ Invalid choice: {choice}")
        else:
            print(f"❌ Invalid input: {choice}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
