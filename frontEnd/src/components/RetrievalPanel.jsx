import { useState } from "react";

import NumberStepper from "../components/NumberStepper";
import SliderControl from "../components/SliderControl";
import StatusBadge from "../components/StatusBadge";
import SourceCard from "../components/SourceCard";

import "../styles/RetrievalPanel.css";
import axios from "axios";

export default function RetrievalPanel() {
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(3);
  const [alpha, setAlpha] = useState(0.75);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [sources, setSources] = useState([]);
  const [relatedLinks, setRelatedLinks] = useState([]);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setIsLoading(true);
    setResult(null);
    setSources([]);
    setRelatedLinks([]);

    try {
      const response = await axios.post("http://localhost:8002/ask", {
        query: query,
        top_k: topK,
        alpha: alpha
      });
      const data = response.data;

      setResult({
        query: data.query,
        response: data.answer,
        top_k: data.top_k,
        alpha: data.alpha
      });

      const formattedSources = data.context.map((c, i) => ({
        id: c.id,
        content: c.content,
        source: c.source,
        page: c.page
      }));

      setSources(formattedSources);
      setRelatedLinks(data.related_links || []);
    }
    catch (error) {
      console.error("API Error:", error);
    }
    setIsLoading(false)
  };

  const handleReset = () => {
    setResult(null);
    setSources([]);
    setIsLoading(false);
  };


const renderAnswer = (text) => {
    if (!text) return null;

    text = text.replace(/- ([^|]+\| Court:[^|]+\| Date:[^|]+\| URL: https?:\/\/[^\s]+)/g, '\n- $1')
    const lines = text.split('\n');

    return lines.map((line, i) => {

        // ✅ section headers
        if (line.includes('SECTION') && (line.includes('━') || line.includes('---'))) {
            return <div key={i} className="section-divider">{line}</div>;
        }

        if (line.startsWith('━') || line.startsWith('---')) {
            return null;
        }

        // ✅ clickable URL lines in section 3
        if (line.includes('URL: https://')) {
            const parts = line.split('| ');
            const namePart = parts[0]?.replace('- ', '').trim();
            const courtPart = parts[1]?.replace('Court:', '').trim();
            const datePart = parts[2]?.replace('Date:', '').trim();
            const urlPart = parts[3]?.replace('URL: ', '').trim();
            return (
                <div key={i} className="case-link-row">
                    <span className="case-link-bullet">📄</span>
                    <div className="case-link-content">
                        <a href={urlPart} target="_blank" rel="noopener noreferrer" className="case-link">
                            {namePart}
                        </a>
                        <span className="case-link-meta">🏛️ {courtPart} · 📅 {datePart}</span>
                    </div>
                </div>
            );
        }

        // ✅ split fields like "👤 Case Name: X 📅 Last Hearing: Y" into separate lines
        const emojiFields = ['👤', '📅', '⏭️', '💰', '📋', '📝', '⚖️', '✅', '🗣️'];
        const hasMultipleEmojis = emojiFields.filter(e => line.includes(e)).length > 1;

        if (hasMultipleEmojis) {
            // ✅ split by emoji fields
            const splitLines = line.split(/(?=👤|📅|⏭️|💰|📋|📝|⚖️|✅|🗣️)/u).filter(Boolean);
            return (
                <div key={i}>
                    {splitLines.map((part, j) => (
                        <p key={j} className="answer-field">{part.trim()}</p>
                    ))}
                </div>
            );
        }

        // ✅ single emoji field
        if (emojiFields.some(e => line.startsWith(e))) {
            return <p key={i} className="answer-field">{line}</p>;
        }

        // ✅ bullet points
        if (line.startsWith('- ')) {
            return (
                <div key={i} className="answer-bullet">
                    <span className="bullet-dot">•</span>
                    <span>{line.replace('- ', '')}</span>
                </div>
            );
        }

        if (line.trim() === '') {
            return <div key={i} style={{ height: '8px' }} />;
        }

        return <p key={i} className="answer-line">{line}</p>;
    });
};

  return (
    <div className="panel retrieval-panel">


      {/* Header */}
      <div className="panel-title">
        <h1>Retrieval</h1>
      </div>

      {/* Query + Parameters Grid */}
      <div className="retrieval-grid">

        {/* Left: Query Input */}
        <div className="query-section">
          <label className="query-label">Retrieval Query</label>
          <textarea
            className="query-textarea"
            rows={4}
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter" && e.ctrlKey) handleSearch(); }}
            placeholder="Enter your retrieval query..."
          />
          <button
            className={`search-btn ${isLoading ? "loading" : ""}`}
            onClick={handleSearch}
            disabled={isLoading}
          >
            {isLoading && <span className="spinner" />}
            {isLoading ? "Searching..." : "Search"}
          </button>

          {/* <button
            className="clear-btn"
            onClick={handleClearDB}
            disabled={isLoading}
          >
            Clear DB
          </button> */}
        </div>

        {/* Right: Parameters */}
        <div className="params-card">
          <h3 className="params-title">Hybrid Search Parameters</h3>
          <NumberStepper
            label="top K"
            value={topK}
            onChange={setTopK}
            tooltip="Number of top results to retrieve"
          />
          <SliderControl
            label="cosine similarity "
            value={alpha}
            min={0} max={1} step={0.01}
            onChange={setAlpha}
            tooltip="Balance between dense (1.0) and sparse (0.0) retrieval"
          />
        </div>
      </div>

      {/* Status */}
      {(isLoading || result) && <StatusBadge running={true} />}

      {/* Results */}

      {result && (
        <div className="results-section">
          <div className="result-block">
            <h2>Parameters Used</h2>
            <div className="params-used">
              <span>🔢 Top K: <strong>{result.top_k}</strong></span>
              <span>⚖️ Alpha: <strong>{result.alpha}</strong></span>
            </div>
          </div>

          <div className="result-block">
            <h2>Query</h2>
            <p className="result-query-text">{result.query}</p>
          </div>

          <div className="result-block">
            <h2>Response</h2>
            <div className="response-card">
              {renderAnswer(result.response)}
            </div>
          </div>

          {sources.length > 0 && (
            <div className="result-block">
              <h2>Sources <span className="sources-count">({sources.length})</span></h2>
              {sources.map(s => <SourceCard key={s.id} source={s} />)}
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!result && !isLoading && (
        <div className="empty-state">
          <div className="empty-icon">🔍</div>
          <p>Enter a query and click Search to retrieve results</p>
          <p className="empty-hint">Tip: Press Ctrl+Enter to search quickly</p>
        </div>
      )}
    </div>
  );
}
