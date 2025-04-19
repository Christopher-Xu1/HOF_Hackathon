#Scraper for fetching the latest earnings PDF from a company's investor relations page using SerpAPI and Selenium.
import os
import re
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from urllib.parse import urljoin, urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time

def find_pdf_links_with_selenium(base_url, max_depth=1):
    print(f"\n🌐 Launching headless browser to crawl: {base_url}")
    options = Options()
    options.headless = True
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    visited = set()
    pdf_links = []

    def crawl(url, depth):
        if depth > max_depth or url in visited:
            return
        visited.add(url)

        print(f"\n📥 Visiting (depth {depth}): {url}")
        try:
            driver.get(url)
            time.sleep(2)  # wait for JS to load
            links = driver.find_elements("tag name", "a")

            print(f"🔗 Found {len(links)} links.")
            for link in links:
                href = link.get_attribute("href")
                if href and href.lower().endswith(".pdf"):
                    print(f"📄 Found PDF: {href}")
                    pdf_links.append(href)

            for link in links:
                href = link.get_attribute("href")
                if href and urlparse(href).netloc == urlparse(base_url).netloc and href not in visited:
                    crawl(href, depth + 1)

        except Exception as e:
            print(f"❌ Error: {e}")

    crawl(base_url, 0)
    driver.quit()
    return pdf_links


# Step 1: Get the IR page from Google using SerpAPI
def get_investor_relations_page(company_name, serpapi_api_key):
    print(f"\n🔍 Searching Google for {company_name} investor relations page...")
    url = "https://serpapi.com/search"
    params = {
        "q": f"{company_name} investor relations",
        "api_key": serpapi_api_key,
        "engine": "google",
        "num": 10,
    }

    response = requests.get(url, params=params)
    data = response.json()

    for result in data.get("organic_results", []):
        link = result.get("link", "")
        if "investor" in link or "ir" in link:
            print(f"✅ Found IR page: {link}")
            return link

    print("❌ No IR page found in search results.")
    return None

# Step 2: Crawl IR page (and subpages) to find PDF links with DEBUGGING
def find_pdf_links_on_ir_site(base_url, max_depth=1):
    visited = set()
    pdf_links = []

    def crawl(url, depth):
        if depth > max_depth or url in visited:
            return
        visited.add(url)

        print(f"\n🌐 Visiting (depth {depth}): {url}")
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")

            links_found = soup.find_all("a", href=True)
            print(f"🔗 Found {len(links_found)} links on this page.")

            for a_tag in links_found:
                href = a_tag["href"]
                full_url = urljoin(url, href)
                if full_url.lower().endswith(".pdf"):
                    print(f"📄 Found PDF: {full_url}")
                    pdf_links.append(full_url)

            for a_tag in links_found:
                href = a_tag["href"]
                full_url = urljoin(url, href)
                parsed = urlparse(full_url)

                if parsed.netloc == urlparse(base_url).netloc and full_url not in visited:
                    print(f"↪️  Queueing to crawl next: {full_url}")
                    crawl(full_url, depth + 1)

        except Exception as e:
            print(f"❌ Error crawling {url}: {e}")

    crawl(base_url, 0)
    return pdf_links

# Step 3: Download the PDF file
def download_pdf(pdf_url, save_dir="downloads"):
    os.makedirs(save_dir, exist_ok=True)
    local_filename = os.path.join(save_dir, pdf_url.split("/")[-1])
    print(f"\n⬇️ Downloading PDF: {pdf_url}")
    with requests.get(pdf_url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print(f"✅ Saved to {local_filename}")
    return local_filename

# Step 4: Validate and preview PDF
def validate_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        first_page_text = reader.pages[0].extract_text()
        print("\n📄 PDF Content Preview (first ~500 chars):")
        print("-" * 60)
        print(first_page_text[:500])
        print("-" * 60)
        return True
    except Exception as e:
        print(f"❌ PDF read error: {e}")
        return False

# Step 5: Main function
def fetch_latest_earnings_pdf(company_name, serpapi_api_key):
    ir_url = get_investor_relations_page(company_name, serpapi_api_key)
    if not ir_url:
        return

    pdf_links = find_pdf_links_with_selenium(ir_url, max_depth=1)
    if not pdf_links:
        print("❌ No PDFs found.")
        return

    # Pick the first PDF that matches Q[1-4] or just the first
    for link in pdf_links:
        if re.search(r"Q[1-4]", link, re.IGNORECASE):
            selected_pdf = link
            break
    else:
        selected_pdf = pdf_links[0]

    pdf_path = download_pdf(selected_pdf)
    if validate_pdf(pdf_path):
        print("✅ Done.")
        return pdf_path
    else:
        print("❌ Failed to process the PDF.")
        return None

if __name__ == "__main__":
    company = input("Enter company name (e.g., Amazon): ").strip()
    api_key = input("Enter your SerpAPI API key: ").strip()
    fetch_latest_earnings_pdf(company, api_key)
