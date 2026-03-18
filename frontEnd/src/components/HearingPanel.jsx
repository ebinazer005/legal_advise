import { useState, useEffect } from "react";
import axios from "axios";
import "../styles/HearingPanel.css";

export default function HearingPanel() {
    const [hearings, setHearings] = useState([]);
    const [message, setMessage] = useState("");
    const [form, setForm] = useState({
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
        }
    };

    useEffect(() => {
        fetchHearings();
    }, []);

    const handleAdd = async () => {
        if (!form.case_name || !form.next_hearing_date) {
            setMessage("⚠️ Case Name and Next Hearing Date are required");
            return;
        }
        try {
            await axios.post("http://localhost:8000/hearings", form);
            setMessage("✅ Client details added successfully");
            setForm({
                case_name: "",
                next_hearing_date: "",
                last_hearing_date: "",
                notes: "",
                fee_paid: "",
                case_status: "Current"
            });
            fetchHearings();
        } catch (err) {
            setMessage("❌ Failed to add client details");
        }
    };

    const handleDelete = async (id) => {
        try {
            await axios.delete(`http://localhost:8000/hearings/${id}`);
            setMessage("🗑️ Record deleted");
            fetchHearings();
        } catch (err) {
            setMessage("❌ Failed to delete");
        }
    };

    return (
        <div className="panel">
            <div className="panel-title">
                <span>👤</span>
                <h1>Client Details</h1>
            </div>

            {message && <p className="upload-message">{message}</p>}

            {/* Add Client Details Form */}
            <div className="info-table">
                <div className="info-row">
                    <span className="info-label">📋 Add Client Details</span>
                </div>

                <div className="info-row">
                    <span className="info-label">Case Name *</span>
                    <input
                        className="search-input"
                        placeholder="Enter the cilent Name "
                        value={form.case_name}
                        onChange={e => setForm({ ...form, case_name: e.target.value })}
                    />
                </div>

                <div className="info-row">
                    <span className="info-label">⏮️ Last Hearing Date</span>
                    <input
                        className="search-input"
                        type="date"
                        value={form.last_hearing_date}
                        onChange={e => setForm({ ...form, last_hearing_date: e.target.value })}
                    />
                </div>

                <div className="info-row">
                    <span className="info-label">⏭️ Next Hearing Date *</span>
                    <input
                        className="search-input"
                        type="date"
                        value={form.next_hearing_date}
                        onChange={e => setForm({ ...form, next_hearing_date: e.target.value })}
                    />
                </div>

                <div className="info-row">
                    <span className="info-label">💰 Fee Paid (RM)</span>
                    <input
                        className="search-input"
                        type="number"
                        placeholder="amount paid"
                        value={form.fee_paid}
                        onChange={e => setForm({ ...form, fee_paid: e.target.value })}
                    />
                </div>

                <div className="info-row">
                    <span className="info-label">📋 Case Status</span>
                    <select
                        className="search-input"
                        value={form.case_status}
                        onChange={e => setForm({ ...form, case_status: e.target.value })}
                    >
                        <option value="Current">🟢 Current</option>
                        <option value="Case Finished">✅ Case Finished</option>
                    </select>
                </div>

                <div className="info-row">
                    <span className="info-label">📝 Notes</span>
                    <input
                        className="search-input"
                        placeholder="notes..."
                        value={form.notes}
                        onChange={e => setForm({ ...form, notes: e.target.value })}
                    />
                </div>

                <div className="info-row">
                    <button className="search-btn" onClick={handleAdd}>➕ Add</button>
                </div>
            </div>

            {/* All Records */}
            {hearings.length > 0 && (
                <div className="info-table" style={{ marginTop: "16px" }}>
                    <div className="info-row">
                        <span className="info-label">📋 All Client Records</span>
                        <span className="info-value">{hearings.length} records</span>
                    </div>

                    {hearings.map((h) => (
                        <div key={h.id} className="info-row">
                            <div className="hearing-card-left">
                                <span className="info-label" style={{ color: "#e0eaff", fontSize: "0.95rem" }}>
                                    {h.case_name}
                                </span>
                                <span className="hearing-date-badge">⏮️ Last: {h.last_hearing_date}</span>
                                <span className="hearing-date-badge" style={{ borderColor: "#4ade80", color: "#4ade80" }}>
                                    ⏭️ Next: {h.next_hearing_date}
                                </span>
                                <p className="file-size">💰 Fee Paid: RM {h.fee_paid}</p>
                                <span className={`status-badge ${h.case_status === "Current" ? "status-current" : "status-finished"}`}>
                                    {h.case_status === "Current" ? "🟢 Current" : "✅ Case Finished"}
                                </span>
                                {h.notes && <p className="file-size">📝 {h.notes}</p>}
                            </div>
                            <button className="clear-btn" onClick={() => handleDelete(h.id)}>🗑️</button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}