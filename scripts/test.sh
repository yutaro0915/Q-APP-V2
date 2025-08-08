#!/bin/bash
set -e

echo "=== Q-APP-V2 Test Suite ==="

# Backend tests
echo "Running Backend tests..."
cd backend
uv run pytest -v
cd ..

# Frontend tests  
echo "Running Frontend tests..."
cd frontend
npm test
cd ..

echo "All tests completed!"