# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kyudai Campus SNS (九大学内SNS) - A university campus social network system for Kyushu University students. The project follows a microservices architecture with FastAPI backend and planned Next.js frontend.

## Commands

### Backend Development

```bash
# Navigate to backend directory
cd /workspace/backend

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Run specific test
pytest tests/test_health.py -v

# Format code
black app/ tests/

# Lint code
ruff check app/ tests/

# Fix linting issues
ruff check --fix app/ tests/
```

### Docker Development

```bash
# Build and run with Docker
cd /workspace/backend
docker build -t kyudai-sns-backend .
docker run -p 8000:8000 kyudai-sns-backend
```

## Architecture

### Layered Backend Structure

The backend follows a strict layered architecture (routers → services → repos):

1. **Routers** (`app/routers/`): Thin HTTP layer, handles requests/responses
2. **Services** (`app/services/`): Core business logic and domain rules
3. **Repos** (`app/repos/`): Data access layer with SQL queries
4. **Schemas** (`app/schemas/`): Pydantic DTOs for request/response validation
5. **DB** (`app/db/`): Database models and migrations

### Key Architectural Principles

- **Async-First**: All database operations use async/await with AsyncPG
- **SQLAlchemy Core**: Use Core (not ORM) for explicit SQL control
- **Soft Deletes**: Never hard delete - use `deleted_at` timestamps
- **Bearer Auth**: Device-based anonymous authentication system
- **S3 Uploads**: Direct client uploads via presigned URLs

### Database Schema

Primary entities:
- **users**: Device-based anonymous users with optional profiles
- **threads**: Main posts with categories (general/question/info)
- **comments**: Nested comments on threads
- **reactions**: Emoji reactions on threads/comments
- **uploads**: S3 image metadata

## API Endpoints

Core endpoints defined in `/workspace/docs/03_api_contract.md`:

- `POST /api/v1/auth/anonymous` - Anonymous device authentication
- `POST /api/v1/threads` - Create thread
- `GET /api/v1/threads` - List threads with pagination
- `POST /api/v1/threads/{id}/comments` - Add comment
- `POST /api/v1/threads/{id}/reactions` - Add reaction
- `GET /api/v1/search` - Fuzzy text search

## Development Workflow

### Issue Management

Issues are tracked in `/workspace/issues/` as YAML files with structure:
- Specification, constraints, tests, and definition of done
- Progress tracked in `/workspace/issues/progress_index.csv`

### Testing Strategy

- Write tests first following TDD approach
- Use pytest with async support
- Mock external dependencies (S3, database)
- Test files go in `backend/tests/` mirroring source structure

### Code Quality Standards

- Format with Black (100 char line length)
- Lint with Ruff (E, F, W, I, N rules)
- Type hints on all functions
- Docstrings for services and complex logic

## Important Implementation Notes

1. **Authentication**: Start with device-based anonymous auth, email OTP planned for later
2. **Search**: Use PostgreSQL `pg_trgm` extension for fuzzy search, not external service
3. **Images**: Client-side resize to 1024px before upload, store originals in S3
4. **Reactions**: Limited set of emojis, one reaction per user per item
5. **Comments**: Support 2-level nesting (comment on thread, reply to comment)
6. **Categories**: Fixed set (general/question/info), enforce in backend

## Documentation References

Comprehensive documentation in `/workspace/docs/`:
- `00_readme.md` - Complete system specification
- `02_domain_invariants.md` - Business rules to enforce
- `03_api_contract.md` - Full API specification
- `04_backend_design.md` - FastAPI implementation guide
- `06_infra_aws.md` - AWS deployment architecture

Always consult these documents for authoritative specifications before implementing features.