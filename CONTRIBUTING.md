# Contributing to AgentOS Bench

Thank you for your interest in contributing to AgentOS Bench!

## Getting Started

1. Fork the repository and clone it locally.
2. Copy `backend/.env.example` to `backend/.env` and configure optional API keys.
3. Start the stack with `docker-compose up --build` or run backend/frontend separately.

## Development Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Code Standards

- **Python**: Format with Black, lint with Ruff, type hints encouraged.
- **TypeScript**: No `any` types. Use shared types from `frontend/src/lib/types.ts`.
- **Commits**: Use clear, descriptive commit messages focused on the why.
- **Tests**: Add pytest tests for backend logic and ensure `npm run build` passes for frontend changes.

## Adding an Agent Plugin

1. Create a new class inheriting from `BaseAgent` in `backend/app/agents/`.
2. Register it in `backend/app/agents/__init__.py`.
3. Add metadata to `AGENT_METADATA`.
4. Write tests for the agent and eval runner integration.

## Pull Request Process

1. Create a feature branch from `main`.
2. Ensure CI passes locally (ruff, black, pytest, eslint, tsc, vite build).
3. Open a PR with a clear description and test plan.
4. Wait for review and address feedback.

## Reporting Issues

Include steps to reproduce, expected vs actual behavior, and environment details (OS, Python/Node versions).
