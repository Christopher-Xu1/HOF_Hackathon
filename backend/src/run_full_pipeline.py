#!/usr/bin/env python3
import sys, os, json
from pathlib import Path

from langchain_pipeline import extract_narrative_text, process_earnings_pdf
def main(pdf_path: str):
    if not os.path.isfile(pdf_path):
        print(f"Error: file not found: {pdf_path}")
        sys.exit(1)

    print(f"→ Extracting narrative text from: {pdf_path}")
    narrative = extract_narrative_text(pdf_path, debug=True)
    print(f"\n--- Narrative ({len(narrative)} chars) ---\n")
    print(narrative[:500] + ("\n…" if len(narrative) > 500 else ""))

    print("\n→ Running LLM summary on narrative…")
    summary = process_earnings_pdf(narrative)
    print("\n--- LLM JSON Output ---\n")
    print(json.dumps(summary, indent=2))
    
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {Path(__file__).name} <path_to_pdf>")
        sys.exit(1)
    main(sys.argv[1])
