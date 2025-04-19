from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import subprocess
import json
from scraper.scraper import fetch_latest_earnings_pdf  # Your existing scraper

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "data/test_docs"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/submit", methods=["POST"])
def handle_submit():
    if request.content_type.startswith("multipart/form-data"):
        # ======= Handle PDF File Upload =======
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded."}), 400

        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        print(f"\n📄 Uploaded file saved to: {filepath}")
    else:
        # ======= Handle Company Name Search =======
        data = request.get_json()
        company_name = data.get("name")
        serpapi_api_key = data.get("serpapi_api_key")

        if not company_name:
            return jsonify({"error": "No company name provided."}), 400
        if not serpapi_api_key:
            return jsonify({"error": "No SerpAPI API key provided."}), 400

        print(f"\n🔍 Searching earnings PDF for: {company_name}")
        filepath = fetch_latest_earnings_pdf(company_name, serpapi_api_key)
        if not filepath:
            return jsonify({"error": "Failed to retrieve or process the PDF."}), 500

    # ======= Run the Pipeline =======
    try:
        print(f"\n⚙️ Running pipeline on: {filepath}")
        script_path = os.path.join(os.path.dirname(__file__), "run_full_pipeline.py")
        print(f"\n🧪 Running command: python {script_path} {filepath}")
        try:
            subprocess.run(["python", script_path, filepath], check=True)
        except subprocess.CalledProcessError as e:  
            print(f"❌ Pipeline error: {e}")
            return jsonify({"error": "Pipeline execution failed."}), 500


        output_filename = os.path.basename(filepath).replace(".pdf", ".json")
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        if os.path.exists(output_path):
            with open(output_path) as f:
                result_data = json.load(f)
            return jsonify(result_data)
        else:
            return jsonify({"error": "Pipeline did not generate output."}), 500
    except subprocess.CalledProcessError as e:
        print(f"❌ Pipeline error: {e}")
        return jsonify({"error": "Pipeline execution failed."}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
