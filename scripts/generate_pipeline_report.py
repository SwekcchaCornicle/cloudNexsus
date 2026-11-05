import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REPORT_PATH = (
    ROOT / "dataset" / "reports" / "corpus_pipeline_report.json"
)


def main():
    print("\n========== CLOUDNEXUS PIPELINE REPORT ==========\n")

    if not REPORT_PATH.exists():
        print("ERROR: Pipeline report does not exist.")
        print("First run: python scripts/run_corpus_pipeline.py")
        return

    with REPORT_PATH.open("r", encoding="utf-8") as file:
        report = json.load(file)

    print("Status:", report.get("status", "UNKNOWN"))
    print("Started:", report.get("started_at", "N/A"))
    print("Finished:", report.get("finished_at", "N/A"))

    document = report.get("document", {})

    print("\nDOCUMENT DETAILS")
    print("----------------")
    print("ID:", document.get("id", "N/A"))
    print("Provider:", document.get("provider", "N/A"))
    print("Service:", document.get("service_name", "N/A"))
    print("URL:", document.get("url", "N/A"))

    print("\nPIPELINE STAGES")
    print("---------------")

    stages = report.get("stages", {})

    for stage, details in stages.items():
        print(f"\n{stage.upper()}")

        if stage == "neo4j_import":
            print("Exit code:", details.get("return_code"))
            print(details.get("stdout", ""))
            if details.get("stderr"):
                print("Errors:", details["stderr"])

        elif isinstance(details, dict):
            print(json.dumps(details, indent=2))

    if report.get("error"):
        print("\nPIPELINE ERROR")
        print(report["error"])

    print("\n===============================================\n")


if __name__ == "__main__":
    main()