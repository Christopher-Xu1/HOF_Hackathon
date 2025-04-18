from langchain_pipeline import extract_tables, extract_narrative_text, title_tables, process_earnings_pdf
def main(pdf_path):
    # 1) split into table pages vs narrative pages
    table_paths = extract_tables(pdf_path, out_dir="tables/")
    narrative = extract_narrative_text(pdf_path)

    # 2) auto‐title each table
    print("→ Generating titles for tables…")
    titled = title_tables("tables/")
    for path, heading in titled:
        print(f"  • {path.name} → {heading}")

    # 3) summarize narrative via LLM
    summary = process_narrative_text(narrative)
    print("→ Narrative summary JSON:")
    print(json.dumps(summary, indent=2))
