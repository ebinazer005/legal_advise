import "../styles/SourceCard.css";

export default function SourceCard({ source }) {
  console.log(source)
  const data = source.content
  return (
    <div className="source-card">
      <div className="source-card-header">
                <span className="source-badge">#{source.id}</span>
                <span className="source-file">{data.content}</span>
                
                {source.page !== "N/A" && (
                    <span className="source-page">Page {source.page}</span>
                )}
            </div>
      <p className="source-excerpt">{source.excerpt}</p>
    </div>
  );
}
