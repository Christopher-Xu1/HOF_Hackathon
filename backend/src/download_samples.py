import os
import requests

# Hardcoded list of URLs
urls = [
    "https://s2.q4cdn.com/299287126/files/doc_financials/2024/q4/AMZN-Q4-2024-Earnings-Release.pdf",
    "https://abc.xyz/assets/91/b3/3f9213d14ce3ae27e1038e01a0e0/2024q1-alphabet-earnings-release-pdf.pdf"
]

# Destination folder
download_dir = "/backend/data/raw"

# Create folder if it doesn't exist
os.makedirs(download_dir, exist_ok=True)

# Download each file
for url in urls:
    filename = os.path.basename(url)  # Extract file name from URL
    dest_path = os.path.join(download_dir, filename)

    print(f"Downloading {url} to {dest_path}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise if HTTP error
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✅ Downloaded {filename}")
    except Exception as e:
        print(f"❌ Failed to download {url}: {e}")
