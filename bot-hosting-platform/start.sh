#!/bin/bash
set -e

# Run migrations (create tables)
python -c "from backend.database import Base, engine; Base.metadata.create_all(bind=engine)"

# Start the API server
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
