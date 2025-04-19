import React, { useState } from "react";
import ReactJson from "react-json-view";
import { FiCopy, FiDownload, FiSearch, FiUpload, FiFileText } from "react-icons/fi";
import { TbSailboat } from "react-icons/tb";
import sailLogo from "./SAIL.png";
import "./App.css";
import loadingGif from "./sail.gif";


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
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div className="logo-section">
          <img src={sailLogo} alt="SAIL Logo" className="logo" />
          <h1 className="title">sail</h1>
        </div>
        <p className="subtitle">Financial Data Extraction Tool</p>
      </div>

      <div className="dashboard-content">
        <div className="input-panel">
          <div className="panel-header">
            <h2>Extract Earnings Data</h2>
          </div>

          <div className="mode-toggle">
            <button
              className={`mode-button ${mode === "search" ? "active" : ""}`}
              onClick={() => setMode("search")}
            >
              <FiSearch /> Search by Keywords
            </button>
            <button
              className={`mode-button ${mode === "upload" ? "active" : ""}`}
              onClick={() => setMode("upload")}
            >
              <FiUpload /> Upload Report
            </button>
          </div>

          <div className="input-section">
            {mode === "search" ? (
              <>
                <label>Enter search query:</label>
                <div className="search-input-wrapper">
                  <FiSearch className="search-icon" />
                  <input
                    type="text"
                    value={name}
                    placeholder="e.g., Apple Q1 2023 earnings report"
                    onChange={(e) => setName(e.target.value)}
                  />
                </div>
              </>
            ) : (
              <>
                <label htmlFor="pdf-upload">Upload earnings report (PDF):</label>
                <div className="file-upload-area">
                  <input
                    id="pdf-upload"
                    type="file"
                    accept=".pdf"
                    onChange={(e) => setFile(e.target.files[0])}
                  />
                  {file && (
                    <div className="file-info">
                      <FiFileText />
                      <span>{file.name}</span>
                    </div>
                  )}
                </div>
              </>
            )}

            <button
              className="submit-button"
              onClick={handleSubmit}
              disabled={
                (mode === "search" && !name) || (mode === "upload" && !file) || loading
              }
            >
              {loading ? "Processing..." : "Extract Data"}
            </button>
          </div>

          <div className="usage-guide">
            <h3>Quick Guide</h3>
            <div className="guide-item">
              <div className="guide-number">1</div>
              <div className="guide-text">
                Select your preferred data source method above
              </div>
            </div>
            <div className="guide-item">
              <div className="guide-number">2</div>
              <div className="guide-text">
                {mode === "search"
                  ? "Enter a specific query (company name, quarter, year)"
                  : "Upload an earnings report PDF file"}
              </div>
            </div>
            <div className="guide-item">
              <div className="guide-number">3</div>
              <div className="guide-text">
                Click "Extract Data" to process and analyze
              </div>
            </div>
          </div>
        </div>

        <div className="results-panel">
          <div className="panel-header">
            <h2>Financial Data Output</h2>
            {data && (
              <div className="action-buttons">
                <button title="Copy JSON" onClick={handleCopy} className="icon-button">
                  <FiCopy />
                </button>
                <button title="Download JSON" onClick={handleDownload} className="icon-button">
                  <FiDownload />
                </button>
              </div>
            )}
          </div>

          <div className="results-content">
            {loading ? (
              <div className="loading-indicator">
                <img src={loadingGif} alt="Loading..." className="loading-gif" />
                <p>Extracing Data</p>
              </div>
            ) : data ? (
              <div className="json-viewer">
                <ReactJson 
                  src={data} 
                  theme="monokai" 
                  collapsed={1} 
                  enableClipboard={false}
                  displayDataTypes={false}
                  displayObjectSize={false}
                />
              </div>
            ) : (
              <div className="empty-state">
                <FiFileText className="empty-icon" />
                <p>No financial data to display yet</p>
                <span>Data will appear here after extraction</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;