from pathlib import Path

from tenderlens.evaluation.runner import write_report

if __name__ == "__main__":
    dataset_dir = Path("/workspace/evaluation/datasets")
    report_path = write_report(dataset_dir, Path("/workspace/evaluation/reports"))
    print(f"Wrote retrieval evaluation report to {report_path}")
