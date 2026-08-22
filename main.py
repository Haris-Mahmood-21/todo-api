import os

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

# =============================================================================
# W4 Assignment — Supabase Auth
# =============================================================================

from supabase import create_client, Client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Server running and connected to Supabase", "version": "4.0"}


# =============================================================================
# PREVIOUS ASSIGNMENT (A3) — Postgres / Task CRUD API
# Kept for reference. All code below is commented out.
# =============================================================================

# import psycopg
# from psycopg.rows import dict_row
# from contextlib import contextmanager
# from fastapi import HTTPException
# from pydantic import BaseModel
#
# DATABASE_URL = os.environ["DATABASE_URL"]
#
#
# # ---------------------------------------------------------------------------
# # Connection + Stage 0/1: create the table, seed it (only once)
# #
# # Every database line lives in this module (the "repository"). Routes below
# # never touch SQL directly — they only call these helpers. That's what keeps
# # a storage swap (memory -> SQLite -> Postgres) from ever touching a route.
# # ---------------------------------------------------------------------------
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
#             # Stretch goal: index on a column we'd filter on (done).
#             cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_done ON tasks (done)")
#
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
# # ---------------------------------------------------------------------------
# # Request/response models — unchanged since Assignment 1
# # ---------------------------------------------------------------------------
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
# # ---------------------------------------------------------------------------
# # Routes — same paths, same status codes, same shapes as A1/A2.
# # Only the storage layer underneath changed (now Postgres, in Docker).
# # ---------------------------------------------------------------------------
#
# @app.get("/")
# def read_root_old():
#     return {"name": "Task API", "version": "3.0", "endpoints": ["/tasks"]}
#
#
# @app.get("/health")
# def health_check():
#     """Health check that also pings the database with SELECT 1."""
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
# # Stage 2: read from Postgres -------------------------------------------------
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
# # Stage 3: create, update, delete on Postgres ---------------------------------
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
