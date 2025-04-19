import React, { useState } from "react";

function App() {
  const [file, setFile] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("http://localhost:5000/upload", {
      method: "POST",
      body: formData,
    });

    const json = await res.json();
    setData(json);
    setLoading(false);
  };

  return (
    <div>
      <h1>Earnings Extractor</h1>

      <div className="upload-wrapper">
        <p>Upload your earnings statement:</p>
        <label htmlFor="file-upload" className="custom-file-upload">
          📁 Choose File
        </label>
        <input
          id="file-upload"
          type="file"
          onChange={(e) => setFile(e.target.files[0])}
        />
        {file && <p className="filename">Selected: {file.name}</p>}
        <button onClick={handleUpload} disabled={!file}>
          Upload
        </button>
      </div>

      {loading && <p>Processing...</p>}
      {data && (
        <div>
          <h2>Extracted Data:</h2>
          <pre>{JSON.stringify(data, null, 2)}</pre>
        </div>
      )}

      <div>
        <h2>How to Use:</h2>
        <ol>
          <li>
            Click on the "Choose File" button to select your earnings statement.
          </li>
          <li>Click on the "Upload" button to upload the file.</li>
          <li>Wait for the processing to complete.</li>
          <li>Your extracted data will be displayed below.</li>
        </ol>
      </div>
    </div>
  );
}

export default App;
