import sqlite3
from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

DB_PATH = Path(__file__).parent / "tasks.db"

@contextmanager
def get_connection():
    """Open a connection to tasks.db, row_factory set so rows behave like dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Create the tasks table if missing, and seed 3 example tasks only if empty.

    The seed is wrapped in a transaction (executescript / explicit commit) so
    it's all-or-nothing: if inserting the third seed task failed halfway
    through, we would not want two orphan rows left behind on next startup.
    """
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_title ON tasks (title)")

        count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        if count == 0:
            with conn: 
                conn.executemany(
                    "INSERT INTO tasks (title, done) VALUES (?, ?)",
                    [
                        ("Buy milk", 0),
                        ("Walk the dog", 0),
                        ("Read a book", 1),
                    ],
                )


init_db()

class TaskCreate(BaseModel):
    title: str = ""


class TaskUpdate(BaseModel):
    title: str = ""
    done: bool = False


def row_to_task(row: sqlite3.Row) -> dict:
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}

@app.get("/")
def read_root():
    """Describe this API and its main endpoint."""
    return {
        "name": "Task API",
        "version": "2.0",
        "endpoints": ["/tasks"]
    }


@app.get("/health")
def health_check():
    """Simple health check to confirm the server is alive."""
    return {"status": "ok"}


@app.get("/tasks")
def get_tasks():
    """Return the full list of tasks, read live from tasks.db."""
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM tasks").fetchall()
        return [row_to_task(r) for r in rows]


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    """Return a single task by its id, or 404 if not found."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return row_to_task(row)


@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):
    """Create a new task. Requires a non-empty title. The database assigns the id."""
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail="Title is required and cannot be empty")
    with get_connection() as conn:
        with conn:
            cursor = conn.execute(
                "INSERT INTO tasks (title, done) VALUES (?, ?)",
                (task.title, 0),
            )
            new_id = cursor.lastrowid
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (new_id,)).fetchone()
    return row_to_task(row)


@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate):
    """Update an existing task's title and done status."""
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail="Title is required and cannot be empty")
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        with conn:
            conn.execute(
                "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
                (task.title, int(task.done), task_id),
            )
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return row_to_task(row)


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    """Delete a task by its id."""
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        with conn:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return
