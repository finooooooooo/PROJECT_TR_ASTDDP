# AGENTS.md

## Project Constraints
- **Backend**: Flask
- **Database**: PostgreSQL (`psycopg2` + `RealDictCursor`). NO SQLite.
- **Frontend**: Jinja2 + Tailwind CSS (CDN) + Vanilla JS.
- **Desktop Wrapper**: `pywebview`.
- **Currency**: Indonesian Rupiah (Rp). No decimals.
- **Tax**: 10% on top of subtotal.
- **Transactions**: `TRX-YYYYMMDD-XXXX`. Atomic.

## Environment
- **DB Host**: localhost
- **DB Name**: kasir_db
- **DB User**: postgres
- **DB Pass**: 5432
- **Port**: 5432

## File Structure
- `static/uploads`: Stores product images.
- `app.py`: Main Flask entry.
- `services.py`: Business logic.
- `db.py`: Database connection context.
