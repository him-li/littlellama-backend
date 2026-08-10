# Little Llama API

FastAPI backend for the Little Llama pet-adoption demo. It uses SQLAlchemy,
Alembic, PostgreSQL in production, SQLite for local development, JWT
authentication, and Cloudinary image uploads.

## Local development

Create a virtual environment and install the development dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

Copy `.env.example` to `.env`, then initialize the local SQLite database and
start the API:

```bash
alembic upgrade head
uvicorn app.main:app --reload --port 3001
```

The API is available at `http://localhost:3001`, with interactive docs at
`http://localhost:3001/docs`. Configure the frontend with:

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:3001
```

Then run `npm run dev` in the frontend repository. Local requests do not use
Fly.io or consume Fly Machine runtime.

## Demo data

Migration `20260810_02` inserts the demo dataset exactly once:

- 2 non-admin users
- 6 pets
- 1 adoption and 1 foster relationship
- 3 saved-pet relationships

Alembic records the migration revision in `alembic_version`, so later app
starts run `alembic upgrade head` without reinserting or overwriting the data.
The demo users share the password `LittleLlamaDemo!`:

- `alex.demo@littlellama.pet`
- `maya.demo@littlellama.pet`

## Checks

```bash
pytest -q
ruff check .
```

## Production

The Docker container applies pending Alembic migrations and starts Uvicorn.
Fly Proxy is configured to stop the Machine when idle and start it on the next
request. This reduces runtime cost but means the first request after an idle
period may have a short cold start.
