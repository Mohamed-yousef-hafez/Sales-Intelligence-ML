"""Automatic refresh for Power BI.

Examples:
    python refresh_exports.py                                  one refresh (newest file in inbox/ -> exports/)
    python refresh_exports.py --watch 300                      keep running, refresh when a new file arrives
    python refresh_exports.py --combine                        use ALL files in inbox/ (for example one per month)
    python refresh_exports.py --input C:\\data\\sales.xlsx --output C:\\SalesIntelligence\\exports
"""
import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))

from src.pipeline import run_pipeline, watch


def main():
    parser = argparse.ArgumentParser(description="Clean sales data and write the Power BI files.")
    parser.add_argument("--input", default="inbox", help="a sales file, or a folder with sales files (default: inbox)")
    parser.add_argument("--output", default="exports", help="where the Power BI files are written (default: exports)")
    parser.add_argument("--watch", type=int, metavar="SECONDS", help="keep running and check the folder every SECONDS")
    parser.add_argument("--combine", action="store_true", help="combine all files of the folder instead of using the newest")
    parser.add_argument("--horizon", type=int, default=3, help="months to forecast (default: 3)")
    parser.add_argument("--lang", choices=["en", "ar"], default="en", help="language of the dashboard titles (default: en)")
    parser.add_argument("--skip-reliability", action="store_true", help="skip the (slower) reliability check of the model")
    args = parser.parse_args()

    options = dict(horizon=args.horizon, combine=args.combine, reliability=not args.skip_reliability, lang=args.lang)
    if not Path(args.input).suffix:          # a folder (not a single file): create it if it does not exist
        Path(args.input).mkdir(parents=True, exist_ok=True)

    if args.watch:
        print(f"Watching {args.input} every {args.watch}s. Press Ctrl+C to stop. | مراقبة المجلد، اضغط Ctrl+C للإيقاف")
        try:
            watch(args.input, args.output, interval=args.watch, **options)
        except KeyboardInterrupt:
            print("Stopped.")
        return 0

    result = run_pipeline(args.input, args.output, **options)
    print(f"{result['status']}: {result['message'] or 'done'}")
    if result["status"] == "OK":
        print(f"Wrote {len(result['files'])} files to {args.output}")
    return 1 if result["status"] == "FAILED" else 0


if __name__ == "__main__":
    sys.exit(main())
