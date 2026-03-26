# Bioventures Visitor Check-In (PBD Laboratories)

Small Flask app to check visitors in/out and show a printable badge.

## Run locally (SQLite)
```bash
pip install -r requirements.txt
python app.py
```
Then open: `http://127.0.0.1:5000/`

## Deploy with free-tier PostgreSQL (recommended)

This app supports Postgres using the environment variable `DATABASE_URL`.

1. Create a Postgres database on a free tier provider (examples):
   - Neon
   - Supabase
   - Render PostgreSQL
2. Copy your connection string (make sure it includes SSL requirements if your provider needs it).
3. Deploy the Flask app to a host that runs Python (examples):
   - Render (Web Service)
   - Railway
   - Fly.io
4. Set environment variable on the host:
   - `DATABASE_URL` = your Postgres connection string
5. Start command (for Render/Railway-style deploys):
   - `gunicorn app:app`

### Expected schema
The app automatically creates a `visits` table and indexes on first startup.

