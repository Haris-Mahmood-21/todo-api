# Task API — CRUD To-Do List

A small in-memory CRUD API built with **Python + FastAPI** for FlyRank Internship — Backend Track, Week 2, Assignment A1.

Supports creating, reading, updating, and deleting tasks. Tasks are stored in memory only (no database) — data resets when the server restarts.

## How to run it

1. Clone the repo:
   ```bash
   git clone https://github.com/Haris-Mahmood-21/todo-api.git
   cd todo-api
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # Mac/Linux
   venv\Scripts\activate      # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

5. Visit:
   - API root: http://localhost:8000/
   - Swagger UI (interactive docs): http://localhost:8000/docs

## Endpoints

| Method | Path              | Description                          | Success | Errors             |
|--------|-------------------|---------------------------------------|---------|---------------------|
| GET    | `/`               | API info                              | 200     | —                   |
| GET    | `/health`         | Health check                          | 200     | —                   |
| GET    | `/tasks`          | List all tasks                        | 200     | —                   |
| GET    | `/tasks/{id}`     | Get a single task                     | 200     | 404 if not found    |
| POST   | `/tasks`          | Create a new task                     | 201     | 400 if title missing/empty |
| PUT    | `/tasks/{id}`     | Update a task's title and done status | 200     | 400 invalid body, 404 not found |
| DELETE | `/tasks/{id}`     | Delete a task                         | 204     | 404 if not found    |

## Example request

```bash
curl -i -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy milk"}'
```

```
HTTP/1.1 201 Created
content-type: application/json

{"id":4,"title":"Buy milk","done":false}
```

## Swagger UI

Screenshot of the interactive docs at `/docs`, showing all endpoints and a working "Try it out" cycle:

![Swagger UI](screenshot.png)

## Data storage note

Tasks are stored in a plain Python list in memory. Restarting the server resets the data back to the 3 seed tasks — there is no database yet (that's next week's topic).