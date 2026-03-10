export const NAV_ITEMS = ["Ingestion", "Retrieval"];

export const MOCK_RESPONSE = `Answer: The main challenges of deploying ML models in enterprise IT environments include:

1. **Model Drift & Validity** — Preserving the validity of predictive services over time as data distributions shift in production.

2. **Performance Diagnostics** — Continuous benchmarking of machine learning solutions in hybrid-cloud enterprise software deployments.

3. **Infrastructure Complexity** — Managing the intersection of DevOps pipelines, model versioning, and real-time inference at scale.

4. **Monitoring & Observability** — Detecting silent failures where models return predictions without errors but with degraded accuracy.

5. **Latency & Throughput** — Balancing response time SLAs with computational cost in high-traffic production systems.`;

export const MOCK_SOURCES = [
  { id: 1, title: "MLOps Production Guide",     score: 0.94, excerpt: "Preserving model validity over time requires continuous monitoring pipelines..." },
  { id: 2, title: "Enterprise AI Deployment",   score: 0.87, excerpt: "Hybrid-cloud architectures introduce complexity in model serving layers..." },
  { id: 3, title: "ML Infrastructure Patterns", score: 0.81, excerpt: "Performance diagnostics must account for both latency and accuracy drift..." },
];

export const INFO_ROWS = [
  { label: "Pipeline",          value: "ingestion and retrieval"   },
  { label: "Embedding Model",   value: "hugging face " },
  { label: "Vector Store",      value: "Chroma"    },
  { label: "LLM",               value: "LLaMA 3.1 8B"        },
  { label: "Documents Indexed", value: ""                  },
  { label: "Last Updated",      value: ""   },
];

export const INITIAL_FILES = [
  { name: "enterprise_ml_guide.pdf",  size: "2.4 MB", status: "indexed" },
  { name: "deployment_patterns.docx", size: "840 KB", status: "indexed" },
];
