import sys, os, json
from pathlib import Path
from langchain_pipeline import process_earnings_pdf_with_orchestrator, run_pipeline_on_text_with_orchestrator
import os

def save_pipeline_output(orchestrated_output, pdf_path):
    output_folder = "outputs"
    os.makedirs(output_folder, exist_ok=True)
    output_filename = os.path.basename(pdf_path).replace(".pdf", ".json")
    output_path = os.path.join(output_folder, output_filename)
    with open(output_path, "w") as f:
        json.dump(orchestrated_output, f, indent=2)
    print(f"✅ Output saved to: {output_path}")


def full_pipeline_with_orchestrator(pdf_path: str) -> None:
    print("\n=== FULL PIPELINE WITH ORCHESTRATOR (tables + narrative analysis with titles and overall summary) ===")
    orchestrated_output = process_earnings_pdf_with_orchestrator(pdf_path)
    print(f"• tables saved: {len(orchestrated_output.get('tables', []))}  →  {orchestrated_output.get('tables', [])[:3]} ...")
    print("• LLM Chunk Analyses with Titles:")
    print(json.dumps(orchestrated_output.get('chunk_analyses', {}), indent=2))
    print("\n• Overall LLM Analysis:")
    print(json.dumps(orchestrated_output.get('overall_analysis', 'No overall analysis available.'), indent=2))
    save_pipeline_output(orchestrated_output, pdf_path)


def main(pdf_path: str) -> None:
    if not os.path.isfile(pdf_path):
        sys.exit(f"❌ file not found: {pdf_path}")

    full_pipeline_with_orchestrator(pdf_path)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {Path(__file__).name} <path_to_pdf>")
        sys.exit(1)
    main(sys.argv[1])