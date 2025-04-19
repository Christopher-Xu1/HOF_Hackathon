from __future__ import annotations
import os, json
from typing import List, Tuple, Dict, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter, TokenTextSplitter
from langchain_core.runnables import RunnableParallel, RunnableLambda  # Corrected imports

from langchain.schema.output_parser import StrOutputParser
from langchain_core.output_parsers import JsonOutputParser # Import JsonOutputParser from the correct location

import pdfplumber, pathlib, re, statistics
import tabula
import pandas as pd

load_dotenv("backend/src/.env")   # path relative to this file
os.environ["JAVA_HOME"] = "/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home"# --------------------------------------------------------------------------
assert os.getenv("OPENAI_API_BASE"), "API base not set"
assert os.getenv("OPENROUTER_API_KEY"), "Key not set"



# 1. Load custom prompts from txt files
# --------------------------------------------------------------------------
def _load_prompt(file_path: str) -> PromptTemplate:
    with open(file_path) as f:
        prompt_text = f.read()
    return PromptTemplate(input_variables=["input"], template=prompt_text)

summary_prompt = _load_prompt("prompts/earnings_summarization.txt")
title_prompt = _load_prompt("prompts/chunk_title.txt")
overall_analysis_prompt = _load_prompt("prompts/overall_analysis.txt")

# --------------------------------------------------------------------------
# 2. Build the LLM chain (OpenRouter)
# --------------------------------------------------------------------------
def _build_llm():
    return ChatOpenAI(
        model="mistralai/Mixtral-8x7b-instruct",
        openai_api_base=os.getenv("OPENAI_API_BASE"),   # "https://openrouter.ai/api/v1"
        openai_api_key =os.getenv("OPENROUTER_API_KEY"),
        temperature=0,
    )

llm = _build_llm()

# --------------------------------------------------------------------------
# 3. Define individual processing chains
# --------------------------------------------------------------------------
process_chunk_chain = (
    {"chunk": lambda x: x}
    | summary_prompt
    | llm
    | JsonOutputParser()
)

title_chunk_chain = (
    {"chunk": lambda x: x}
    | title_prompt
    | llm
    | StrOutputParser()
)

# --------------------------------------------------------------------------
# 4. Orchestrator Bot Logic
# --------------------------------------------------------------------------
def orchestrate_analysis(results: Dict[str, Dict]):
    chunk_analyses = {
        chunk_id: {
            "title": title_chunk_chain.invoke({"chunk": result.get("sentimentReasoning", "") if result else "No Data"}),
            "analysis": result if result else None,
        }
        for chunk_id, result in results.items()
    }

    all_kpis = [item["analysis"].get("kpis", {}) for item in chunk_analyses.values() if item["analysis"]]
    all_sentiments = [item["analysis"].get("sentiment", "") for item in chunk_analyses.values() if item["analysis"]]

    overall_context = f"""
    Individual Chunk Analyses: {chunk_analyses}
    Extracted KPIs across all chunks: {all_kpis}
    Overall Sentiments: {all_sentiments}
    """

    overall_analysis = llm.invoke(overall_analysis_prompt.format(input=overall_context)).content

    return {"chunk_analyses": chunk_analyses, "overall_analysis": overall_analysis}

# --------------------------------------------------------------------------
# 5. Public entry-point: Process PDF with Orchestrator
# --------------------------------------------------------------------------
def process_earnings_pdf_with_orchestrator(pdf_path: str) -> Dict[str, Any]:
    table_csvs: List[dict] = extract_tables(pdf_path)
    narrative_text: str = extract_narrative_text(pdf_path)

    if not narrative_text.strip():
        return {"tables": table_csvs, "chunk_analyses": [], "overall_analysis": "No narrative text to analyze."}

    splitter = TokenTextSplitter(chunk_size=1500, chunk_overlap=150)
    chunks = splitter.split_text(narrative_text)

    parallel_processor = RunnableParallel(tasks={f"chunk_{i}": process_chunk_chain for i in range(len(chunks))})
    chunk_results = parallel_processor.invoke(chunks)

    final_analysis = orchestrate_analysis(chunk_results)
    final_analysis["tables"] = table_csvs
    return final_analysis

def run_pipeline_on_text_with_orchestrator(raw_text: str) -> Dict[str, Any]:
    splitter = TokenTextSplitter(chunk_size=1500, chunk_overlap=150)
    chunks = splitter.split_text(raw_text)

    parallel_processor = RunnableParallel(tasks={f"chunk_{i}": process_chunk_chain for i in range(len(chunks))})
    chunk_results = parallel_processor.invoke(chunks)

    final_analysis = orchestrate_analysis(chunk_results)
    return final_analysis



def extract_tables(pdf_path: str):
    tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True, stream=True)
    return [fix_table_formatting(t) for t in tables]

