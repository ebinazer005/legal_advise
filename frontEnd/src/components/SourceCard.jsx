import "../styles/SourceCard.css";

export default function SourceCard({ source }) {
  
  return (
    <div className="source-card">
      <div className="source-card-header">
                <span className="source-badge">#{source.id}</span>
                <span className="source-file">{source.source}</span>
                
                {source.page !== "N/A" && (
                    <span className="source-page">Page {source.page}</span>
                )}
            </div>
      <p className="source-excerpt">{source.content}</p>
    </div>
  );
}
