# src/extract/llm_narrative_pipeline.py
from __future__ import annotations
import os, json
from typing import List, Tuple
from dotenv import load_dotenv
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema.output_parser import StrOutputParser
import pdfplumber, pathlib, re, statistics
import tabula
import pandas as pd

load_dotenv()

# --------------------------------------------------------------------------
# 1. Load custom prompt from a txt file
# --------------------------------------------------------------------------
def _load_prompt() -> PromptTemplate:
    with open("src/prompts/earnings_summarization.txt") as f:
        prompt_text = f.read()
    return PromptTemplate(input_variables=["chunk"], template=prompt_text)

# --------------------------------------------------------------------------
# 2. Build the LLM chain (OpenRouter)
# --------------------------------------------------------------------------
def _build_chain():
    prompt = _load_prompt()
    llm = ChatOpenAI(
        model="mistralai/Mixtral-8x7b-instruct",
        base_url=os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        temperature=0,
    )
    return prompt | llm | StrOutputParser()

# --------------------------------------------------------------------------
# 3. Public entry-point: Process PDF
# --------------------------------------------------------------------------
def process_earnings_pdf(pdf_path: str) -> Tuple[List[str], List[dict]]:
    """
    Returns:
        - table_csvs: List of CSV file paths from table pages (handled elsewhere)
        - llm_summary: List of parsed JSON dicts from narrative text
    """

    table_csvs: List[str] = extract_tables(pdf_path)        
    narrative_text: str = extract_narrative_text(pdf_path)  

    if not narrative_text.strip():
        return table_csvs, []

    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    chunks = splitter.split_text(narrative_text)

    chain = _build_chain()
    parsed_chunks: List[dict] = []

    for chunk in chunks:
        try:
            raw = chain.invoke({"chunk": chunk})
            parsed_chunks.append(json.loads(raw))
        except json.JSONDecodeError:
            print("Skipping malformed output")
            continue

    return table_csvs, parsed_chunks

# --------------------------------------------------------------------------
#Placeholders (replace w implementations later)
# --------------------------------------------------------------------------
def extract_tables(pdf_path: str) -> List[str]:
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
        
    return pd.DataFrame(fixed_rows, columns=df_clean.columns)

def title_tables(csv_folder: str) -> List[Tuple[Path, str]]:
    """
    Read every CSV in `csv_folder`, use the LLM to generate a title,
    and return a list of (path, title).
    """
    llm = _make_llm()
    chain = LLMChain(prompt=_PROMPT, llm=llm)
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

def extract_narrative_text(pdf_path: str, umeric_threshold: float = 0.33, min_chars: int = 100, debug: bool = False) -> str:
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