def fix_table_formatting(table: pd.DataFrame):
    # `apply` analyzes the table, vertically by default
    # the lambda we define returns a single bool for a column, which is basically if there is 
    df_clean: pd.DataFrame = table.loc[:, ~table.apply(lambda col: (col.isna() | col.eq('$')).all())]
    
    fixed_rows: list[tuple[str]] = []
    buffer: tuple[str] = None
    
    for row in df_clean.itertuples(index=False):
        clean_row = [str(cell) if pd.notna(cell) else "" for cell in row]
        is_continuation = buffer is not None and (not row[0] or str(row[0])[0].islower())
        is_incomplete = sum(bool(cell) for cell in clean_row) < len(clean_row)

        if is_continuation:
            buffer = tuple(
                (a if a else "") + "\n" + (b if b else "")
                for a, b in zip(buffer, clean_row)
            )
        else:
            if buffer:
                fixed_rows.append(buffer)
                buffer = None

            if is_incomplete:
                buffer = clean_row
            else:
                fixed_rows.append(clean_row)

    if buffer:
        fixed_rows.append(buffer)
        
    return pd.DataFrame(fixed_rows, columns=df_clean.columns).to_dict()

def title_tables(csv_folder: str) -> List[Tuple[Path, str]]:
    """
    Read every CSV in `csv_folder`, use the LLM to generate a title,
    and return a list of (path, title).
    """
    llm = ChatOpenAI(
        model="mistralai/Mixtral-8x7b-instruct",
        openai_api_base=os.getenv("OPENAI_API_BASE"),
        openai_api_key =os.getenv("OPENROUTER_API_KEY"),
        temperature=0,
    )

    chain = _build_chain()
    titles = []

    for csv_path in sorted(Path(csv_folder).glob("*.csv")):
        df = pd.read_csv(csv_path)
        # join columns
        cols = ", ".join(df.columns.tolist())
        # take 3 sample rows as CSV text
        sample = df.head(3).to_csv(index=False)
        # ask the LLM
        title = chain.run(columns=cols, sample_rows=sample).strip().strip('"')
        titles.append((csv_path, title))

    return titles


_NUM_RE   = re.compile(r"\d[\d,\.]*")
_ALPHA_RE = re.compile(r"[A-Za-z]")

def _numeric_density(text: str) -> float:
    if not text: return 0.0
    n_len = sum(len(m.group(0)) for m in _NUM_RE.finditer(text))
    a_len = len(_ALPHA_RE.findall(text)) + 1e-6
    return n_len / (n_len + a_len)

def _drop_repeating_lines(pages: List[str], top_n=3, bottom_n=3) -> List[str]:
    # same as before…
    from collections import Counter
    tops, bots = [], []
    for t in pages:
        lines = [ln.strip() for ln in t.splitlines() if ln.strip()]
        tops += lines[:top_n]
        bots += lines[-bottom_n:]
    thresh = int(len(pages)*0.7)
    top_common = {ln for ln,c in Counter(tops).items() if c>=thresh}
    bot_common = {ln for ln,c in Counter(bots).items() if c>=thresh}
    cleaned = []
    for t in pages:
        lines = [ln.strip() for ln in t.splitlines() if ln.strip()]
        lines = [ln for ln in lines if ln not in top_common and ln not in bot_common]
        cleaned.append("\n".join(lines))
    return cleaned

def extract_narrative_text(pdf_path: str, numeric_threshold: float = 0.33, min_chars: int = 100, debug: bool = False) -> str:
    narrative_pages: List[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for i,page in enumerate(pdf.pages):
            tables = page.find_tables()
            raw = page.extract_text() or ""
            if not raw.strip():
                continue

            if not tables:
                # no tables: same as before
                if _numeric_density(raw) > numeric_threshold or len(raw)<min_chars:
                    continue
                narrative_pages.append(raw)
            else:
                # page has tables: carve out text above & below
                # find top of top‑most table and bottom of bottom‑most table
                tops  = [tbl.bbox[1] for tbl in tables]  # bbox = (x0,y0,x1,y1)
                bots  = [tbl.bbox[3] for tbl in tables]
                y_top = min(tops)
                y_bot = max(bots)
                # extract "above" region
                above = page.within_bbox((0, 0, page.width, y_top)).extract_text() or ""
                # extract "below" region
                below = page.within_bbox((0, y_bot, page.width, page.height)).extract_text() or ""
                for chunk in (above, below):
                    chunk = chunk.strip()
                    if not chunk:
                        continue
                    if _numeric_density(chunk) > numeric_threshold or len(chunk)<min_chars:
                        continue
                    if debug:
                        print(f"[keep split] p{i+1}  len={len(chunk)} nd={_numeric_density(chunk):.2f}")
                    narrative_pages.append(chunk)

    # strip headers/footers
    cleaned = _drop_repeating_lines(narrative_pages)
    return "\n\n".join(cleaned).strip()
