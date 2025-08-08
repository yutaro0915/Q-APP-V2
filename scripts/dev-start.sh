#!/bin/bash
set -e

echo "=== Q-APP-V2 Development Startup ==="

# Check PostgreSQL
if ! brew services list | grep -q "postgresql@16.*started"; then
  echo "Starting PostgreSQL..."
  brew services start postgresql@16
fi

# Check if database exists
if ! psql -lqt | cut -d \| -f 1 | grep -qw campus_sns; then
  echo "Creating database..."
  createdb campus_sns
  psql campus_sns -f docs/03a_ddl_postgresql_v1.sql
fi

echo "PostgreSQL ready!"

# Start backend in background
echo "Starting Backend..."
cd backend
echo "Please run the following command in another terminal:"
echo "  cd backend && uv run uvicorn app.main:app --reload --port 8000"
cd ..

# Start frontend
echo "Starting Frontend..."
cd frontend
npm run dev