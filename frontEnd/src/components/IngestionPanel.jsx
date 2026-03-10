import { useState, useRef } from "react";
import axios from "axios";
import { INITIAL_FILES } from "./constants";
import "../styles/IngestionPanel.css";
import { useEffect } from "react";

export default function IngestionPanel() {
  const [files, setFiles] = useState([]);
  const [message, setMessage] = useState("");
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
}, []);
  return (
    <div className="panel ingestion-panel">

      <div className="panel-title">
        <span className="panel-title-icon">📤</span>
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

      <div className="file-list">
      {files.map((f, i) => (
      <div key={i} className="file-item">
      <div>
        <p className="file-name">{f.name}</p>
        <p className="file-size">{f.size}</p>
        <p className="file-size">{f.uploaded_at}</p>
      </div>
      <span className="file-badge">✓ {f.status}</span>
      </div>
    ))}
</div>

    </div>
  );
}