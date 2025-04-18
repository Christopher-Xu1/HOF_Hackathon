import tabula
import pandas as pd
import os

def extract_with_tabula(pdf_path: str):
    tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True, stream=True)
    tables = [fix_table_formatting(t) for t in tables]
    filename = os.path.splitext(os.path.basename(pdf_path))[0]
    folder = os.path.join("backend", "data", "processed", filename)
    os.makedirs(folder)
    for (i, table) in enumerate(tables):
        table.to_csv(os.path.join(folder, f"Table_{i}.csv"))

def fix_table_formatting(table: pd.DataFrame):
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
