# REST API standards

Technical reference for the Couple Life Simulator HTTP API. All backend endpoints and frontend API clients must follow these conventions.

**Base path:** `/api`  
**Content type:** `application/json` for all request and response bodies.

---

## Response envelopes

Every JSON response uses a consistent top-level shape. Do not return raw resource objects or bare error strings at the root level.

### Success (2xx)

The response payload lives under `data`.

```json
{
  "data": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "status": "created"
  }
}
```

Rules:

- Use `ok(data)` from `app.schemas.responses` in routers, or return `{"data": ...}` directly.
- When there is no meaningful payload (e.g. after a delete), return `"data": null`.
- Do **not** place resource fields at the top level alongside `data`.

### Error (4xx / 5xx)

Errors are returned as a list under `errors`. Each item is an object with at least `code` and `message`.

```json
{
  "errors": [
    {
      "code": "GAME_NOT_FOUND",
      "message": "Game not found"
    }
  ]
}
```

Optional fields:

| Field | Type | When to use |
|-------|------|-------------|
| `field` | string | Validation errors — location of the invalid input (e.g. `body.partner_a_name`) |

Multiple errors may be returned in a single response (e.g. several validation failures).

---

## Error codes

| Rule | Detail |
|------|--------|
| Format | Stable, machine-readable identifiers in `SCREAMING_SNAKE_CASE` |
| Examples | `GAME_NOT_FOUND`, `VALIDATION_ERROR`, `CONFLICT` |
| `message` | Human-readable, translatable string — use `gettext` / `_()` |
| Raising errors | Services raise `AppError`; routers do not format error JSON manually |
| Avoid | Raw `HTTPException` for domain errors — use `AppError` so codes stay consistent |

### Implementation

| Module | Role |
|--------|------|
| `app.shared.exceptions.AppError` | Domain/application exception with `code`, `message`, `status_code`, optional `field` |
| `app.shared.exception_handlers` | Global handlers that format `AppError`, `HTTPException`, validation errors, and unhandled exceptions |
| `app.schemas.responses.ok` | Helper to wrap successful payloads |

Example:

```python
from gettext import gettext as _

from app.shared.exceptions import AppError

raise AppError("GAME_NOT_FOUND", _("Game not found"), status_code=404)
```

---

## HTTP methods and status codes

| Action | Method | Success status | `data` shape |
|--------|--------|----------------|--------------|
| Create resource | `POST` | `201 Created` | Created resource (or identifier) |
| Read one | `GET` | `200 OK` | Resource object |
| Read collection | `GET` | `200 OK` | Object with `items` + `pagination` |
| Partial update | `PATCH` | `200 OK` | Updated resource |
| Full replace | `PUT` | `200 OK` | Updated resource |
| Delete | `DELETE` | `200 OK` | `null` unless a summary is useful |

Use the most specific 4xx/5xx status that applies (`400`, `404`, `409`, `422`, `500`, etc.). The response body always uses the `errors` envelope — never a bare string `detail`.

Common error status codes:

| Status | Typical `code` | When |
|--------|----------------|------|
| `400` | `BAD_REQUEST` | Malformed or semantically invalid request |
| `404` | `*_NOT_FOUND` | Resource does not exist |
| `409` | `CONFLICT` | State conflict (e.g. duplicate, wrong game status) |
| `422` | `VALIDATION_ERROR` | Request body or query param failed Pydantic validation |
| `500` | `INTERNAL_ERROR` | Unexpected server failure |

---

## URLs and naming

| Rule | Good | Bad |
|------|------|-----|
| Plural, lowercase nouns for collections | `/api/games` | `/api/game` |
| UUID path parameters | `/api/games/{game_id}` | `/api/games/{id}` with integer IDs |
| snake_case JSON fields | `partner_a_name` | `partnerAName` |
| HTTP methods express actions | `POST /api/games` | `/api/create-game` |
| Nest related resources when clear | `/api/games/{game_id}/players` | Flat unrelated paths |

Keep routers thin; business logic belongs in services.

---

## Pagination

List endpoints return paginated results inside `data`:

```json
{
  "data": {
    "items": [
      {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "status": "created"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 1
    }
  }
}
```

Query parameters:

| Parameter | Default | Notes |
|-----------|---------|-------|
| `page` | `1` | 1-based page index |
| `per_page` | `20` | Page size; cap at `100` |

---

## Request validation

- Request bodies and query parameters are validated with **Pydantic v2** schemas in `backend/app/schemas/`.
- Validation failures return **422** with one `errors` entry per failure:

```json
{
  "errors": [
    {
      "code": "VALIDATION_ERROR",
      "message": "Field required",
      "field": "body.partner_a_name"
    }
  ]
}
```

---

## Current endpoints (MVP 0)

```
POST   /api/games
GET    /api/games/{game_id}
PATCH  /api/games/{game_id}
```

Extend with resource-oriented endpoints as features are added.

---

## Frontend consumption

API client code in `frontend/src/services/` should:

1. On success — read the payload from `response.data`.
2. On failure — read `response.errors` and handle by `code`.
3. Map `code` to i18n translation keys when the UI needs localized copy beyond the server `message`.

Example TypeScript shapes:

```typescript
type ApiSuccess<T> = { data: T };
type ApiErrorDetail = { code: string; message: string; field?: string };
type ApiError = { errors: ApiErrorDetail[] };
```

---

## Checklist for new endpoints

- [ ] Success response wrapped in `{ "data": ... }`
- [ ] Domain errors raised as `AppError` with a stable `code`
- [ ] Correct HTTP status code for the operation
- [ ] Pydantic schema for request validation
- [ ] User-facing `message` strings wrapped in `_()` for i18n
- [ ] List endpoints use `items` + `pagination` inside `data`
