import React, { useState } from "react";

function App() {
  const [name, setName] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!name) return;
    setLoading(true);

    const response = await fetch("http://localhost:5000/submit", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name: name,
        serpapi_api_key:
          "0dd9088229b70f2b5740ad8161755df192087552c216747df776310b6feb23fe", // Pass the API key here
      }),
    });

    const json = await response.json();
    setData(json);
    setLoading(false);
  };

  return (
    <div>
      <h1>Earnings Extractor</h1>

      <div className="input-wrapper">
        <p>Enter your name:</p>
        <input
          type="text"
          placeholder="Enter your name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        {name && <p className="name">Entered: {name}</p>}
        <button onClick={handleSubmit} disabled={!name}>
          Submit
        </button>
      </div>

      {loading && <p>Processing...</p>}
      {data && (
        <div>
          <h2>Response Data:</h2>
          <pre>{JSON.stringify(data, null, 2)}</pre>
        </div>
      )}

      <div>
        <h2>How to Use:</h2>
        <ol>
          <li>Enter your name in the text input field.</li>
          <li>Click on the "Submit" button to send the name.</li>
          <li>Wait for the processing to complete.</li>
          <li>The response data will be displayed below.</li>
        </ol>
      </div>
    </div>
  );
}

export default App;
