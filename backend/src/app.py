from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import subprocess
import json
from scraper.scraper import fetch_latest_earnings_pdf  # Import the scraper function

app = Flask(__name__)
CORS(app)

OUTPUT_FOLDER = 'outputs'
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/submit", methods=["POST"])
def submit_name():
    # Get the name from the request body
    data = request.get_json()
    company_name = data.get("name")
    serpapi_api_key = data.get("serpapi_api_key")  # API key can be passed in request

    if not company_name:
        return jsonify({"error": "No company name provided"}), 400

    if not serpapi_api_key:
        return jsonify({"error": "No SerpAPI API key provided"}), 400

    # Step 1: Call the scraper to fetch the latest earnings PDF
    print(f"\n🔍 Fetching latest earnings PDF for: {company_name}")
    pdf_path = fetch_latest_earnings_pdf(company_name, serpapi_api_key)
    
    if not pdf_path:
        return jsonify({"error": "Failed to retrieve or process the PDF."}), 500
    
    # Step 2: Run the pipeline script with the downloaded PDF file
    try:
        print(f"\n📄 Running pipeline with the PDF: {pdf_path}")
        subprocess.run(["python", "pipeline.py", pdf_path], check=True)

        # Assuming the pipeline creates a JSON file with the processed data
        output_filename = os.path.basename(pdf_path).replace(".pdf", ".json")
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        if os.path.exists(output_path):
            with open(output_path) as f:
                result_data = json.load(f)
            return jsonify(result_data)
        else:
            return jsonify({"error": "Pipeline failed to produce output."}), 500
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running pipeline: {e}")
        return jsonify({"error": "Error running pipeline."}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
