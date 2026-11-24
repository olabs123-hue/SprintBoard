# SprintBoard — Full-stack task dashboard

A **new, independent 2026 rebuild** of a task-management MVP. This repository does **not** establish the scope, headcount, time-to-delivery, or usage of earlier Chrisdeb work.

**Stack:** React 19, TypeScript (strict), Vite, FastAPI, SQLAlchemy, PyJWT, SQLite for local development and tests.

## Features
- Registration, login, short-lived signed JWTs and private user workspaces.
- Kanban board: **To do / In progress / Done**, with three task priority levels.
- Create, view, update status, delete, search and filter tasks.
- Four KPIs from real task state: total, in progress, completed, completion percentage.
- Loading, empty and error states; responsive desktop/mobile presentation.
- Account ownership is checked on every task read/write.

## Start backend
```bash
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
API docs: http://localhost:8000/docs

## Start frontend
```bash
cd frontend
npm install
npm run dev
```
Browse http://localhost:5173. Development proxy forwards `/api` to the backend.

## Tests and build
```bash
PYTHONPATH=backend python -m pytest -q backend/tests
cd frontend && npm install && npm run build && npm run lint
```
GitHub Actions runs the checks after each commit. Do not interpret source-file counts as historical Chrisdeb delivery metrics.

## Deployment security
Development mode uses a local SQLite database and placeholder JWT secret. **Never publicly deploy it that way.** Production requires a strong `JWT_SECRET`, managed database, TLS, reverse-proxy rate limiting, migrations, observability, security review, and persistent storage.

## Project boundaries
This is an independently rebuilt demo; user counts, team size and development timeline are not claimed. Do not attribute newly implemented endpoints, screens or tests to earlier employment without independent evidence.
