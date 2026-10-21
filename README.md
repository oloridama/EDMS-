# EDMS — Enterprise Distribution Management System

A Python domain-driven implementation of an automotive-parts distribution business: procurement, catalog, inventory, sales, logistics, and operational reporting.

The project uses SQLAlchemy for persistence and keeps business rules in plain dataclasses, with repositories translating between domain objects and database records.

## Architecture

```
administration/   (roadmap — users, roles, branches, warehouses)
API/              FastAPI app, dependencies, schemas, and routers
authentication/   Users, roles/permissions, password hashing, bearer tokens
catalog/          Categories, specification types, products, configurations, pricing
inventory/        Stock lots, balances, movements, reservations
logistics/        Transporters, shipments, dispatch tracking
procurement/      Suppliers, manufacturers, purchase orders and lines
reporting/        Read-only operational and management reports
sales/            Customers, sales orders, order lines, fulfillment
shared/           Database, pricing value objects, logging, errors
tests/            unittest suites for every implemented module
```

**Layering:** `models` (business rules) → `repositories` (persistence and mapping) → `services` (use cases and orchestration).

## Requirements

- Python 3.12+
- SQLAlchemy 2.x, FastAPI, Uvicorn (`requirements.txt`)

## Setup

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

## Running the API

```bash
. .venv/bin/activate
uvicorn API.main:app --reload
```

Interactive docs are available at `http://127.0.0.1:8000/docs`; the health check is `GET /health`.

All business endpoints live under `/api`. The schema is created automatically when the app starts.

### First user

Registration requires the `auth:manage` permission, which no user has until an administrator exists. Bootstrap the first administrator once:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/bootstrap \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","email":"admin@example.com","password":"secret123"}'
```

Then obtain a bearer token and use it for subsequent calls:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"secret123"}'

curl http://127.0.0.1:8000/api/auth/me -H 'Authorization: Bearer <token>'
```

### Endpoints

| Area | Endpoints |
| --- | --- |
| Auth | `POST /api/auth/bootstrap`, `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me` |
| Catalog | `POST /api/catalog/categories`, `POST /api/catalog/products`, `POST /api/catalog/configurations`, `GET /api/catalog/products/{product_id}`, `PUT /api/catalog/prices/{product_name}` |
| Inventory | `POST /api/inventory/lots`, `GET /api/inventory/lots/{lot_id}`, `GET /api/inventory/stock/{configuration_id}` |
| Sales | `POST /api/sales/orders`, `GET /api/sales/orders/{order_id}`, and lifecycle actions `pay`, `pick`, `fulfill`, `pack`, `dispatch`, `deliver`, `complete`, `cancel` |
| Procurement | `POST /api/procurement/orders`, `GET /api/procurement/orders/{order_id}`, `PATCH /api/procurement/orders/{order_id}/status` |
| Logistics | `POST /api/logistics/transporters`, `POST /api/logistics/shipments`, `GET /api/logistics/shipments/{tracking_id}`, `PATCH /api/logistics/shipments/{tracking_id}/status` |
| Reporting | `GET /api/reports/inventory`, `GET /api/reports/sales`, `GET /api/reports/procurement`, `GET /api/reports/stock-movements` |

## Running tests

```bash
. .venv/bin/activate
python -m unittest discover -s tests -p '*_tests.py' -v
```

The function-style specification tests run directly:

```bash
PYTHONPATH=. python tests/specification_tests.py
```

## Implemented capabilities

### Authentication and authorization
- PBKDF2-HMAC-SHA256 password hashing with per-user salts
- Opaque bearer tokens stored only as SHA-256 digests, with expiry and revocation
- Role-based permissions for eight roles (CEO, Administrator, Branch Manager, Warehouse Manager, Sales Officer, Procurement Officer, Logistics Officer, Dispatch Rider)
- First-administrator bootstrap and deactivation support
- Domain errors mapped to HTTP 400/401/403/409 responses

### Catalog
- Categories with required specification types and allowed values
- Products linked to brands and categories
- Product configurations with specification values and quantity-based pricing tiers
- Product-level fallback prices

### Inventory
- Lot-based stock per product configuration and warehouse
- Available, reserved, damaged, and expired balances
- Audited stock movements (receipt, reservation, release, dispatch, damage, expiry)
- Transactional reserve / release / dispatch operations used by sales

### Procurement
- Purchase orders with lifecycle: draft → approved → sent → partially received → completed
- Snapshot supplier/product/manufacturer/unit-price data at order time
- Database uniqueness and quantity/price constraints
- Validated status transitions, including received-quantity consistency

### Sales
- Customers, sales orders, and order lines
- Lifecycle: created → paid → picking → packed → dispatched → delivered → completed (cancel supported before picking)
- Partial fulfillment and partial dispatch
- Price snapshots per line, resolved from configuration tiers with fallback prices
- Stock reservation on payment, release on cancellation, and inventory deduction on dispatch

### Logistics
- Transporter records with generated identifiers
- Shipments with immutable dispatch-time transporter and transport-mode snapshots
- Status transitions and package references to persisted product configurations

### Reporting
Read-only aggregate queries over the operational tables:
- `inventory_levels()` — available/reserved/damaged/expired by configuration and warehouse
- `sales_summary()` — order counts and value by status
- `procurement_summary()` — order counts, value, ordered and received quantities by status
- `stock_movement_summary()` — movement counts and quantities by movement type

## Design notes

- **Domain models stay ORM-free.** SQLAlchemy records live in repository modules (`*_records`/`records.py`) and are mapped to dataclasses by mappers.
- **Database constraints back up business rules.** Uniqueness, non-negative prices, and quantity ranges are enforced in both Python and SQL.
- **Single owner per concept.** Customer sales orders belong to `sales`; the earlier catalog-level order/order-line implementation was removed to prevent duplicated order semantics. Its quantity-tier pricing behavior was carried over into `SalesOrderService`.
- **Snapshots preserve history.** Order lines keep the price agreed at order time, and shipments keep transporter/transport details as of dispatch.
