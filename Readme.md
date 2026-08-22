# Auth API — Supabase Authentication with FastAPI

A secure authentication API built with **Python + FastAPI** and **Supabase Auth** for FlyRank Internship — Backend Track, Week 2, Assignment A4.

> **Note:** This repo has grown across four assignments in the same lane:
> A1 → in-memory list · A2 → SQLite · A3 → containerized PostgreSQL · **A4 (this one) → Supabase Auth**.
> The previous assignment's Task CRUD code is preserved (commented out) in `main.py` for reference.

---

## What it does

Implements a complete authentication flow using **Supabase as the Identity Provider** — your server never stores or hashes passwords. Supabase handles all of that and issues signed JWTs; your server only verifies them.

```
Client → POST /auth/signup  → Supabase creates account
Client → POST /auth/login   → Supabase returns JWT
Client → GET  /protected/*  → FastAPI verifies JWT with Supabase → allows/rejects
```

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/Haris-Mahmood-21/todo-api.git
cd todo-api
```

### 2. Create and fill in your `.env`
```bash
cp .env.example .env
```
Then edit `.env` with your real values:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here
```

Get these from your [Supabase Dashboard](https://supabase.com) → **Project Settings → API**.

> **One-time Supabase setting:** Go to **Authentication → Sign In / Providers → Email** and turn **"Confirm email" OFF** so a fresh signup can log in immediately.

### 3. Create a virtual environment and install dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Run the server
```bash
uvicorn main:app --reload
```

Server starts at **http://localhost:8000**
Interactive docs at **http://localhost:8000/docs**

---

## Environment Variables

| Variable       | Description                                        |
|----------------|----------------------------------------------------|
| `SUPABASE_URL` | Your Supabase project URL                          |
| `SUPABASE_KEY` | Your Supabase anon (public) key — safe in your app |

> The `DATABASE_URL` variable in `.env.example` is kept for the previous assignment (A3 Postgres setup) and is not used by the A4 auth server.

---

## API Endpoints

| Method | Path                    | Auth Required       | Status | Description                              |
|--------|-------------------------|---------------------|--------|------------------------------------------|
| GET    | `/`                     | No                  | 200    | Server status                            |
| POST   | `/auth/signup`          | No                  | 201    | Create a new user account                |
| POST   | `/auth/login`           | No                  | 200    | Log in — returns `access_token` + `refresh_token` |
| POST   | `/auth/logout`          | Bearer token        | 204    | End the session                          |
| GET    | `/public/info`          | No                  | 200    | Public info, open to everyone            |
| GET    | `/protected/profile`    | Bearer token        | 200    | Returns verified user's id, email, created_at |
| GET    | `/protected/dashboard`  | Bearer token        | 200    | Returns a welcome message for the user   |

### Error codes

| Code | Meaning                                              |
|------|------------------------------------------------------|
| 400  | Missing `email` or `password` in request body        |
| 401  | Missing, malformed, or invalid/expired Bearer token  |

---

## How to authenticate

**Sign up:**
```bash
curl -i -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpassword"}'
```

**Log in (get your token):**
```bash
curl -i -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpassword"}'
```

**Call a protected route:**
```bash
curl -i http://localhost:8000/protected/profile \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

**Tamper the token (see the guard reject it):**
```bash
curl -i http://localhost:8000/protected/profile \
  -H "Authorization: Bearer TAMPERED_TOKEN"
# → 401 Invalid or expired token
```

---

## Swagger UI

FastAPI serves interactive docs automatically at **http://localhost:8000/docs**.

Because the protected routes use FastAPI's `HTTPBearer` security scheme, Swagger shows a **🔒 lock icon** on every protected endpoint. Click **Authorize**, paste your `access_token` from `/auth/login`, and use **Try it out** to call any route directly from the browser — no curl needed.

![Swagger UI with bearer auth](swagger_screenshot.png)

---

## How the auth guard works

The reusable `get_current_user` dependency is the single guard applied to every protected route:

```python
bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(credentials = Depends(bearer_scheme)):
    if credentials is None:
        raise HTTPException(401, {"error": "Access token required"})
    try:
        user = supabase.auth.get_user(credentials.credentials)
        return user.user
    except Exception:
        raise HTTPException(401, {"error": "Invalid or expired token"})
```

Any route protected with `Depends(get_current_user)` gets the full verification with zero repeated code — one guard, standing at every locked door.


---

## Previous assignment (A3)

The Task CRUD API (Postgres + Docker) from A3 is preserved inside `main.py` in commented-out blocks, and `compose.yaml` / `dockerfile` are kept in the repo so the previous assignment history is intact.
