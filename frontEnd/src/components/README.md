# DAGWorks RAG UI — Component Structure

## Folder Structure
```
src/
├── App.jsx                        # Root app — layout + routing
├── data/
│   └── constants.js               # Mock data, nav items, info rows
├── components/                    # Reusable UI components
│   ├── Logo.jsx
│   ├── Sidebar.jsx
│   ├── TopBar.jsx
│   ├── NumberStepper.jsx
│   ├── SliderControl.jsx
│   ├── StatusBadge.jsx
│   └── SourceCard.jsx
├── panels/                        # Full page panels (views)
│   ├── RetrievalPanel.jsx
│   ├── InformationPanel.jsx
│   └── IngestionPanel.jsx
└── styles/                        # One CSS file per component
    ├── global.css                 # Reset, fonts, animations, layout
    ├── Logo.css
    ├── Sidebar.css
    ├── TopBar.css
    ├── Controls.css               # Shared: NumberStepper + SliderControl
    ├── StatusBadge.css
    ├── SourceCard.css
    ├── RetrievalPanel.css
    ├── InformationPanel.css
    └── IngestionPanel.css
```

## Getting Started
```bash
npx create-react-app dagworks-rag
cd dagworks-rag
# Replace src/ with this folder
npm start
```

## Component Responsibilities

| Component         | Responsibility                                 |
|-------------------|------------------------------------------------|
| `App.jsx`         | Layout shell, active panel state               |
| `Sidebar`         | Navigation links, logo                         |
| `Logo`            | Brand mark + wordmark                          |
| `TopBar`          | Refresh / Expand / More action buttons         |
| `NumberStepper`   | Integer increment/decrement control            |
| `SliderControl`   | Range slider with fill track + thumb           |
| `StatusBadge`     | Running / Stopped indicator                    |
| `SourceCard`      | Retrieved document result card                 |
| `RetrievalPanel`  | Query input, params, search, results display   |
| `InformationPanel`| Pipeline metadata table                        |
| `IngestionPanel`  | File drag-and-drop + indexed file list         |
