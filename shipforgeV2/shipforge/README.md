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

### Projects (Ship Design & Construction Planning platform)

- `POST /api/projects` — create a project. `ship_id` is **optional** — a
  project can now be created purely from the Requirements Form, before any
  2D ship design exists, and a ship can be attached to it later.
- `GET /api/projects` — list your projects
- `GET /api/projects/{id}`
- `PUT /api/projects/{id}` — update name/client/status/progress/dates, the
  planning fields below, or attach/replace `ship_id`
- `DELETE /api/projects/{id}`

Status values: `PLANNING`, `DESIGN`, `CONSTRUCTION`, `INSPECTION`, `SEA_TRIAL`, `COMPLETED`, `ON_HOLD`.

Planning / requirements fields on a project: `vessel_type`, `intended_use`,
`operating_area`, `budget_min`, `budget_max`, `estimated_duration` (months),
and a structured `requirements` object (passenger capacity, cargo tons,
desired speed, crew size, free-text notes — stored as JSON).

### Design recommendations (rule-based, not ML)

- `POST /api/projects/{id}/recommendations` — generate 3 preliminary design
  options (Economy / Balanced / Premium) from the project's requirements,
  replacing any previous set. Every number is produced by simple,
  explainable formulas (see `backend/app/recommend.py`) — this is **not**
  machine learning and **not** a certified naval-architecture calculation,
  it's a planning aid.
- `GET /api/projects/{id}/recommendations` — list the last generated set.

Each design option also includes a **cost breakdown by category** (hull/structure,
materials & fabrication, propulsion, electrical/mechanical, nav & safety
equipment, labor, finishing, inspection & commissioning, contingency — fixed
proportions of the total, always reconciling exactly) and an **8-phase
construction timeline** (requirements/concept → testing/commissioning) with
duration ranges, not fixed dates.

### Materials reference (§12)

- `GET /api/materials/info` — transparent trade-off notes per material
  (cost, weight, corrosion, maintenance, durability, fabrication). General
  engineering guidance, not sourced/dated market pricing.

### Shipyard discovery (§15 — SAMPLE DATA ONLY)

- `GET /api/shipyards?vessel_type=&budget_max=&length_m=` — browse/match
  shipyards, ranked by how many criteria matched (never excludes near-misses).
- `GET /api/projects/{id}/shipyards` — a project's shortlisted shipyards.
- `POST /api/projects/{id}/shipyards` — add a shipyard to a project's shortlist.
- `DELETE /api/projects/{id}/shipyards/{shortlist_id}` — remove from shortlist.

All seeded shipyard rows are fictional placeholders with `source="sample"`
and `verified=false` — the UI labels them as sample data throughout, per the
spec's explicit instruction never to fabricate real businesses/contacts.

### ShipForge project API

- `GET /api/parts?search=engine` — browse the part catalog
- `GET /api/materials` — browse the material catalog
- `POST /api/ships` — save a ship (blueprint + material + ship type)
- `GET /api/ships` — list your saved ships
- `GET /api/ships/{id}` — load one ship
- `PUT /api/ships/{id}` — update an existing ship's blueprint in place (used when editing an already-saved ship, so it doesn't duplicate)
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
