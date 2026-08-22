import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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

app = FastAPI(
    title="Auth API — Supabase & FastAPI",
    description="Secure authentication API with Supabase Auth. Sign up, log in, log out, and access protected routes using Bearer tokens.",
    version="4.0",
)


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
# Stage 2 — Public route (no auth)
# =============================================================================

@app.get("/public/info")
def public_info():
    """Open to everyone — no auth required."""
    return {"message": "Welcome stranger! This info is public."}


# =============================================================================
# Stage 4 — Reusable auth dependency (replaces manual header check from Stage 3)
#
# HTTPBearer(auto_error=False) lets us return 401 ourselves instead of the
# default 403 FastAPI would send when the Authorization header is missing.
# This dependency is the single "guard" — add Depends(get_current_user) to
# any route and it is instantly protected with no repeated auth code.
# =============================================================================

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    """
    FastAPI dependency: extracts the Bearer token, verifies it with Supabase,
    and returns the verified user object. Raises 401 on any failure.
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail={"error": "Access token required"})
    token = credentials.credentials
    try:
        user_response = supabase.auth.get_user(token)
        return user_response.user
    except Exception:
        raise HTTPException(status_code=401, detail={"error": "Invalid or expired token"})


# =============================================================================
# Stage 3 / 4 — Protected routes using the reusable dependency
# =============================================================================

@app.get("/protected/profile")
def profile(user=Depends(get_current_user)):
    """Returns the verified user's profile data. Requires Bearer token."""
    return {
        "id": user.id,
        "email": user.email,
        "created_at": str(user.created_at),
    }


@app.get("/protected/dashboard")
def dashboard(user=Depends(get_current_user)):
    """
    Second protected route — uses the exact same dependency, zero new auth code.
    Proves the guard is reusable (Stage 4 checkpoint requirement).
    """
    return {
        "message": f"Welcome to your dashboard, {user.email}",
        "user_id": user.id,
    }


@app.post("/auth/logout", status_code=204)
def logout(user=Depends(get_current_user)):
    """
    Protected logout route — guard runs first, then Supabase session is ended.
    Returns 204 No Content on success.
    """
    try:
        supabase.auth.sign_out()
    except Exception:
        pass  # Best-effort; token is already verified so we still return 204
    return


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
