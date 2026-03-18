import { useState, useRef } from "react";
import axios from "axios";
import "../styles/IngestionPanel.css";
import { useEffect } from "react";

export default function IngestionPanel() {
  const [files, setFiles] = useState([]);
  const [message, setMessage] = useState("");

  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [downloadedFiles, setDownloadedFiles] = useState([]);
  const [processingLog, setProcessingLog] = useState([]);



  const fileInputRef = useRef(null);


  const handleBrowseClick = () => {
    fileInputRef.current.click();
  };

const handleFileUpload = async (e) => {

  const selectedFiles = Array.from(e.target.files);

  if (!selectedFiles.length) {
    setMessage("No file selected");
    return;
  }

  const formData = new FormData();

  selectedFiles.forEach((file) => {
    formData.append("files", file);
  });

  try {

    const response = await axios.post(
      "http://localhost:8000/upload",
      formData
    );

    
    if (response.status === 200) {

      setMessage("File uploaded successfully!");

      const uploaded = selectedFiles.map((f) => ({
        name: f.name,
        size: `${(f.size / 1024).toFixed(0)} KB`,
        status: "indexed",
      }));

      setFiles((prev) => [...prev, ...uploaded]);

    } else {
      setMessage("File upload failed.");
    }

  } catch (error) {

    console.error("Upload failed:", error.response?.data || error.message);

    // setMessage(" File upload failed.");
  }

};

//return the uploades files 
useEffect(() => {
  const fetchFiles = async () => {
  try {

    const res = await axios.get("http://localhost:8000/files");

    const backendFiles = res.data.files.map((f) => ({
      name: f.name,
      size: "N/A",
      status: "indexed"
    }));

    setFiles(backendFiles);

  } catch (err) {
    console.error("Failed to load files", err);
  }
};
fetchFiles();
}, []);


  //added external search 
const handleSearch = async () => {
    if (!query.trim()) {
      setMessage("Please enter a search query");
      return;
    }
    setIsSearching(true);
    setMessage("");
    setDownloadedFiles([]);
    setProcessingLog([]); 
    try {
      const response = await axios.post("http://localhost:8001/ingest", { query });

      console.log("Full response:", response.data);           
      console.log("Log:", response.data.log);                 
      console.log("Files:", response.data.files);

      if (response.data.log) {
        setProcessingLog(response.data.log);  
      }

      if (response.data.files?.length > 0) {
        setDownloadedFiles(response.data.files);
        setMessage(`Downloaded ${response.data.files.length} files`);

        // refresh uploaded files list after download
        const res = await axios.get("http://localhost:8000/files");
        const backendFiles = res.data.files.map((f) => ({
          name: f.name,
          size: "N/A",
          status: "indexed"
        }));
        setFiles(backendFiles);

      } else {
        setMessage("⚠️ No documents found");
      }
    } catch (error) {
      setMessage("Search failed. Check your backend.");
    }
    setIsSearching(false);
  };

  //clear documents 
  const handleClear = async () => {
    try {
      const response = await axios.delete("http://localhost:8001/ingest/clear");
      setDownloadedFiles([]);
      setQuery("");
      setMessage(` ${response.data.message}`);
    } catch (error) {
      setMessage("Failed to clear files");
    }
  };


  const handleDeleteSelected = async () => {
    const selectedFiles = files.filter(f => f.selected);

  if (selectedFiles.length === 0) {
    setMessage("No files selected");
    return;
  }
  try {
    const response = await axios.delete("http://localhost:8000/files/delete", {
      data: { file_names: selectedFiles.map(f => f.name) }
    });

    setMessage(` ${response.data.message}`);
    const res = await axios.get("http://localhost:8000/files");
    const backendFiles = res.data.files.map((f) => ({
      name: f.name,
      size: "N/A",
      status: "indexed"
    }));
    setFiles(backendFiles);

  } catch (error) {
    setMessage("Failed to delete files");
  }
  }
  return (
    <div className="panel ingestion-panel">

      <div className="panel-title">
        <h1>Ingestion</h1>
      </div>

      {message && <p className="upload-message">{message}</p>}

      <div className="drop-zone" onClick={handleBrowseClick}>
        <div className="drop-zone-icon">📁</div>
        <p className="drop-zone-primary">Click to browse files</p>
        <p className="drop-zone-secondary">
          PDF, DOCX, TXT
        </p>
      </div>

      <input
        type="file"
        multiple
        ref={fileInputRef}
        style={{ display: "none" }}
        onChange={handleFileUpload}
      />

    {/* <div className="file-list">
      {files.map((f, i) => (
      <div key={i} className="file-item">
      <div>
        <p className="file-name">{f.name}</p>
        <p className="file-size">{f.size}</p>
        <p className="file-size">{f.uploaded_at}</p>
      </div>
      <span className="file-badge">{f.status}</span>
      
      </div>
      
    ))}
    <button className="clear-btn">delete button</button>
</div> */}


<div className="file-list">
  {files.map((f, i) => (
    <div key={i} className="file-item">
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <input
          type="checkbox"
          checked={f.selected || false}
          onChange={() => {
            setFiles(prev => prev.map((file, idx) =>
              idx === i ? { ...file, selected: !file.selected } : file
            ));
          }}
        />
        <div>
          <p className="file-name">{f.name}</p>
          <p className="file-size">{f.size}</p>
          <p className="file-size">{f.uploaded_at}</p>
        </div>
      </div>
      <span className="file-badge">✓ {f.status}</span>
    </div>
  ))}

  {files.length > 0 && (
    <button
      className="clear-btn"
      style={{ marginTop: "10px" }}
      onClick={handleDeleteSelected}
    >
       Delete Selected
    </button>
  )}
</div>

{/* added Search Section below upload */}
<div className="info-table" style={{ marginTop: "24px" }}>

  <div className="info-row">
    <span className="info-label">🔍 Search Similar Legal Cases</span>
  </div>

  <div className="info-row">
    <div className="search-row" style={{ width: "100%" }}>
      <input
        type="text"
        className="search-input"
        placeholder="search previous cases"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={(e) => { if (e.key === "Enter") handleSearch(); }}
      />
      <button className="search-btn" onClick={handleSearch} disabled={isSearching}>
        {isSearching ? "Searching..." : "Search"}
      </button>
      <button className="clear-btn" onClick={handleClear} disabled={isSearching}>
        Clear
      </button>
    </div>
  </div>

  {processingLog.length > 0 && (
  <>
    <div className="info-row">
      <span className="info-label">Processing Log</span>
      <span className="info-value">{processingLog.length} cases checked</span>
    </div>
    {processingLog.map((log, i) => (
      <div key={i} className="info-row">
        <span className="info-label">{log.case}</span>
        <span className="info-value">{log.status}</span>
      </div>
    ))}
  </>
)}

  {downloadedFiles.length > 0 && (
    <>
      <div className="info-row">
        <span className="info-label"> Downloaded Cases</span>
        <span className="info-value">{downloadedFiles.length} files</span>
      </div>
      {downloadedFiles.map((f, i) => (
        <div key={i} className="info-row">
          <span className="info-label">{f.name}</span>
          <span className="info-value">{f.type}</span>
        </div>
      ))}
    </>
  )}

</div>
    </div>
  );
}





