# ShipForge — Ship Design & Sea Trial Simulator

Full-stack version of the ShipForge demo: a FastAPI + MySQL backend behind
the original single-page frontend, following the same pattern as the
ครัวชัวร์ Nutrition REST API project (FastAPI/Python, MySQL 8.4, JWT + Argon2,
Docker Compose, Swagger docs).

## Tech stack

- **Frontend:** static HTML/CSS/JS (`frontend/index.html`), served by nginx
- **Backend:** FastAPI / Python
- **Database:** MySQL 8.4
- **Authentication:** JWT + Argon2 password hashing
- **Container:** Docker + Docker Compose
- **API docs:** Swagger UI

## Run

```
docker compose up --build
```

Then open:

- Frontend (the game): http://localhost:8080
- Swagger: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

The frontend talks to the backend at `http://localhost:8000/api` by
default. To point it at a different backend URL, set
`window.SHIPFORGE_API_BASE` before `index.html`'s script runs, or edit the
`API_BASE` constant near the top of the `<script>` block.

## API overview

### Authentication

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `POST /api/auth/change-password`

### User management

- `GET /api/me`
- `GET /api/users/{id}`
- `GET /api/users?page=1&limit=10`
- `PUT /api/users/{id}`
- `DELETE /api/users/{id}`
- `GET /api/check-username/{name}`

### ShipForge project API

- `GET /api/parts?search=engine` — browse the part catalog
- `GET /api/materials` — browse the material catalog
- `POST /api/ships` — save a ship (blueprint + material + ship type)
- `GET /api/ships` — list your saved ships
- `GET /api/ships/{id}` — load one ship
- `DELETE /api/ships/{id}`
- `POST /api/ships/{id}/inspect` — run the safety inspection server-side
  (same formulas as the frontend's live readout, recomputed from the DB)
- `POST /api/ships/{id}/sea-trial` — store a completed sea trial result
- `GET /api/ships/{id}/trials` — sea trial history for a ship

## Example register

```json
{
  "username": "testuser",
  "email": "test@example.com",
  "full_name": "Test User",
  "password": "12345678"
}
```

## Example login

```json
{
  "username": "testuser",
  "password": "12345678"
}
```

Paste the returned `access_token` into Swagger's **Authorize** button as:

```
Bearer <access_token>
```

## Example create ship

```json
{
  "name": "Northern Star",
  "ship_type": "fishing",
  "material_key": "steel",
  "parts": [
    {"part_key": "hull", "x": 2, "y": 2},
    {"part_key": "engine", "x": 4, "y": 2},
    {"part_key": "fuelTank", "x": 5, "y": 2}
  ]
}
```

The API computes `safety_score`, `stability`, `buoyancy`, `range` and the
rest from the parts + material, the same way the frontend's live blueprint
readout does — the calculation lives in `backend/app/calc.py`, ported from
the frontend's JS so both sides agree.

## Relationship to the single-file demo

The original `shipforge.html` demo kept a hardcoded catalog of parts and
materials, and computed everything in the browser. This backend moves that
catalog into MySQL (`parts`, `materials` tables) and the calculation into a
REST API, the same move the nutrition project made from
`nutrition-appnew.html` to its FastAPI backend. The frontend here still
works fully offline (local JS calculation) — login lets you additionally
save/load ships to your account and verify a ship's safety score against
the server.
