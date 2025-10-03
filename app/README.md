# MIDAS Graph Explorer 🧬

A simple Streamlit app for exploring biomedical knowledge graphs.

## What This App Does

This application provides a user-friendly interface to query and explore a biomedical knowledge graph containing genes, diseases, and sequence variants. Instead of running queries in a Jupyter notebook, you can now interact with the Neptune database through natural language questions.

**Key Features:**
- 🔍 Natural language queries to the Neptune graph database
- 📊 Real-time insights about genes, diseases, and relationships
- 🎨 Clean, modern UI with easy-to-read results
- 📝 Query history to track your explorations

## Database Contents

The Neptune graph contains:
- **1,142 genes** - genetic entities and their properties
- **880 diseases** - medical conditions and disorders  
- **754 sequence variants** - genetic variations
- **22,632 relationships** - connections between entities

## How to Run

1. Install dependencies (from project root):
```bash
cd /home/ubuntu/MIDAS
uv sync
```

2. Make sure you have AWS credentials configured for the Neptune database

3. Run the app:
```bash
uv run streamlit run app/app.py
```

Or use the convenience script:
```bash
./app/run.sh
```

4. Open your browser to `http://localhost:8501`

## Sample Questions

- "What's in the database?"
- "Show me the most connected genes"
- "Find diseases related to cancer"
- "What's the median number of neighbors per node?"
- "Tell me about gene BRCA1"

## Color Scheme

The app uses a light, modern color palette:
- Golden Yellow (#E5B867) - highlights
- Teal/Cyan (#7DD8D5) - primary accents
- Mint Green (#67E5AD) - secondary accents  
- Dark Blue (#0E1B31) - text
- Light Slate (#A8B2D1) - subtitles

