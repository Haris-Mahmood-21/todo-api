import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.requests import Request
from pydantic import BaseModel

load_dotenv()

# =============================================================================
# W4 Assignment — Supabase Auth
# =============================================================================

from supabase import create_client, Client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Convert FastAPI 422 validation errors to 400 Bad Request per assignment spec."""
    return JSONResponse(
        status_code=400,
        content={"error": "Email and password are required"},
    )


@app.get("/")
def read_root():
    return {"message": "Server running and connected to Supabase", "version": "4.0"}


# =============================================================================
# Stage 1 — Auth: Sign Up & Log In
# =============================================================================

class AuthBody(BaseModel):
    email: str
    password: str


@app.post("/auth/signup", status_code=201)
def signup(body: AuthBody):
    """Register a new user via Supabase Auth. Returns 201 with user object."""
    if not body.email or not body.password:
        raise HTTPException(status_code=400, detail="Email and password are required")
    try:
        response = supabase.auth.sign_up({"email": body.email, "password": body.password})
        return {
            "user": {
                "id": response.user.id,
                "email": response.user.email,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/login")
def login(body: AuthBody):
    """Authenticate a user. Returns 200 with access_token and refresh_token."""
    if not body.email or not body.password:
        raise HTTPException(status_code=400, detail="Email and password are required")
    try:
        response = supabase.auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "token_type": "bearer",
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid login credentials")


# =============================================================================
# Stage 2 — Public & Protected Gates (token presence check only, not verified)
# =============================================================================

@app.get("/public/info")
def public_info():
    """Open to everyone — no auth required."""
    return {"message": "Welcome stranger! This info is public."}


@app.get("/protected/profile")
def profile(request: Request):
    """
    Protected route — requires Authorization: Bearer <token> header.
    Stage 2: only checks the token is PRESENT, not yet verified.
    Stage 3 will add actual Supabase verification.
    """
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Access token required")
    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Access token required")
    # Token is present but NOT verified yet — that is Stage 3
    return {"message": "Token present (not yet verified — Stage 2)"}


# =============================================================================
# PREVIOUS ASSIGNMENT (A3) — Postgres / Task CRUD API
# Kept for reference. All code below is commented out.
# =============================================================================

# import psycopg
# from psycopg.rows import dict_row
# from contextlib import contextmanager
#
# DATABASE_URL = os.environ["DATABASE_URL"]
#
#
# @contextmanager
# def get_connection():
#     """Open a connection to Postgres using the DATABASE_URL from .env."""
#     conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
#     try:
#         yield conn
#     finally:
#         conn.close()
#
#
# def init_db():
#     """Create the tasks table if missing, and seed 3 example tasks only if empty."""
#     with get_connection() as conn:
#         with conn.cursor() as cur:
#             cur.execute(
#                 """
#                 CREATE TABLE IF NOT EXISTS tasks (
#                     id SERIAL PRIMARY KEY,
#                     title TEXT NOT NULL,
#                     done BOOLEAN NOT NULL DEFAULT FALSE
#                 )
#                 """
#             )
#             cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_done ON tasks (done)")
#             cur.execute("SELECT COUNT(*) AS count FROM tasks")
#             count = cur.fetchone()["count"]
#             if count == 0:
#                 cur.executemany(
#                     "INSERT INTO tasks (title, done) VALUES (%s, %s)",
#                     [
#                         ("Buy milk", False),
#                         ("Walk the dog", False),
#                         ("Read a book", True),
#                     ],
#                 )
#         conn.commit()
#
#
# init_db()
#
#
# class TaskCreate(BaseModel):
#     title: str = ""
#
#
# class TaskUpdate(BaseModel):
#     title: str = ""
#     done: bool = False
#
#
# def row_to_task(row: dict) -> dict:
#     return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}
#
#
# @app.get("/")
# def read_root_old():
#     return {"name": "Task API", "version": "3.0", "endpoints": ["/tasks"]}
#
#
# @app.get("/health")
# def health_check():
#     try:
#         with get_connection() as conn:
#             with conn.cursor() as cur:
#                 cur.execute("SELECT 1")
#                 cur.fetchone()
#         return {"status": "ok", "db": "ok"}
#     except Exception:
#         raise HTTPException(status_code=503, detail={"status": "error", "db": "unreachable"})
#
#
# @app.get("/tasks")
# def get_tasks():
#     with get_connection() as conn:
#         with conn.cursor() as cur:
#             cur.execute("SELECT * FROM tasks")
#             rows = cur.fetchall()
#     return [row_to_task(r) for r in rows]
#
#
# @app.get("/tasks/{task_id}")
# def get_task(task_id: int):
#     with get_connection() as conn:
#         with conn.cursor() as cur:
#             cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
#             row = cur.fetchone()
#     if row is None:
#         raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
#     return row_to_task(row)
#
#
# @app.post("/tasks", status_code=201)
# def create_task(task: TaskCreate):
#     if not task.title or not task.title.strip():
#         raise HTTPException(status_code=400, detail="Title is required and cannot be empty")
#     with get_connection() as conn:
#         with conn.cursor() as cur:
#             cur.execute(
#                 "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *",
#                 (task.title, False),
#             )
#             row = cur.fetchone()
#         conn.commit()
#     return row_to_task(row)
#
#
# @app.put("/tasks/{task_id}")
# def update_task(task_id: int, task: TaskUpdate):
#     if not task.title or not task.title.strip():
#         raise HTTPException(status_code=400, detail="Title is required and cannot be empty")
#     with get_connection() as conn:
#         with conn.cursor() as cur:
#             cur.execute(
#                 "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING *",
#                 (task.title, task.done, task_id),
#             )
#             row = cur.fetchone()
#             if row is None:
#                 raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
#         conn.commit()
#     return row_to_task(row)
#
#
# @app.delete("/tasks/{task_id}", status_code=204)
# def delete_task(task_id: int):
#     with get_connection() as conn:
#         with conn.cursor() as cur:
#             cur.execute("DELETE FROM tasks WHERE id = %s RETURNING id", (task_id,))
#             row = cur.fetchone()
#             if row is None:
#                 raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
#         conn.commit()
#     return
