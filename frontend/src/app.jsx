import React, { useState } from "react";
import ReactJson from "react-json-view";
import { FiCopy, FiDownload } from "react-icons/fi";
import "./App.css";

function App() {
  const [mode, setMode] = useState("search"); // 'search' or 'upload'
  const [name, setName] = useState("");
  const [file, setFile] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    setData(null);

    try {
      let response;

      if (mode === "search") {
        response = await fetch("http://localhost:5000/submit", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name,
            serpapi_api_key:
              "0dd9088229b70f2b5740ad8161755df192087552c216747df776310b6feb23fe",
          }),
        });
      } else {
        const formData = new FormData();
        formData.append("file", file);

        response = await fetch("http://localhost:5000/submit", {
          method: "POST",
          body: formData,
        });
      }

      const json = await response.json();
      setData(json);
    } catch (err) {
      console.error("Error:", err);
      setData({ error: "Failed to fetch data." });
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
  };

  const handleDownload = () => {
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "data.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="app-container">
      <h1 className="title">Earnings Extractor</h1>
      <div className="cards-container">
        {/* Input Card */}
        <div className="card input-card">
          <h2>Input</h2>

          {/* Mode Selector */}
          <div className="mode-toggle">
            <label>
              <input
                type="radio"
                value="search"
                checked={mode === "search"}
                onChange={() => setMode("search")}
              />
              Search by Name
            </label>
            <label>
              <input
                type="radio"
                value="upload"
                checked={mode === "upload"}
                onChange={() => setMode("upload")}
              />
              Upload PDF
            </label>
          </div>

          {mode === "search" ? (
  <>
    <label>Enter a query:</label>
    <input
      type="text"
      value={name}
      placeholder="e.g., Apple Q1 2023 earnings"
      onChange={(e) => setName(e.target.value)}
    />
  </>
) : (
  <>
    <label htmlFor="pdf-upload">Upload a PDF file:</label>
    <input
      id="pdf-upload"
      type="file"
      accept=".pdf"
      style={{
        marginTop: "0.5rem",
        marginBottom: "1rem",
        padding: "0.4rem",
        border: "1px solid #ccc",
        borderRadius: "6px",
        background: "#fff",
        width: "100%",
      }}
      onChange={(e) => setFile(e.target.files[0])}
    />
    {file && <p><strong>Selected:</strong> {file.name}</p>}
  </>
)}


          <button
            onClick={handleSubmit}
            disabled={
              (mode === "search" && !name) || (mode === "upload" && !file)
            }
          >
            Submit
          </button>

          <div className="instructions">
            <h3>Instructions:</h3>
            <ol>
              <li>Select a mode above</li>
              <li>Search: type a company + quarter + "earnings"</li>
              <li>Upload: choose a PDF earnings report</li>
              <li>Click Submit to process</li>
            </ol>
          </div>
        </div>

        {/* Output Card */}
        <div className="card output-card">
          <div className="output-header">
            <h2>Output</h2>
            {data && (
              <div className="output-actions">
                <button title="Copy" onClick={handleCopy}>
                  <FiCopy />
                </button>
                <button title="Download" onClick={handleDownload}>
                  <FiDownload />
                </button>
              </div>
            )}
          </div>
          {loading && <p>Processing...</p>}
          {data ? (
            <ReactJson src={data} collapsed={1} enableClipboard={false} />
          ) : (
            <p className="no-data">No data to display yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
