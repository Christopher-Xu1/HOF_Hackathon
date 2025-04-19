
from flask import Flask, request, jsonify
from flask_cors import CORS
import os, subprocess, json

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'data/test_docs'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    subprocess.run(["python", "src/pipeline.py", filepath])

    output_path = os.path.join(OUTPUT_FOLDER, file.filename.replace(".pdf", ".json"))
    if os.path.exists(output_path):
        with open(output_path) as f:
            data = json.load(f)
        return jsonify(data)
    else:
        return jsonify({"error": "Processing failed"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
