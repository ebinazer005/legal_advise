import { useState, useEffect } from "react";
import axios from "axios";
import "../styles/HearingPanel.css";

export default function HearingPanel() {
    const [hearings, setHearings] = useState([]);
    const [message, setMessage] = useState("");
    const [editingId, setEditingId] = useState(null); 
    const [form, setForm] = useState({
        case_id: "",
        case_name: "",
        next_hearing_date: "",
        last_hearing_date: "",
        notes: "",
        fee_paid: "",
        case_status: "Current"
    });

    const fetchHearings = async () => {
        try {
            const res = await axios.get("http://localhost:8000/hearings");
            setHearings(res.data.all_hearings);
        } catch (err) {
            console.error("Failed to fetch hearings", err);
            setMessage("Failed to fetch records");
        }
    };

    useEffect(() => {
        fetchHearings();
    }, []);

    // Reset form to empty state
    const resetForm = () => {
        setForm({
            case_id: "",
            case_name: "",
            next_hearing_date: "",
            last_hearing_date: "",
            notes: "",
            fee_paid: "",
            case_status: "Current"
        });
        setEditingId(null);
    };

    // Load hearing data into form for editing
    const handleEdit = (hearing) => {
        setForm({
            case_id: hearing.case_id,
            case_name: hearing.case_name,
            next_hearing_date: hearing.next_hearing_date,
            last_hearing_date: hearing.last_hearing_date,
            notes: hearing.notes,
            fee_paid: hearing.fee_paid.toString(),
            case_status: hearing.case_status
        });
        setEditingId(hearing.id);
        setMessage(""); // Clear previous messages
    };

    // Add or Update hearing
    const handleSubmit = async () => {
        if (!form.case_name || !form.next_hearing_date) {
            setMessage("❌ Case Name and Next Hearing Date are required");
            return;
        }

        try {
            if (editingId) {
                // UPDATE existing record
                const response = await axios.put(`http://localhost:8000/hearings/${editingId}`, form);
                setMessage(`${response.data.message}`);
            } else {
                // ADD new record
                const response = await axios.post("http://localhost:8000/hearings", form);
                setMessage(`${response.data.message}`);
            }

            resetForm();
            fetchHearings();
        } catch (err) {
            console.error("Error:", err);
            setMessage(` ${err.response?.data?.message || "Failed to save changes"}`);
        }
    };

    const handleDelete = async (id) => {
        if (window.confirm("Are you sure you want to delete this record?")) {
            try {
                const response = await axios.delete(`http://localhost:8000/hearings/${id}`);
                setMessage(` ${response.data.message}`);
                fetchHearings();
            } catch (err) {
                console.error("Error:", err);
                setMessage(" Failed to delete");
            }
        }
    };

    return (
        <div className="panel">
            <div className="panel-title">
                <span>👤</span>
                <h1>Client Details</h1>
            </div>

            {message && (
                <p className={`upload-message ${message.startsWith("❌") ? "error" : "success"}`}>
                    {message}
                </p>
            )}

            {/* Add/Update Client Details Form */}
            <div className="info-table">
                <div className="info-row">
                    <span className="info-label">
                        {editingId ? " Edit Client Details" : "Add Client Details"}
                    </span>
                </div>

                <div className="info-row">
                    <span className="info-label">Case ID *</span>
                    <input
                        className="search-input"
                        placeholder="enter the cases id"
                        value={form.case_id}
                        onChange={e => setForm({ ...form, case_id: e.target.value })}
                    />
                </div>

                <div className="info-row">
                    <span className="info-label">Case Name *</span>
                    <input
                        className="search-input"
                        placeholder="enter the client name"
                        value={form.case_name}
                        onChange={e => setForm({ ...form, case_name: e.target.value })}
                    />
                </div>

                <div className="info-row">
                    <span className="info-label">Last Hearing Date</span>
                    <input
                        className="search-input"
                        type="date"
                        value={form.last_hearing_date}
                        onChange={e => setForm({ ...form, last_hearing_date: e.target.value })}
                    />
                </div>

                <div className="info-row">
                    <span className="info-label">Next Hearing Date *</span>
                    <input
                        className="search-input"
                        type="date"
                        value={form.next_hearing_date}
                        onChange={e => setForm({ ...form, next_hearing_date: e.target.value })}
                    />
                </div>

                <div className="info-row">
                    <span className="info-label">Fee Paid (RM)</span>
                    <input
                        className="search-input"
                        type="number"
                        placeholder="amount paid"
                        value={form.fee_paid}
                        onChange={e => setForm({ ...form, fee_paid: e.target.value })}
                    />
                </div>

                <div className="info-row">
                    <span className="info-label">Case Status</span>
                    <select
                        className="search-input"
                        value={form.case_status}
                        onChange={e => setForm({ ...form, case_status: e.target.value })}
                    >
                        <option value="Current">Current</option>
                        <option value="Case Finished">Case Finished</option>
                    </select>
                </div>

                <div className="info-row">
                    <span className="info-label">Notes</span>
                    <input
                        className="search-input"
                        placeholder="leave notes"
                        value={form.notes}
                        onChange={e => setForm({ ...form, notes: e.target.value })}
                    />
                </div>

                <div className="info-row" style={{ gap: "8px" }}>
                    <button className="search-btn" onClick={handleSubmit}>
                        {editingId ? " Update" : " Add"}
                    </button>
                    {editingId && (
                        <button
                            className="clear-btn"
                            onClick={resetForm}
                            style={{ backgroundColor: "#ef4444" }}
                        >
                            ✕ Cancel
                        </button>
                    )}
                </div>
            </div>

            {/* All Records */}
            {hearings.length > 0 && (
                <div className="info-table" style={{ marginTop: "16px" }}>
                    <div className="info-row">
                        <span className="info-label">All Client Records</span>
                        <span className="info-value">{hearings.length} records</span>
                    </div>

                    {hearings.map((h) => (
                        <div key={h.id} className="info-row">
                            <div className="hearing-card-left">
                                <span className="info-label" style={{ color: "#e0eaff", fontSize: "0.95rem" }}>
                                    {h.case_name}
                                </span>
                                <span className="case-id-badge" style={{ fontSize: "0.85rem", color: "#94a3b8" }}>
                                    ID: {h.case_id}
                                </span>
                                <span className="hearing-date-badge">Last: {h.last_hearing_date}</span>
                                <span className="hearing-date-badge" style={{ borderColor: "#4ade80", color: "#4ade80" }}>
                                    Next: {h.next_hearing_date}
                                </span>
                                <p className="file-size">💰 Fee Paid: RM {h.fee_paid}</p>
                                <span className={`status-badge ${h.case_status === "Current" ? "status-current" : "status-finished"}`}>
                                    {h.case_status === "Current" ? "🔵 Current" : "Case Finished"}
                                </span>
                                {h.notes && <p className="file-size">📝 {h.notes}</p>}
                            </div>
                            <div className="button-group" style={{ display: "flex", gap: "8px" }}>
                                <button
                                    className="edit-btn"
                                    onClick={() => handleEdit(h)}
                                    style={{
                                        backgroundColor: "#3b82f6",
                                        color: "white",
                                        padding: "8px 12px",
                                        border: "none",
                                        borderRadius: "4px",
                                        cursor: "pointer",
                                        fontSize: "0.85rem",
                                        fontWeight: "600"
                                    }}
                                >
                                     Edit
                                </button>
                                <button
                                    className="clear-btn"
                                    onClick={() => handleDelete(h.id)}
                                    style={{
                                        backgroundColor: "#ef4444",
                                        color: "white",
                                        padding: "8px 12px",
                                        border: "none",
                                        borderRadius: "4px",
                                        cursor: "pointer",
                                        fontSize: "0.85rem",
                                        fontWeight: "600"
                                    }}
                                >
                                     Delete
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {hearings.length === 0 && !editingId && (
                <div style={{ textAlign: "center", padding: "40px", color: "#94a3b8" }}>
                    <p> No client records yet. Add one to get started!</p>
                </div>
            )}
        </div>
    );
}






