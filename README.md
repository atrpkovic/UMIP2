# UMIP 2.0 - Universal Marketing Intelligence Platform

AI-powered SQL assistant for Priority Tire's marketing data warehouse.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. Run the app:
```bash
python -m app.main
```

## Architecture

- **app/agent/** - Claude API integration and text-to-SQL logic
- **app/database/** - Snowflake connection and schema definitions
- **app/routes/** - Flask API endpoints
- **config/** - Environment configuration

## Usage

Send questions to the `/api/chat` endpoint:

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What were our top 10 selling tire brands last month?"}'
```

## Adding New Tables

1. Add table definition to `app/database/schema.py`
2. The agent will automatically include it in query generation
