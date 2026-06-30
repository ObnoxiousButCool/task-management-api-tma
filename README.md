# Task Management API

Task Management API is a Flask service with signed bearer-token authentication, bcrypt password hashing, SQLAlchemy models, and PostgreSQL-ready configuration.

## Setup

1. Create and activate the virtual environment:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

2. Install dependencies:
   ```powershell
   .venv\Scripts\pip install Flask Flask-SQLAlchemy SQLAlchemy bcrypt psycopg2-binary pytest
   ```

3. Create a PostgreSQL 14.5 database and copy `.env.example` values into your environment.

4. Initialize the database tables explicitly:
   ```powershell
   $env:FLASK_APP = "app:create_app"
   flask init-db
   ```

5. Seed the default user:
   ```powershell
   $env:TMA_SEED_ADMIN_PASSWORD = "<local-admin-password>"
   python seed.py
   ```

6. Start the API:
   ```powershell
   python app.py
   ```

The service listens on `http://localhost:5000` when run with `python app.py`.

## API

- `POST /api/auth/register` with `email` and `password`
- `POST /api/auth/login` with `email` and `password`
- `POST /api/tasks` with Bearer token
- `GET /api/tasks` with optional `status`, `priority`, `due_from`, and `due_to`
- `GET /api/tasks/<id>`
- `PUT /api/tasks/<id>`
- `DELETE /api/tasks/<id>`
- `GET /api/tasks/analytics/completion`

## CI Check

Run the iteration sanity check:

```powershell
python ci_check.py
```
