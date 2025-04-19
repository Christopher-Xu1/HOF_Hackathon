import sys, os, json
from pathlib import Path

from langchain_pipeline import process_earnings_pdf, run_pipeline_on_text

def full_pipeline(pdf_path: str) -> None:
    print("\n=== FULL PIPELINE (tables + narrative) ===")
    csv_paths, summary = process_earnings_pdf(pdf_path)   # <-- PASS PATH
    print(f"• tables saved: {len(csv_paths)}  →  {csv_paths[:3]} ...")
    print("• LLM summary:")
    print(json.dumps(summary, indent=2))



def main(pdf_path: str) -> None:
    if not os.path.isfile(pdf_path):
        sys.exit(f"❌ file not found: {pdf_path}")

    full_pipeline(pdf_path)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {Path(__file__).name} <path_to_pdf>")
        sys.exit(1)
    main(sys.argv[1])