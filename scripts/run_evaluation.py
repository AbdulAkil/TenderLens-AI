import argparse
from pathlib import Path

from tenderlens.evaluation.runner import write_report

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", type=Path, default=root / "evaluation" / "datasets")
    parser.add_argument("--report-dir", type=Path, default=root / "evaluation" / "reports")
    args = parser.parse_args()
    report_path = write_report(args.dataset_dir, args.report_dir)
    print(f"Wrote retrieval evaluation report to {report_path}")
