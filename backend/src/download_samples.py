from pathlib import Path
import requests

# Hard‑coded URLs
urls = [
    "https://s2.q4cdn.com/299287126/files/doc_financials/2024/q4/AMZN-Q4-2024-Earnings-Release.pdf",
    "https://abc.xyz/assets/91/b3/3f9213d14ce3ae27e1038e01a0e0/2024q1-alphabet-earnings-release-pdf.pdf"
]

# Destination folder  →  project_root/backend/data/raw
project_root = Path(__file__).resolve().parents[1]        # adjust if layout differs
download_dir = project_root / "data" / "raw"
download_dir.mkdir(parents=True, exist_ok=True)

for url in urls:
    filename = Path(url).name
    dest_path = download_dir / filename

    print(f"Downloading {url} → {dest_path}")
    try:
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"✅  Saved {filename}")
    except Exception as e:
        print(f"❌  Failed to fetch {url} – {e}")
